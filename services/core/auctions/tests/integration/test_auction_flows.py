from decimal import Decimal

import pytest
from django.urls import reverse
from payments.models import Wallet
from rest_framework import status
from users.tests.factories import UserFactory

from auctions.models import AuctionListing
from auctions.tests.factories import AuctionListingFactory


@pytest.mark.django_db
class TestAuctionFlows:
    def test_create_auction(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)

        url = reverse("auction_create")
        data = {
            "title": "My New Item",
            "description": "Mint condition",
            "category": "ELECTRONICS",
            "condition": "NEW",
            "start_time": "2026-01-01T12:00:00Z",
            "end_time": "2026-01-02T12:00:00Z",
            "starting_price": "100.00",
            "buy_now_price": "200.00",
        }

        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED

        auction = AuctionListing.objects.get(id=response.data["id"])
        assert auction.product.title == "My New Item"
        assert auction.product.owner == user
        assert auction.status == "DRAFT"
        assert auction.current_price == Decimal("100.00")

    def test_place_bid_flow(self, api_client):
        # 1. Setup Auction and Users
        seller = UserFactory(username="seller")
        bidder1 = UserFactory(username="bidder1")
        bidder2 = UserFactory(username="bidder2")

        # Fund bidders
        Wallet.objects.create(user=bidder1, balance=500)
        Wallet.objects.create(user=bidder2, balance=500)

        auction = AuctionListingFactory(
            status=AuctionListing.Status.ACTIVE, starting_price="10.00", current_price="10.00", product__owner=seller
        )

        url_bid = reverse("auction_bid", kwargs={"id": auction.id})

        # 2. Bidder 1 places bid
        api_client.force_authenticate(user=bidder1)
        response = api_client.post(url_bid, {"amount": "50.00"})
        assert response.status_code == status.HTTP_201_CREATED

        auction.refresh_from_db()
        assert auction.current_price == Decimal("50.00")
        assert auction.winner == bidder1

        w1 = Wallet.objects.get(user=bidder1)
        assert w1.balance == 450  # 500 - 50 held
        assert w1.held_balance == 50

        # 3. Bidder 2 outbids
        api_client.force_authenticate(user=bidder2)
        response = api_client.post(url_bid, {"amount": "100.00"})
        assert response.status_code == status.HTTP_201_CREATED

        auction.refresh_from_db()
        assert auction.current_price == Decimal("100.00")
        assert auction.winner == bidder2

        # Check Bidder 1 refunded
        w1.refresh_from_db()
        assert w1.balance == 500
        assert w1.held_balance == 0

        # Check Bidder 2 funds held
        w2 = Wallet.objects.get(user=bidder2)
        assert w2.balance == 400  # 500 - 100
        assert w2.held_balance == 100

    def test_buy_now_flow(self, api_client):
        buyer = UserFactory()
        Wallet.objects.create(user=buyer, balance=1000)

        auction = AuctionListingFactory(
            status=AuctionListing.Status.ACTIVE, starting_price="100.00", current_price="100.00", buy_now_price="500.00"
        )

        api_client.force_authenticate(user=buyer)
        url = reverse("auction_buy_now", kwargs={"id": auction.id})

        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        auction.refresh_from_db()
        assert auction.status == AuctionListing.Status.FINISHED
        assert auction.winner == buyer
        assert auction.current_price == Decimal("500.00")

        # Check wallet
        w = Wallet.objects.get(user=buyer)
        assert w.balance == 500
        assert w.held_balance == 500  # Moved to held awaiting payout logic
