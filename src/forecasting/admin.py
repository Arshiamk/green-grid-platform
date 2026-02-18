from django.contrib import admin

from .models import DemandForecast, ForecastPoint


class ForecastPointInline(admin.TabularInline):
    model = ForecastPoint
    extra = 0
    readonly_fields = ("timestamp", "predicted_kwh", "lower_bound_kwh", "upper_bound_kwh")


@admin.register(DemandForecast)
class DemandForecastAdmin(admin.ModelAdmin):
    list_display = (
        "meter", "granularity", "forecast_start",
        "forecast_end", "total_predicted_kwh", "created_at",
    )
    list_filter = ("granularity",)
    search_fields = ("meter__mpan",)
    inlines = [ForecastPointInline]
