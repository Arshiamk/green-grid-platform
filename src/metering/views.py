from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MeterReading, UploadedFile
from .serializers import (
    FileUploadSerializer,
    MeterReadingSerializer,
    UploadedFileSerializer,
)
from .tasks import process_readings_upload


class MeterReadingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MeterReadingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = ["reading_at", "value_kwh"]
    ordering = ["-reading_at"]

    def get_queryset(self):
        user = self.request.user
        qs = MeterReading.objects.select_related("meter").all()
        if user.is_staff:
            return qs
        return qs.filter(meter__property__customer__user=user)


class ReadingsUploadView(APIView):
    """Upload a CSV of meter readings for async processing."""

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        csv_file = serializer.validated_data["file"]
        upload = UploadedFile.objects.create(
            file=csv_file,
            original_filename=csv_file.name,
        )

        # Dispatch to Celery
        process_readings_upload.delay(str(upload.pk))

        return Response(
            UploadedFileSerializer(upload).data,
            status=status.HTTP_202_ACCEPTED,
        )


class UploadStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """Check the status of a CSV upload."""

    queryset = UploadedFile.objects.all()
    serializer_class = UploadedFileSerializer
