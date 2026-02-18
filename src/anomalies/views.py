from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Anomaly
from .serializers import AnomalySerializer, DetectAnomaliesSerializer
from .services import detect_anomalies


class AnomalyViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AnomalySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Anomaly.objects.select_related("meter").all()
        if user.is_staff:
            return qs
        return qs.filter(meter__property__customer__user=user)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """Mark an anomaly as resolved."""
        anomaly = self.get_object()
        anomaly.is_resolved = True
        anomaly.save(update_fields=["is_resolved"])
        return Response(AnomalySerializer(anomaly).data)


class DetectAnomaliesView(APIView):
    """Run anomaly detection for a meter."""

    def post(self, request):
        serializer = DetectAnomaliesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            anomalies = detect_anomalies(
                meter_id=str(serializer.validated_data["meter_id"]),
                lookback_days=serializer.validated_data["lookback_days"],
            )
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            AnomalySerializer(anomalies, many=True).data,
            status=status.HTTP_201_CREATED,
        )
