from django.contrib import admin

from .models import Wallet, WalletTransaction, WithdrawalRequest


class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    readonly_fields = ("transaction_type", "amount", "reference_id", "created_at")
    can_delete = False


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "held_balance", "updated_at")
    search_fields = ("user__username", "user__email")
    inlines = [WalletTransactionInline]


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("wallet", "transaction_type", "amount", "reference_id", "created_at")
    list_filter = ("transaction_type", "created_at")
    readonly_fields = ("wallet", "transaction_type", "amount", "reference_id", "created_at")
    search_fields = ("wallet__user__username", "reference_id")
    date_hierarchy = "created_at"


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "user__email", "bank_details")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
