import uuid

from django.db import models

from customers.models import Customer, Meter
from tariffs.models import Tariff


class Bill(models.Model):
    """Monthly or periodic bill for a customer."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("issued", "Issued"),
        ("paid", "Paid"),
        ("void", "Void"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="bills"
    )
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")

    # Totals (all in pence)
    total_kwh = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    standing_charge_pence = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    usage_charge_pence = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount_pence = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    issued_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-period_start"]
        unique_together = ["customer", "period_start", "period_end"]

    def __str__(self):
        total_pounds = self.total_amount_pence / 100
        return f"Bill {self.customer.account_number} | {self.period_start} → {self.period_end} | £{total_pounds:.2f}"

    @property
    def total_pounds(self):
        return self.total_amount_pence / 100


class BillLineItem(models.Model):
    """Itemised charge within a bill."""

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="line_items")
    meter = models.ForeignKey(Meter, on_delete=models.SET_NULL, null=True, blank=True)
    tariff = models.ForeignKey(Tariff, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=200)
    rate_band_label = models.CharField(max_length=50, blank=True)
    kwh = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    rate_pence_per_kwh = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    amount_pence = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.description} - {self.amount_pence / 100:.2f}"


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, default="PENDING")  # PENDING, SUCCEEDED, FAILED
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} for Bill {self.bill.id}"
