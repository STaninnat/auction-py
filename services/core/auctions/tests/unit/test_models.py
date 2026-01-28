from datetime import timedelta

import pytest
from django.db.utils import IntegrityError
from django.utils import timezone

from auctions.models import AuctionListing
from auctions.tests.factories import AuctionListingFactory, ProductFactory


@pytest.mark.django_db
class TestAuctionListingValidation:
    def test_create_valid_auction(self):
        """Test creating a valid auction listing."""
        auction = AuctionListingFactory()
        assert auction.pk is not None
        assert auction.status == AuctionListing.Status.ACTIVE

    def test_start_time_after_end_time(self):
        """Constraint: start_time must be before end_time."""
        now = timezone.now()
        with pytest.raises(IntegrityError):
            AuctionListingFactory(start_time=now + timedelta(days=1), end_time=now)

    def test_starting_price_negative(self):
        """Constraint: starting_price must be > 0."""
        with pytest.raises(IntegrityError):
            AuctionListingFactory(starting_price="-10.00")

    def test_current_price_lt_starting_price(self):
        """Constraint: current_price >= starting_price."""
        with pytest.raises(IntegrityError):
            AuctionListingFactory(starting_price="100.00", current_price="50.00")

    def test_str_representation(self):
        """Test the string representation of the model."""
        product = ProductFactory(title="Vintage Vase")
        auction = AuctionListingFactory(product=product, status=AuctionListing.Status.ACTIVE)
        assert str(auction) == "Vintage Vase (Status: ACTIVE)"

    def test_product_defaults(self):
        """Test that products have correct default category and condition."""
        product = ProductFactory()
        assert product.category == "OTHER"
        assert product.condition == "USED_GOOD"

    def test_product_valid_choices(self):
        """Test creating product with valid non-default choices."""
        from auctions.models import Product

        product = ProductFactory(category=Product.Category.ELECTRONICS, condition=Product.Condition.NEW)
        assert product.category == "ELECTRONICS"
        assert product.condition == "NEW"
