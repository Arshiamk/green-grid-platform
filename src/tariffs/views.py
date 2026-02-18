from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import CustomerTariff, Tariff
from .serializers import (
    CustomerTariffSerializer,
    TariffListSerializer,
    TariffSerializer,
)


class TariffViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tariff.objects.prefetch_related("rate_bands").all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == "list":
            return TariffListSerializer
        return TariffSerializer


class CustomerTariffViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CustomerTariffSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = CustomerTariff.objects.select_related("customer", "tariff").all()
        if user.is_staff:
            return qs
        return qs.filter(customer__user=user)
