from rest_framework import serializers

from .models import Anomaly


class AnomalySerializer(serializers.ModelSerializer):
    meter_mpan = serializers.CharField(source="meter.mpan", read_only=True)

    class Meta:
        model = Anomaly
        fields = [
            "id", "meter", "meter_mpan", "anomaly_type", "severity",
            "title", "description", "detected_at",
            "value_kwh", "expected_kwh", "is_resolved", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class DetectAnomaliesSerializer(serializers.Serializer):
    meter_id = serializers.UUIDField()
    lookback_days = serializers.IntegerField(default=7, min_value=1, max_value=90)
