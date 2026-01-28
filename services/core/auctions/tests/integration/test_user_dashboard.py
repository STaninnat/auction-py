import pytest
from django.urls import reverse
from rest_framework import status
from users.tests.factories import UserFactory

from auctions.models import AuctionListing
from auctions.tests.factories import AuctionListingFactory, BidTransactionFactory


@pytest.mark.django_db
class TestUserDashboardAPI:
    def test_my_bids_list(self, api_client):
        """Test listing auctions where user has bid."""
        user = UserFactory()
        other_user = UserFactory()
        api_client.force_authenticate(user=user)

        # Auction 1: User is winning
        a1 = AuctionListingFactory(current_price="100.00", status=AuctionListing.Status.ACTIVE)
        BidTransactionFactory(auction=a1, bidder=user, amount="100.00")

        # Auction 2: User is outbid
        a2 = AuctionListingFactory(current_price="200.00", status=AuctionListing.Status.ACTIVE)
        BidTransactionFactory(auction=a2, bidder=user, amount="150.00")
        BidTransactionFactory(auction=a2, bidder=other_user, amount="200.00")

        # Auction 3: User never bid
        AuctionListingFactory(status=AuctionListing.Status.ACTIVE)

        url = reverse("user_bids")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"] if "results" in response.data else response.data

        # Should return 2 auctions (a1 and a2)
        assert len(results) == 2

        # Verify status context
        # Since ordering is -created_at, and factory creates sequentially, a2 is first, then a1.
        # But factory timestamps might be same, let's check ids or logic.

        # Find result for a1
        res_a1 = next(r for r in results if r["id"] == str(a1.id))
        assert res_a1["user_status"] == "WINNING"
        assert float(res_a1["my_highest_bid"]) == 100.00

        # Find result for a2
        res_a2 = next(r for r in results if r["id"] == str(a2.id))
        assert res_a2["user_status"] == "OUTBID"
        assert float(res_a2["my_highest_bid"]) == 150.00

    def test_my_bids_unauthenticated(self, api_client):
        """Test endpoints returns 401 for guests."""
        url = reverse("user_bids")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
