from django.urls import path

from .views import AuctionListAPIView, AuctionRetrieveAPIView, UserBidListAPIView

urlpatterns = [
    path("", AuctionListAPIView.as_view(), name="auction_list"),  # /api/auctions/
    path("<uuid:id>/", AuctionRetrieveAPIView.as_view(), name="auction_detail"),  # /api/auctions/<id>/
    path("my-bids/", UserBidListAPIView.as_view(), name="user_bids"),
]
