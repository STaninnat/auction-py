import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

from .models import AuctionListing
from .serializers import AuctionDetailSerializer, AuctionListingSerializer, UserAuctionSerializer


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
