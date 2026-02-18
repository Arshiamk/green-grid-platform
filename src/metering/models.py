import uuid

from django.db import models

from customers.models import Meter


class MeterReading(models.Model):
    """Individual meter reading — actual or estimated."""

    READING_TYPES = [
        ("actual", "Actual"),
        ("estimated", "Estimated"),
    ]

    meter = models.ForeignKey(
        Meter, on_delete=models.CASCADE, related_name="readings"
    )
    reading_at = models.DateTimeField(db_index=True)
    value_kwh = models.DecimalField(max_digits=12, decimal_places=4)
    reading_type = models.CharField(max_length=10, choices=READING_TYPES, default="actual")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reading_at"]
        indexes = [
            models.Index(fields=["meter", "reading_at"]),
        ]

    def __str__(self):
        return f"{self.meter.mpan} @ {self.reading_at:%Y-%m-%d %H:%M} — {self.value_kwh} kWh"


class UploadedFile(models.Model):
    """Tracks a CSV file uploaded for meter reading ingestion."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to="uploads/readings/")
    original_filename = models.CharField(max_length=255)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending")
    rows_total = models.PositiveIntegerField(default=0)
    rows_ok = models.PositiveIntegerField(default=0)
    rows_failed = models.PositiveIntegerField(default=0)
    error_log = models.TextField(blank=True, help_text="Per-row errors as JSON lines")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.original_filename} — {self.status}"
