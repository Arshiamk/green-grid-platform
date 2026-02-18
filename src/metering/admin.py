from django.contrib import admin

from .models import MeterReading, UploadedFile


@admin.register(MeterReading)
class MeterReadingAdmin(admin.ModelAdmin):
    list_display = ("meter", "reading_at", "value_kwh", "reading_type", "created_at")
    list_filter = ("reading_type", "reading_at")
    search_fields = ("meter__mpan",)
    date_hierarchy = "reading_at"
    raw_id_fields = ("meter",)


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = (
        "original_filename", "status", "rows_total",
        "rows_ok", "rows_failed", "created_at", "completed_at",
    )
    list_filter = ("status",)
    readonly_fields = ("error_log",)
