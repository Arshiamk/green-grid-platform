from django.contrib import admin

from .models import Bill, BillLineItem, Payment


class BillLineItemInline(admin.TabularInline):
    model = BillLineItem
    extra = 0
    readonly_fields = ("description", "rate_band_label", "kwh", "rate_pence_per_kwh", "amount_pence")


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
        "id", "customer", "period_start", "period_end",
        "status", "total_kwh", "total_amount_display", "created_at",
    )
    list_filter = ("status", "period_start", "created_at")
    search_fields = ("customer__account_number", "customer__last_name", "id")
    inlines = [BillLineItemInline]
    date_hierarchy = "created_at"

    @admin.display(description="Total (£)")
    def total_amount_display(self, obj):
        return f"£{obj.total_amount_pence / 100:.2f}"

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "bill", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("bill__id", "stripe_payment_intent_id")
    raw_id_fields = ("bill",)
    date_hierarchy = "created_at"

