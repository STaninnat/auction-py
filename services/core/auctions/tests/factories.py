from datetime import timedelta

from django.utils import timezone
from factory.declarations import LazyAttribute, LazyFunction, Sequence, SubFactory
from factory.django import DjangoModelFactory
from users.tests.factories import UserFactory

from auctions.models import AuctionListing, BidTransaction, Product


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    owner = SubFactory(UserFactory)
    title = Sequence(lambda n: f"Product {n}")
    description = "Test Description"
    # Skipping image for now to avoid file system issues in tests


class AuctionListingFactory(DjangoModelFactory):
    class Meta:
        model = AuctionListing

    product = SubFactory(ProductFactory)
    status = AuctionListing.Status.ACTIVE
    start_time = LazyFunction(timezone.now)
    end_time = LazyAttribute(lambda o: o.start_time + timedelta(days=7))
    starting_price = "10.00"
    current_price = "10.00"
    buy_now_price = "100.00"


class BidTransactionFactory(DjangoModelFactory):
    class Meta:
        model = BidTransaction

    bidder = SubFactory(UserFactory)
    auction = SubFactory(AuctionListingFactory)
    amount = "20.00"
