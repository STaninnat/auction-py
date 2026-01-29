import django_filters
from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from payments.models import Wallet, WalletTransaction
from rest_framework import filters, generics, permissions, status, views
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import AuctionListing, BidTransaction
from .serializers import (
    AuctionCreateSerializer,
    AuctionDetailSerializer,
    AuctionListingSerializer,
    BidCreateSerializer,
    UserAuctionSerializer,
)


class AuctionFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="current_price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="current_price", lookup_expr="lte")
    category = django_filters.CharFilter(field_name="product__category")
    condition = django_filters.CharFilter(field_name="product__condition")

    class Meta:
        model = AuctionListing
        fields = ["status", "category", "condition", "min_price", "max_price"]


class AuctionListAPIView(generics.ListAPIView):
    serializer_class = AuctionListingSerializer
    permission_classes = [permissions.AllowAny]
    queryset = AuctionListing.objects.exclude(status="DRAFT").order_by("-created_at")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AuctionFilter
    search_fields = ["product__title", "product__description"]
    ordering_fields = ["current_price", "end_time", "created_at"]


class AuctionRetrieveAPIView(generics.RetrieveAPIView):
    queryset = AuctionListing.objects.all()
    serializer_class = AuctionDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "id"


class UserBidListAPIView(generics.ListAPIView):
    serializer_class = UserAuctionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AuctionListing.objects.filter(bids__bidder=self.request.user).distinct().order_by("-created_at")


class AuctionCreateAPIView(generics.CreateAPIView):
    # TODO: Add logic to deduct listing fee if applicable? For now, free.
    queryset = AuctionListing.objects.all()
    serializer_class = AuctionCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


class AuctionUpdateAPIView(generics.UpdateAPIView):
    queryset = AuctionListing.objects.all()
    serializer_class = AuctionCreateSerializer  # Re-use create serializer for update
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def perform_update(self, serializer):
        auction = self.get_object()
        if auction.product.owner != self.request.user:
            raise PermissionDenied("You do not own this auction.")
        if auction.status != AuctionListing.Status.DRAFT:
            raise ValidationError("You can only edit DRAFT auctions.")
        serializer.save()


class AuctionDeleteAPIView(generics.DestroyAPIView):
    queryset = AuctionListing.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def perform_destroy(self, instance):
        if instance.product.owner != self.request.user:
            raise PermissionDenied("You do not own this auction.")
        if instance.status != AuctionListing.Status.DRAFT:
            raise ValidationError("You can only delete DRAFT auctions.")
        instance.delete()


class PlaceBidAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        auction = generics.get_object_or_404(AuctionListing, id=id)
        serializer = BidCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        amount = serializer.validated_data["amount"]
        user = request.user

        if auction.status != AuctionListing.Status.ACTIVE:
            return Response({"error": "Auction is not active."}, status=status.HTTP_400_BAD_REQUEST)

        if auction.end_time < timezone.now():
            return Response({"error": "Auction has ended."}, status=status.HTTP_400_BAD_REQUEST)

        if user == auction.product.owner:
            return Response({"error": "You cannot bid on your own auction."}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= auction.current_price:
            return Response({"error": "Bid must be higher than current price."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # 1. Check Wallet Balance
            wallet = Wallet.objects.select_for_update().get(user=user)
            # Assuming full amount hold for simplicity, or just check?
            # Let's assume we hold the bid amount.
            if wallet.balance < amount:
                return Response({"error": "Insufficient funds."}, status=status.HTTP_400_BAD_REQUEST)

            # 2. Release previous winner's hold (if any)
            if auction.winner:
                prev_winner_wallet = Wallet.objects.select_for_update().get(user=auction.winner)
                prev_bid = auction.current_price
                prev_winner_wallet.held_balance -= prev_bid
                prev_winner_wallet.balance += prev_bid  # Refund back to balance
                prev_winner_wallet.save()

                WalletTransaction.objects.create(
                    wallet=prev_winner_wallet,
                    transaction_type=WalletTransaction.Type.BID_RELEASE,
                    amount=prev_bid,
                    reference_id=str(auction.id),
                )

            # 3. Hold funds for new bidder
            wallet.balance -= amount
            wallet.held_balance += amount
            wallet.save()

            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type=WalletTransaction.Type.BID_HOLD,
                amount=amount,
                reference_id=str(auction.id),
            )

            # 4. Create Bid
            BidTransaction.objects.create(auction=auction, bidder=user, amount=amount)

            # 5. Update Auction
            auction.current_price = amount
            auction.winner = user
            auction.save()

        return Response({"status": "Bid placed successfully."}, status=status.HTTP_201_CREATED)


class BuyNowAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        auction = generics.get_object_or_404(AuctionListing, id=id)
        user = request.user

        if not auction.buy_now_price:
            return Response({"error": "Buy Now not available."}, status=status.HTTP_400_BAD_REQUEST)

        if auction.status != AuctionListing.Status.ACTIVE:
            return Response({"error": "Auction is not active."}, status=status.HTTP_400_BAD_REQUEST)

        if user == auction.product.owner:
            return Response({"error": "You cannot buy your own item."}, status=status.HTTP_400_BAD_REQUEST)

        price = auction.buy_now_price

        with transaction.atomic():
            # 1. Check/Deduct Funds
            wallet = Wallet.objects.select_for_update().get(user=user)
            if wallet.balance < price:
                return Response({"error": "Insufficient funds."}, status=status.HTTP_400_BAD_REQUEST)

            # 2. Refund previous highest bidder if exists
            if auction.winner:
                prev_winner_wallet = Wallet.objects.select_for_update().get(user=auction.winner)
                prev_bid = auction.current_price
                prev_winner_wallet.held_balance -= prev_bid
                prev_winner_wallet.balance += prev_bid
                prev_winner_wallet.save()
                WalletTransaction.objects.create(
                    wallet=prev_winner_wallet,
                    transaction_type=WalletTransaction.Type.BID_RELEASE,
                    amount=prev_bid,
                    reference_id=str(auction.id),
                )

            # 3. Process Payment (Immediate Transfer logic could go here, but for now we hold -> close)
            # Actually, Buy Now usually means immediate sold.
            wallet.balance -= price
            # We move it to held or directly subtract? Let's move to held and mark auction finished.
            # The system will process "Finished" auctions to transfer money to seller.
            wallet.held_balance += price
            wallet.save()

            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type=WalletTransaction.Type.PAYMENT,  # Or BID_HOLD then PAYMENT?
                amount=price,
                reference_id=str(auction.id),
            )

            # 4. Update Auction
            auction.winner = user
            auction.current_price = price
            auction.status = AuctionListing.Status.FINISHED
            auction.end_time = timezone.now()  # End immediately
            auction.save()

            # TODO: Create delivery order etc.

        return Response({"status": "Item purchased successfully."}, status=status.HTTP_200_OK)
