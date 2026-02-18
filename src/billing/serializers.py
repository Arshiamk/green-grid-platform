from rest_framework import serializers

from .models import Bill, BillLineItem


class BillLineItemSerializer(serializers.ModelSerializer):
    amount_pounds = serializers.SerializerMethodField()

    class Meta:
        model = BillLineItem
        fields = [
            "id", "description", "rate_band_label",
            "kwh", "rate_pence_per_kwh", "amount_pence", "amount_pounds",
        ]

    def get_amount_pounds(self, obj):
        return f"{obj.amount_pence / 100:.2f}"


class BillSerializer(serializers.ModelSerializer):
    line_items = BillLineItemSerializer(many=True, read_only=True)
    customer_account = serializers.CharField(source="customer.account_number", read_only=True)
    total_pounds = serializers.SerializerMethodField()

    class Meta:
        model = Bill
        fields = [
            "id", "customer", "customer_account",
            "period_start", "period_end", "status",
            "total_kwh", "standing_charge_pence", "usage_charge_pence",
            "total_amount_pence", "total_pounds",
            "issued_at", "created_at", "line_items",
        ]
        read_only_fields = ["id", "created_at"]

    def get_total_pounds(self, obj):
        return f"{obj.total_amount_pence / 100:.2f}"


class BillListSerializer(serializers.ModelSerializer):
    customer_account = serializers.CharField(source="customer.account_number", read_only=True)
    total_pounds = serializers.SerializerMethodField()

    class Meta:
        model = Bill
        fields = [
            "id", "customer_account", "period_start", "period_end",
            "status", "total_kwh", "total_amount_pence", "total_pounds",
            "created_at",
        ]

    def get_total_pounds(self, obj):
        return f"{obj.total_amount_pence / 100:.2f}"


class GenerateBillSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()
