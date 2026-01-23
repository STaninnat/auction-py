from datetime import timedelta
from decimal import Decimal

from auctions.models import AuctionListing, Product
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from payments.models import Wallet

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds database for E2E tests"

    def handle(self, *args, **options):
        # 1. Create Owner User
        owner, _ = User.objects.get_or_create(username="e2e_owner", defaults={"email": "owner@example.com"})
        owner.set_password("StrongPassword123!")
        owner.save()
        Wallet.objects.get_or_create(user=owner)  # Ensure wallet

        # 2. Create Bidder User
        bidder, _ = User.objects.get_or_create(username="e2e_bidder", defaults={"email": "bidder@example.com"})
        bidder.set_password("StrongPassword123!")
        bidder.save()

        # Fund Bidder
        wallet, _ = Wallet.objects.get_or_create(user=bidder)
        wallet.balance = Decimal("1000.00")
        wallet.save()
        self.stdout.write(self.style.SUCCESS("Created e2e_owner and funded e2e_bidder"))

        # 3. Create Product (Owned by Owner)
        product, created = Product.objects.get_or_create(
            title="E2E Product",
            owner=owner,
            defaults={
                "description": "Created for E2E testing",
            },
        )

        # 4. Create Active Auction
        now = timezone.now()
        end_time = now + timedelta(hours=1)

        auction, created = AuctionListing.objects.get_or_create(
            product=product,
            defaults={
                "status": AuctionListing.Status.ACTIVE,
                "start_time": now,
                "end_time": end_time,
                "starting_price": Decimal("10.00"),
                "current_price": Decimal("10.00"),
            },
        )

        # Ensure it's active in case it existed
        if not created:
            auction.status = AuctionListing.Status.ACTIVE
            if auction.end_time < now:
                auction.end_time = end_time
            auction.save()

        self.stdout.write(self.style.SUCCESS(f"Seeded Auction: {auction.id}"))
