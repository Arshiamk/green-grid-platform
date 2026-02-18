import uuid

from django.db import models

from customers.models import Customer


class Tariff(models.Model):
    """Energy tariff with pricing structure."""

    FUEL_TYPES = [
        ("electricity", "Electricity"),
        ("gas", "Gas"),
    ]

    TARIFF_TYPES = [
        ("fixed", "Fixed"),
        ("variable", "Variable"),
        ("time_of_use", "Time of Use"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30, unique=True)
    fuel_type = models.CharField(max_length=15, choices=FUEL_TYPES)
    tariff_type = models.CharField(max_length=15, choices=TARIFF_TYPES, default="variable")
    standing_charge_pence = models.DecimalField(
        max_digits=8, decimal_places=4,
        help_text="Daily standing charge in pence",
    )
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-valid_from"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class RateBand(models.Model):
    """Time-based rate band within a tariff (e.g. day/night rates)."""

    tariff = models.ForeignKey(
        Tariff, on_delete=models.CASCADE, related_name="rate_bands"
    )
    label = models.CharField(max_length=50, blank=True, help_text="e.g. 'Peak', 'Off-peak', 'Standard'")
    start_time = models.TimeField(null=True, blank=True, help_text="Null for flat-rate tariffs")
    end_time = models.TimeField(null=True, blank=True)
    rate_pence_per_kwh = models.DecimalField(
        max_digits=8, decimal_places=4,
        help_text="Unit rate in pence per kWh",
    )

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        if self.start_time and self.end_time:
            return f"{self.label or 'Band'}: {self.start_time:%H:%M}–{self.end_time:%H:%M} @ {self.rate_pence_per_kwh}p/kWh"
        return f"{self.label or 'Flat rate'}: {self.rate_pence_per_kwh}p/kWh"


class CustomerTariff(models.Model):
    """Links a customer to a tariff for a period."""

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="tariff_assignments"
    )
    tariff = models.ForeignKey(
        Tariff, on_delete=models.CASCADE, related_name="customer_assignments"
    )
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-effective_from"]

    def __str__(self):
        return f"{self.customer.account_number} → {self.tariff.code} (from {self.effective_from})"
