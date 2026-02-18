from rest_framework import serializers

from .models import Recommendation


class RecommendationSerializer(serializers.ModelSerializer):
    estimated_saving_pounds = serializers.SerializerMethodField()
    customer_account = serializers.CharField(source="customer.account_number", read_only=True)

    class Meta:
        model = Recommendation
        fields = [
            "id", "customer", "customer_account", "category", "priority",
            "title", "description", "estimated_saving_pence",
            "estimated_saving_pounds", "is_dismissed", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_estimated_saving_pounds(self, obj):
        return f"{obj.estimated_saving_pence / 100:.2f}"


class GenerateRecommendationsSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
