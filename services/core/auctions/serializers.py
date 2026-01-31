from rest_framework import serializers
from users.models import User

from .models import AuctionListing, BidTransaction, Product


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class MaskedUserSummarySerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username"]

    def get_username(self, obj):
        if not obj.username:
            return "Anonymous"

        # Simple masking: "j***e"
        if len(obj.username) <= 2:
            return f"{obj.username[0]}***"

        return f"{obj.username[0]}***{obj.username[-1]}"


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
    bidder = MaskedUserSummarySerializer(read_only=True)

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


class AuctionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating an auction listing along with the product.
    """

    title = serializers.CharField(source="product.title")
    description = serializers.CharField(source="product.description", required=False)
    image = serializers.ImageField(source="product.image", required=False)
    category = serializers.ChoiceField(choices=Product.Category.choices, source="product.category")
    condition = serializers.ChoiceField(choices=Product.Condition.choices, source="product.condition")

    class Meta:
        model = AuctionListing
        fields = [
            "id",
            "title",
            "description",
            "image",
            "category",
            "condition",
            "start_time",
            "end_time",
            "starting_price",
            "buy_now_price",
        ]

    def create(self, validated_data):
        product_data = validated_data.pop("product")
        owner = self.context["request"].user

        # Create Product
        product = Product.objects.create(owner=owner, **product_data)

        # Create Auction Listing
        # Initialize current_price to starting_price
        validated_data["current_price"] = validated_data["starting_price"]
        auction = AuctionListing.objects.create(product=product, status=AuctionListing.Status.DRAFT, **validated_data)

        return auction


class BidCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Bid amount must be positive.")
        return value
