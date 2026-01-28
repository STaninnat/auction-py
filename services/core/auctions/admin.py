from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import AuctionListing, BidTransaction, Product


class BidTransactionInline(admin.TabularInline):
    model = BidTransaction
    extra = 0
    readonly_fields = ("bidder", "amount", "created_at")
    can_delete = False


class AuctionListingInline(admin.StackedInline):
    model = AuctionListing
    extra = 0
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "condition", "owner", "image_preview", "created_at")
    list_filter = ("category", "condition", "created_at")
    search_fields = ("title", "owner__username")
    inlines = [AuctionListingInline]

    @admin.display(description=_("Image"))
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.image.url)
        return "-"


@admin.register(AuctionListing)
class AuctionListingAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "colored_status", "current_price", "buy_now_price", "end_time")
    list_filter = ("status", "product__category", "start_time", "end_time")
    search_fields = ("product__title", "winner__username", "winner__email")
    date_hierarchy = "created_at"
    inlines = [BidTransactionInline]
    actions = ["cancel_auctions"]
    fieldsets = (
        (None, {"fields": ("product", "status", "winner")}),
        (_("Time Settings"), {"fields": ("start_time", "end_time")}),
        (_("Price Settings"), {"fields": ("starting_price", "buy_now_price", "current_price")}),
        (_("System Info"), {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")

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

    @admin.display(description=_("Status"), ordering="status")
    def colored_status(self, obj):
        colors = {
            AuctionListing.Status.ACTIVE: "green",
            AuctionListing.Status.FINISHED: "blue",
            AuctionListing.Status.EXPIRED: "gray",
            AuctionListing.Status.CANCELLED: "red",
            AuctionListing.Status.DRAFT: "orange",
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, "black"),
            obj.get_status_display(),
        )


@admin.register(BidTransaction)
class BidTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "bidder", "auction", "amount", "created_at")
    readonly_fields = ("bidder", "auction", "amount", "created_at")
