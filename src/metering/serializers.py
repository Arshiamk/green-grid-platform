from rest_framework import serializers

from .models import MeterReading, UploadedFile


class MeterReadingSerializer(serializers.ModelSerializer):
    meter_mpan = serializers.CharField(source="meter.mpan", read_only=True)

    class Meta:
        model = MeterReading
        fields = [
            "id", "meter", "meter_mpan", "reading_at",
            "value_kwh", "reading_type", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = [
            "id", "original_filename", "status",
            "rows_total", "rows_ok", "rows_failed",
            "error_log", "created_at", "completed_at",
        ]
        read_only_fields = fields


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
