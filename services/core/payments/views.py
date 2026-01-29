import logging
from decimal import Decimal

from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, status, views
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Wallet, WalletTransaction, WithdrawalRequest
from .serializers import (
    DepositSerializer,
    WalletSerializer,
    WalletTransactionSerializer,
    WithdrawSerializer,
)
from .stripe_utils import create_checkout_session, handle_webhook_event

logger = logging.getLogger(__name__)


class WalletRetrieveAPIView(generics.RetrieveAPIView):
    """
    Get the current user's wallet balance.
    """

    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Create wallet if it doesn't exist (Auto-provisioning)
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return wallet


class DepositAPIView(views.APIView):
    """
    Initiate a deposit via Stripe Checkout.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DepositSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data["amount"]
            checkout_url = create_checkout_session(request.user, amount)

            if checkout_url:
                return Response({"checkout_url": checkout_url}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Failed to create checkout session"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(views.APIView):
    """
    Handle Stripe Webhooks (e.g., checkout.session.completed)
    """

    permission_classes = [permissions.AllowAny]  # Stripe calls this, not a user.

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        event = handle_webhook_event(payload, sig_header)

        if not event:
            return Response({"status": "invalid payload or signature"}, status=status.HTTP_400_BAD_REQUEST)

        # Handle specific events
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            self.handle_checkout_completed(session)

        return Response({"status": "success"}, status=status.HTTP_200_OK)

    def handle_checkout_completed(self, session):
        """
        Credit the user's wallet.
        """
        try:
            client_reference_id = session.get("client_reference_id")
            amount_total = session.get("amount_total")  # In cents

            if not client_reference_id or amount_total is None:
                logger.error("Missing user ID or amount in session")
                return

            user_id = client_reference_id
            amount = Decimal(amount_total) / 100

            with transaction.atomic():
                # Lock the wallet to update balance safely
                wallet = Wallet.objects.select_for_update().get(user__id=user_id)
                wallet.balance += amount
                wallet.save()

                # Create Transaction Record
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type=WalletTransaction.Type.DEPOSIT,
                    amount=amount,
                    reference_id=session.get("id"),  # Stripe Session ID
                )

                logger.info(f"Deposited {amount} to user {user_id}")

        except Wallet.DoesNotExist:
            logger.error(f"Wallet not found for user {client_reference_id}")
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")


class WithdrawAPIView(generics.CreateAPIView):
    """
    Request a withdrawal.
    """

    serializer_class = WithdrawSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        amount = serializer.validated_data["amount"]
        user = self.request.user

        with transaction.atomic():
            # Lock wallet to check funds
            wallet = Wallet.objects.select_for_update().get(user=user)

            if wallet.balance < amount:
                raise ValidationError({"amount": "Insufficient funds."})

            # Create Request
            withdrawal = serializer.save(user=user)

            wallet.balance -= amount
            wallet.held_balance += amount
            wallet.save()

            # Log the hold
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type=WalletTransaction.Type.WITHDRAW,  # Marking as withdraw intent
                amount=amount,
                reference_id=str(withdrawal.id),
            )


class WalletTransactionListAPIView(generics.ListAPIView):
    serializer_class = WalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return transactions for the current user's wallet
        return WalletTransaction.objects.filter(wallet__user=self.request.user).order_by("-created_at")


class WithdrawalListAPIView(generics.ListAPIView):
    serializer_class = WithdrawSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WithdrawalRequest.objects.filter(user=self.request.user).order_by("-created_at")
