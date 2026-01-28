from django.urls import path

from .views import (
    DepositAPIView,
    StripeWebhookView,
    WalletRetrieveAPIView,
    WalletTransactionListAPIView,
    WithdrawalListAPIView,
    WithdrawAPIView,
)

urlpatterns = [
    path("wallet/", WalletRetrieveAPIView.as_view(), name="wallet-detail"),
    path("deposit/", DepositAPIView.as_view(), name="deposit"),
    path("withdraw/", WithdrawAPIView.as_view(), name="withdraw"),
    path("webhook/stripe/", StripeWebhookView.as_view(), name="stripe-webhook"),
    path("transactions/", WalletTransactionListAPIView.as_view(), name="wallet_transactions"),
    path("withdrawals/", WithdrawalListAPIView.as_view(), name="withdrawal_requests"),
]
