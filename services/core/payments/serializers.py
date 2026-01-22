from rest_framework import serializers

from .models import Wallet, WithdrawalRequest


class WalletSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for User's Wallet
    """

    class Meta:
        model = Wallet
        fields = ["id", "balance", "held_balance", "created_at", "updated_at"]
        read_only_fields = fields


class DepositSerializer(serializers.Serializer):
    """
    Serializer to validate deposit amount
    """

    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)


class WithdrawSerializer(serializers.ModelSerializer):
    """
    Serializer for creating withdrawal requests
    """

    class Meta:
        model = WithdrawalRequest
        fields = ["id", "amount", "status", "bank_details", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive.")

        return value
