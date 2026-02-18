from django.contrib import admin

from .models import Customer, Meter, Property


class PropertyInline(admin.TabularInline):
    model = Property
    extra = 0
    show_change_link = True


class MeterInline(admin.TabularInline):
    model = Meter
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("account_number", "first_name", "last_name", "email", "created_at")
    search_fields = ("account_number", "first_name", "last_name", "email")
    list_filter = ("created_at",)
    inlines = [PropertyInline]
    ordering = ("-created_at",)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("address_line_1", "city", "postcode", "property_type", "customer")
    search_fields = ("address_line_1", "postcode", "customer__last_name", "customer__account_number")
    list_filter = ("property_type", "city")
    inlines = [MeterInline]


@admin.register(Meter)
class MeterAdmin(admin.ModelAdmin):
    list_display = ("mpan", "serial_number", "fuel_type", "is_smart", "property_address")
    search_fields = ("mpan", "serial_number", "property__address_line_1")
    list_filter = ("fuel_type", "is_smart")

    @admin.display(description="Property")
    def property_address(self, obj):
        return obj.property.address_line_1 if obj.property else "N/A"

