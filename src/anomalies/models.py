import uuid

from django.db import models

from customers.models import Meter


class Anomaly(models.Model):
    """Detected anomaly in meter reading patterns."""

    ANOMALY_TYPES = [
        ("spike", "Usage Spike"),
        ("drop", "Usage Drop"),
        ("gap", "Reading Gap"),
        ("negative", "Negative Reading"),
        ("flatline", "Flatline"),
    ]

    SEVERITY_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meter = models.ForeignKey(
        Meter, on_delete=models.CASCADE, related_name="anomalies"
    )
    anomaly_type = models.CharField(max_length=15, choices=ANOMALY_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default="warning")
    title = models.CharField(max_length=200)
    description = models.TextField()
    detected_at = models.DateTimeField()
    value_kwh = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True,
        help_text="The anomalous reading value",
    )
    expected_kwh = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True,
        help_text="The expected normal value",
    )
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "anomalies"
        ordering = ["-detected_at"]

    def __str__(self):
        return f"[{self.severity.upper()}] {self.title}"
