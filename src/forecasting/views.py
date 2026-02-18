from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DemandForecast
from .serializers import (
    DemandForecastListSerializer,
    DemandForecastSerializer,
    GenerateForecastSerializer,
)
from .services import generate_forecast


class DemandForecastViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = DemandForecast.objects.select_related("meter").prefetch_related("points").all()
        if user.is_staff:
            return qs
        return qs.filter(meter__property__customer__user=user)

    def get_serializer_class(self):
        if self.action == "list":
            return DemandForecastListSerializer
        return DemandForecastSerializer


class GenerateForecastView(APIView):
    """Synchronously generate a demand forecast for a meter."""

    def post(self, request):
        serializer = GenerateForecastSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            forecast = generate_forecast(
                meter_id=str(serializer.validated_data["meter_id"]),
                days_ahead=serializer.validated_data["days_ahead"],
                lookback_days=serializer.validated_data["lookback_days"],
                granularity=serializer.validated_data["granularity"],
            )
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            DemandForecastSerializer(forecast).data,
            status=status.HTTP_201_CREATED,
        )
