from __future__ import annotations

from typing import Any

from common.models import TimestampMixin, UUIDMixin
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _


class Product(UUIDMixin, TimestampMixin):  # type: ignore
    owner: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
    )
    title: models.CharField = models.CharField(
        max_length=255,
        verbose_name="Title",
    )
    description: models.TextField = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
    )
    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True,
        verbose_name="Image",
    )

    def __str__(self):
        return self.title


class AuctionListing(UUIDMixin, TimestampMixin):
    """
    Auction Round (Auction Item)
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("Draft")
        ACTIVE = "ACTIVE", _("Active")
        FINISHED = "FINISHED", _("Finished")
        CANCELLED = "CANCELLED", _("Cancelled")

    product: Any = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="auctions",
    )
    status: models.CharField = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        verbose_name=_("Status"),
    )

    # Time Settings
    start_time: models.DateTimeField = models.DateTimeField(
        verbose_name=_("Start Time"),
    )
    end_time: models.DateTimeField = models.DateTimeField(
        verbose_name=_("End Time"),
    )

    # Money Settings
    starting_price: models.DecimalField = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Starting Price"),
    )
    buy_now_price: models.DecimalField = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Buy Now Price"),
    )
    current_price: models.DecimalField = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Current Price"),
    )

    #  Winner Info
    winner: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="won_auctions",
        verbose_name=_("Winner"),
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # Constraint 1: start_time must be before end_time
            models.CheckConstraint(
                check=Q(end_time__gt=F("start_time")),
                name="check_end_time_after_start_time",
            ),
            # Constraint 2: starting_price must be greater than 0
            models.CheckConstraint(check=Q(start_price__gt=0), name="check_start_price_positive"),
            # Constraint 3: current_price must be greater than starting_price
            models.CheckConstraint(
                check=Q(current_price__gte=F("start_price")), name="check_current_price_gte_start_price"
            ),
        ]

    def __str__(self):
        return f"{self.product.title} (Status: {self.status})"


class BidTransaction(UUIDMixin, TimestampMixin):
    """
    Auction History (Immutable Log)
    """

    bidder: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bids",
    )
    auction: models.ForeignKey = models.ForeignKey(AuctionListing, on_delete=models.CASCADE, related_name="bids")
    amount: models.DecimalField = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Amount"),
    )

    class Meta:
        ordering = ["-amount"]
        indexes = [
            models.Index(fields=["auction", "amount"]),
        ]
        constraints = [
            # Constraint: The bid price cannot be negative or zero.
            models.CheckConstraint(check=Q(amount__gt=0), name="check_bid_amount_positive"),
        ]

    def __str__(self):
        return f"{self.bidder} bid {self.amount} on {self.auction}"
