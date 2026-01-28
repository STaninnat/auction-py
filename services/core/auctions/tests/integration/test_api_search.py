import pytest
from django.urls import reverse
from rest_framework import status

from auctions.models import AuctionListing, Product
from auctions.tests.factories import AuctionListingFactory, ProductFactory


@pytest.mark.django_db
class TestAuctionSearchAPI:
    def test_search_by_title(self, api_client):
        """Test searching auctions by product title."""
        p1 = ProductFactory(title="Retro Camera", description="A cool camera")
        p2 = ProductFactory(title="Modern Phone", description="Smart device")
        AuctionListingFactory(product=p1, status=AuctionListing.Status.ACTIVE)
        AuctionListingFactory(product=p2, status=AuctionListing.Status.ACTIVE)

        url = reverse("auction_list")
        response = api_client.get(url, {"search": "Camera"})

        assert response.status_code == status.HTTP_200_OK
        assert response.status_code == status.HTTP_200_OK
        results = response.data
        assert len(results) == 1
        assert results[0]["product"]["title"] == "Retro Camera"

    def test_filter_by_category(self, api_client):
        """Test filtering auctions by product category."""
        p1 = ProductFactory(title="Laptop", category=Product.Category.ELECTRONICS)
        p2 = ProductFactory(title="Dress", category=Product.Category.FASHION)
        AuctionListingFactory(product=p1, status=AuctionListing.Status.ACTIVE)
        AuctionListingFactory(product=p2, status=AuctionListing.Status.ACTIVE)

        url = reverse("auction_list")
        response = api_client.get(url, {"category": "ELECTRONICS"})

        assert response.status_code == status.HTTP_200_OK
        results = response.data
        assert len(results) == 1
        assert results[0]["product"]["title"] == "Laptop"

    def test_filter_by_price_range(self, api_client):
        """Test filtering auctions by price range."""
        AuctionListingFactory(current_price="100.00", status=AuctionListing.Status.ACTIVE)
        middle = AuctionListingFactory(current_price="500.00", status=AuctionListing.Status.ACTIVE)
        AuctionListingFactory(current_price="1000.00", status=AuctionListing.Status.ACTIVE)

        url = reverse("auction_list")
        response = api_client.get(url, {"min_price": "200", "max_price": "800"})

        assert response.status_code == status.HTTP_200_OK
        results = response.data
        assert len(results) == 1
        assert results[0]["id"] == str(middle.id)

    def test_sort_by_price_desc(self, api_client):
        """Test sorting by current price descending."""
        a1 = AuctionListingFactory(current_price="10.00", status=AuctionListing.Status.ACTIVE)
        a2 = AuctionListingFactory(current_price="100.00", status=AuctionListing.Status.ACTIVE)

        url = reverse("auction_list")
        response = api_client.get(url, {"ordering": "-current_price"})

        results = response.data
        assert len(results) == 2
        assert results[0]["id"] == str(a2.id)
        assert results[1]["id"] == str(a1.id)
