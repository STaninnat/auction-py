from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

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
    actions = ["cancel_auctions"]

    @admin.action(description=_("Cancel selected auctions"))
    def cancel_auctions(self, request, queryset):
        updated_count = queryset.filter(status__in=[AuctionListing.Status.ACTIVE, AuctionListing.Status.DRAFT]).update(
            status=AuctionListing.Status.CANCELLED
        )

        self.message_user(
            request,
            _("%(count)d auctions were successfully cancelled.") % {"count": updated_count},
            messages.SUCCESS,
        )


@admin.register(BidTransaction)
class BidTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "bidder", "auction", "amount", "created_at")
    readonly_fields = ("bidder", "auction", "amount", "created_at")
