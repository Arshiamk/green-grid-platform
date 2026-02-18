import uuid

from django.db import models

from customers.models import Customer


class Recommendation(models.Model):
    """Energy-saving or tariff recommendation for a customer."""

    CATEGORY_CHOICES = [
        ("tariff_switch", "Tariff Switch"),
        ("usage_reduction", "Usage Reduction"),
        ("peak_shifting", "Peak Shifting"),
        ("appliance", "Appliance Upgrade"),
        ("general", "General"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="recommendations"
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    title = models.CharField(max_length=200)
    description = models.TextField()
    estimated_saving_pence = models.PositiveIntegerField(
        default=0,
        help_text="Estimated annual saving in pence",
    )
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.priority.upper()}] {self.title}"

    @property
    def estimated_saving_pounds(self):
        return self.estimated_saving_pence / 100
