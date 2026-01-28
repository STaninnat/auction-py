from typing import Any

from common.models import TimestampMixin, UUIDMixin
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class Wallet(UUIDMixin, TimestampMixin):
    """
    User Wallet
    Logic: Total Money = balance + held_balance
    - balance: Freely available money
    - held_balance: Money locked and awaiting payment (temporarily when you win the auction)
    """

    user: models.OneToOneField = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="wallet"
    )
    balance: models.DecimalField = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Freely available money",
        verbose_name="Balance",
    )
    held_balance: models.DecimalField = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Money locked and awaiting payment (temporarily when you win the auction)",
        verbose_name="Held Balance",
    )

    class Meta:
        constraints = [
            # Constraint: balance and held_balance must be non-negative
            models.CheckConstraint(condition=Q(balance__gte=0), name="check_wallet_balance_positive"),
            models.CheckConstraint(condition=Q(held_balance__gte=0), name="check_held_balance_positive"),
        ]

    def __str__(self):
        return f"Wallet of {self.user} (Avail: {self.balance}, Held: {self.held_balance})"


class WalletTransaction(UUIDMixin, TimestampMixin):
    """
    Audit Log: The entire financial transaction history.
    """

    class Type(models.TextChoices):
        DEPOSIT = "DEPOSIT", _("Deposit")
        WITHDRAW = "WITHDRAW", _("Withdraw")
        BID_HOLD = "BID_HOLD", _("Bid Hold")  # Lock in funds when bidding.
        BID_RELEASE = "BID_RELEASE", _("Bid Release")  # Release funds when bidding is released.
        PAYMENT = "PAYMENT", _("Payment")  # Payment when winning the auction.
        REFUND = "REFUND", _("Refund")

    wallet: Any = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    transaction_type: models.CharField = models.CharField(
        max_length=20,
        choices=Type.choices,
        db_index=True,
        verbose_name="Transaction Type",
    )
    amount: models.DecimalField = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )
    reference_id: models.CharField = models.CharField(
        max_length=100, blank=True, null=True, db_index=True, help_text="e.g. Auction ID or Stripe Charge ID"
    )

    def __str__(self):
        return f"{self.transaction_type}: {self.amount} ({self.wallet.user})"


class WithdrawalRequest(UUIDMixin, TimestampMixin):
    """
    Manual Withdrawal Requests
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        APPROVED = "APPROVED", _("Approved - Paid")
        REJECTED = "REJECTED", _("Rejected")

    user: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="withdrawals",
    )
    amount: models.DecimalField = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Amount"),
    )
    status: models.CharField = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name=_("Status"),
    )
    bank_details: models.TextField = models.TextField(
        verbose_name=_("Bank Details / Notes"),
        help_text="IBAN, Swift, Account Number, etc.",
    )
    admin_note: models.TextField = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Admin Note"),
    )

    def __str__(self):
        return f"Withdrawal: {self.amount} - {self.user} ({self.status})"
