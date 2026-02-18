from django.contrib import admin

from .models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = (
        "title", "customer", "category", "priority",
        "estimated_saving_pence", "is_dismissed", "created_at",
    )
    list_filter = ("category", "priority", "is_dismissed")
    search_fields = ("title", "customer__account_number")
