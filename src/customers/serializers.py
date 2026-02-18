from rest_framework import serializers

from .models import Customer, Meter, Property


class MeterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meter
        fields = [
            "id", "mpan", "serial_number", "fuel_type",
            "is_smart", "installed_on",
        ]
        read_only_fields = ["id"]


class PropertySerializer(serializers.ModelSerializer):
    meters = MeterSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = [
            "id", "address_line_1", "address_line_2",
            "city", "postcode", "property_type", "meters",
        ]
        read_only_fields = ["id"]


class CustomerSerializer(serializers.ModelSerializer):
    properties = PropertySerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id", "account_number", "first_name", "last_name",
            "email", "phone", "created_at", "properties",
        ]
        read_only_fields = ["id", "created_at"]


class CustomerListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views (no nested properties)."""

    class Meta:
        model = Customer
        fields = [
            "id", "account_number", "first_name", "last_name",
            "email", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
