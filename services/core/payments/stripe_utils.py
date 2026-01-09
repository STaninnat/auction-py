import logging

import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


def create_checkout_session(user, amount, currency="usd"):
    """
    Creates a Stripe Checkout Session for a one-time payment.
    The 'amount' is expected to be a Decimal or float.
    Stripe expects amounts in cents (integers).
    """

    try:
        # Convert amount to cents
        amount_in_cents = int(amount * 100)

        # Build success/cancel URLs
        base_url = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "http://localhost:8000"
        if not base_url.startswith("http"):
            base_url = f"http://{base_url}"

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "unit_amount": amount_in_cents,
                        "product_data": {
                            "name": "Wallet Deposit",
                            "description": f"Deposit for user {user.username}",
                        },
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{base_url}/api/payments/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/api/payments/cancel",
            client_reference_id=str(user.id),  # Important: This lets us know WHO paid when the Webhook arrives.
            metadata={"user_id": str(user.id), "username": user.username},
        )
        return checkout_session.url

    except Exception as e:
        logger.error(f"Error creating Stripe session: {e}")
        return None


def handle_webhook_event(payload, sig_header):
    """
    Verifies the webhook signature and returns the event object.
    """

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        return event
    except ValueError:
        # Invalid payload
        return None
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return None
