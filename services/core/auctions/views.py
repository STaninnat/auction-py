from rest_framework import generics, permissions

from .models import AuctionListing
from .serializers import AuctionListingSerializer


class AuctionListAPIView(generics.ListAPIView):
    serializer_class = AuctionListingSerializer
    permission_class = [permissions.AllowAny]

    def get_queryset(self):
        return AuctionListing.objects.filter(status="ACTIVE").order_by("-created_at")


class AuctionRetrieveAPIView(generics.RetrieveAPIView):
    queryset = AuctionListing.objects.all()
    serializer_class = AuctionListingSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "id"
