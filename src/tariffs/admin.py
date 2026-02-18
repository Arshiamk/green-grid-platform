from django.contrib import admin

from .models import CustomerTariff, RateBand, Tariff


class RateBandInline(admin.TabularInline):
    model = RateBand
    extra = 1


class CustomerTariffInline(admin.TabularInline):
    model = CustomerTariff
    extra = 0
    raw_id_fields = ("customer",)


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "fuel_type", "tariff_type", "standing_charge_pence", "is_active", "valid_from")
    list_filter = ("fuel_type", "tariff_type", "is_active")
    search_fields = ("name", "code")
    inlines = [RateBandInline, CustomerTariffInline]


@admin.register(CustomerTariff)
class CustomerTariffAdmin(admin.ModelAdmin):
    list_display = ("customer", "tariff", "effective_from", "effective_to")
    list_filter = ("effective_from",)
    raw_id_fields = ("customer", "tariff")
