from rest_framework import serializers
from users.models import User

from .models import AuctionListing, BidTransaction, Product


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class ProductSerializer(serializers.ModelSerializer):
    owner = UserSummarySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ["id", "title", "description", "image", "category", "condition", "owner", "created_at"]


class AuctionListingSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = AuctionListing
        fields = [
            "id",
            "product",
            "current_price",
            "starting_price",
            "status",
            "start_time",
            "end_time",
        ]


class BidTransactionSerializer(serializers.ModelSerializer):
    bidder = UserSummarySerializer(read_only=True)

    class Meta:
        model = BidTransaction
        fields = ["id", "bidder", "amount", "created_at"]


class AuctionDetailSerializer(AuctionListingSerializer):
    bids = BidTransactionSerializer(many=True, read_only=True)

    class Meta(AuctionListingSerializer.Meta):
        fields = AuctionListingSerializer.Meta.fields + ["bids"]


class UserAuctionSerializer(AuctionListingSerializer):
    user_status = serializers.SerializerMethodField()
    my_highest_bid = serializers.SerializerMethodField()

    class Meta(AuctionListingSerializer.Meta):
        fields = AuctionListingSerializer.Meta.fields + ["user_status", "my_highest_bid"]

    def get_my_highest_bid(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return None
        # Simplified: fetch latest bid by user
        highest_bid = obj.bids.filter(bidder=user).order_by("-amount").first()
        return highest_bid.amount if highest_bid else None

    def get_user_status(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return "GUEST"

        highest_bid_amount = self.get_my_highest_bid(obj)
        if not highest_bid_amount:
            return "NO_BID"

        # Simplified winning logic
        if highest_bid_amount >= obj.current_price:
            return "WINNING"
        else:
            return "OUTBID"
