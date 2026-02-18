import uuid

from django.db import models


from django.contrib.auth.models import User
from django.db import models


class Customer(models.Model):
    """Energy customer account."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    account_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.account_number} — {self.first_name} {self.last_name}"


class Property(models.Model):
    """Physical property linked to a customer account."""

    PROPERTY_TYPES = [
        ("house", "House"),
        ("flat", "Flat"),
        ("bungalow", "Bungalow"),
        ("commercial", "Commercial"),
        ("other", "Other"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="properties"
    )
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    postcode = models.CharField(max_length=10)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES, default="house")

    class Meta:
        verbose_name_plural = "properties"
        ordering = ["postcode"]

    def __str__(self):
        return f"{self.address_line_1}, {self.postcode}"


class Meter(models.Model):
    """Physical or smart meter installed at a property."""

    FUEL_TYPES = [
        ("electricity", "Electricity"),
        ("gas", "Gas"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="meters"
    )
    mpan = models.CharField(
        "MPAN / MPRN",
        max_length=21,
        unique=True,
        help_text="Meter Point Administration Number (electricity) or Meter Point Reference Number (gas)",
    )
    serial_number = models.CharField(max_length=20)
    fuel_type = models.CharField(max_length=15, choices=FUEL_TYPES)
    is_smart = models.BooleanField(default=False)
    installed_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["mpan"]

    def __str__(self):
        return f"{self.get_fuel_type_display()} — {self.mpan}"
