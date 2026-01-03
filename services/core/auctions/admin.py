from django.contrib import admin

from .models import AuctionListing, BidTransaction, Product


class BidTransactionInline(admin.TabularInline):
    model = BidTransaction
    extra = 0
    readonly_fields = ("bidder", "amount", "created_at")
    can_delete = False


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "created_at")
    search_fields = ("title", "owner__username")


@admin.register(AuctionListing)
class AuctionListingAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "status", "current_price", "end_time")
    list_filter = ("status", "start_time", "end_time")
    search_fields = ("product__title",)
    inlines = [BidTransactionInline]


@admin.register(BidTransaction)
class BidTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "bidder", "auction", "amount", "created_at")
    readonly_fields = ("bidder", "auction", "amount", "created_at")
