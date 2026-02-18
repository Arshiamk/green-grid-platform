import uuid

from django.db import models

from customers.models import Meter


class DemandForecast(models.Model):
    """Forecast run for a meter over a future period."""

    GRANULARITY_CHOICES = [
        ("half_hourly", "Half-hourly"),
        ("hourly", "Hourly"),
        ("daily", "Daily"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meter = models.ForeignKey(
        Meter, on_delete=models.CASCADE, related_name="forecasts"
    )
    granularity = models.CharField(max_length=15, choices=GRANULARITY_CHOICES, default="half_hourly")
    forecast_start = models.DateTimeField()
    forecast_end = models.DateTimeField()
    lookback_days = models.PositiveIntegerField(
        default=7,
        help_text="Number of historical days used for the prediction",
    )
    total_predicted_kwh = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Forecast {self.meter.mpan} | {self.forecast_start:%Y-%m-%d} → {self.forecast_end:%Y-%m-%d}"


class ForecastPoint(models.Model):
    """Individual predicted data point within a forecast."""

    forecast = models.ForeignKey(
        DemandForecast, on_delete=models.CASCADE, related_name="points"
    )
    timestamp = models.DateTimeField()
    predicted_kwh = models.DecimalField(max_digits=12, decimal_places=4)
    lower_bound_kwh = models.DecimalField(max_digits=12, decimal_places=4)
    upper_bound_kwh = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} — {self.predicted_kwh} kWh"
