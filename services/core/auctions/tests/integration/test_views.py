import pytest
from django.urls import reverse
from rest_framework import status

from auctions.models import AuctionListing
from auctions.tests.factories import AuctionListingFactory


@pytest.mark.django_db
class TestAuctionListAPI:
    def test_list_active_auctions(self, api_client):
        """Test listing only active auctions."""
        # Create one active and one draft auction
        active_auction = AuctionListingFactory(status=AuctionListing.Status.ACTIVE)
        AuctionListingFactory(status=AuctionListing.Status.DRAFT)

        url = reverse("auction_list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Check that we got results
        results = response.data["results"] if "results" in response.data else response.data
        assert len(results) == 1
        assert results[0]["id"] == str(active_auction.id)

    def test_retrieve_auction_detail(self, api_client):
        """Test retrieving a specific auction details."""
        auction = AuctionListingFactory(status=AuctionListing.Status.ACTIVE)

        url = reverse("auction_detail", kwargs={"id": auction.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(auction.id)
        assert response.data["current_price"] == str(auction.current_price)

    def test_retrieve_not_found(self, api_client):
        """Test 404 for non-existent auction."""
        import uuid

        url = reverse("auction_detail", kwargs={"id": uuid.uuid4()})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
