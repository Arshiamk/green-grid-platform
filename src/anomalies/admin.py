from django.contrib import admin

from .models import Anomaly


@admin.register(Anomaly)
class AnomalyAdmin(admin.ModelAdmin):
    list_display = (
        "title", "meter", "anomaly_type", "severity",
        "detected_at", "is_resolved", "created_at",
    )
    list_filter = ("anomaly_type", "severity", "is_resolved")
    search_fields = ("title", "meter__mpan")
