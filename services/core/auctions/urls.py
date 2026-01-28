from django.urls import path

from .views import (
    AuctionCreateAPIView,
    AuctionDeleteAPIView,
    AuctionListAPIView,
    AuctionRetrieveAPIView,
    AuctionUpdateAPIView,
    BuyNowAPIView,
    PlaceBidAPIView,
    UserBidListAPIView,
)

urlpatterns = [
    path("", AuctionListAPIView.as_view(), name="auction_list"),  # /api/auctions/
    path("create/", AuctionCreateAPIView.as_view(), name="auction_create"),
    path("<uuid:id>/", AuctionRetrieveAPIView.as_view(), name="auction_detail"),  # /api/auctions/<id>/
    path("<uuid:id>/update/", AuctionUpdateAPIView.as_view(), name="auction_update"),
    path("<uuid:id>/delete/", AuctionDeleteAPIView.as_view(), name="auction_delete"),
    path("<uuid:id>/bid/", PlaceBidAPIView.as_view(), name="auction_bid"),
    path("<uuid:id>/buy-now/", BuyNowAPIView.as_view(), name="auction_buy_now"),
    path("my-bids/", UserBidListAPIView.as_view(), name="user_bids"),
]
