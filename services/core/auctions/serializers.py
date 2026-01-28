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
