from rest_framework import serializers

from .models import CustomerTariff, RateBand, Tariff


class RateBandSerializer(serializers.ModelSerializer):
    class Meta:
        model = RateBand
        fields = ["id", "label", "start_time", "end_time", "rate_pence_per_kwh"]
        read_only_fields = ["id"]


class TariffSerializer(serializers.ModelSerializer):
    rate_bands = RateBandSerializer(many=True, read_only=True)

    class Meta:
        model = Tariff
        fields = [
            "id", "name", "code", "fuel_type", "tariff_type",
            "standing_charge_pence", "is_active",
            "valid_from", "valid_to", "rate_bands",
        ]
        read_only_fields = ["id"]


class TariffListSerializer(serializers.ModelSerializer):
    """Lighter serializer without nested rate bands."""

    class Meta:
        model = Tariff
        fields = [
            "id", "name", "code", "fuel_type", "tariff_type",
            "standing_charge_pence", "is_active",
            "valid_from", "valid_to",
        ]
        read_only_fields = ["id"]


class CustomerTariffSerializer(serializers.ModelSerializer):
    tariff_name = serializers.CharField(source="tariff.name", read_only=True)
    customer_account = serializers.CharField(source="customer.account_number", read_only=True)

    class Meta:
        model = CustomerTariff
        fields = [
            "id", "customer", "customer_account",
            "tariff", "tariff_name",
            "effective_from", "effective_to",
        ]
        read_only_fields = ["id"]
