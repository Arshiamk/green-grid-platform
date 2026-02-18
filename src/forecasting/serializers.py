from rest_framework import serializers

from .models import DemandForecast, ForecastPoint


class ForecastPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForecastPoint
        fields = ["timestamp", "predicted_kwh", "lower_bound_kwh", "upper_bound_kwh"]


class DemandForecastSerializer(serializers.ModelSerializer):
    points = ForecastPointSerializer(many=True, read_only=True)
    meter_mpan = serializers.CharField(source="meter.mpan", read_only=True)

    class Meta:
        model = DemandForecast
        fields = [
            "id", "meter", "meter_mpan", "granularity",
            "forecast_start", "forecast_end", "lookback_days",
            "total_predicted_kwh", "created_at", "points",
        ]
        read_only_fields = ["id", "created_at"]


class DemandForecastListSerializer(serializers.ModelSerializer):
    meter_mpan = serializers.CharField(source="meter.mpan", read_only=True)

    class Meta:
        model = DemandForecast
        fields = [
            "id", "meter_mpan", "granularity",
            "forecast_start", "forecast_end",
            "total_predicted_kwh", "created_at",
        ]


class GenerateForecastSerializer(serializers.Serializer):
    meter_id = serializers.UUIDField()
    days_ahead = serializers.IntegerField(default=7, min_value=1, max_value=90)
    lookback_days = serializers.IntegerField(default=7, min_value=1, max_value=365)
    granularity = serializers.ChoiceField(
        choices=["half_hourly", "hourly", "daily"],
        default="half_hourly",
    )
