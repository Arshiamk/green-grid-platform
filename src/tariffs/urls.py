from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomerTariffViewSet, TariffViewSet

router = DefaultRouter()
router.register("plans", TariffViewSet, basename="tariff")
router.register("assignments", CustomerTariffViewSet, basename="customer-tariff")

urlpatterns = [
    path("", include(router.urls)),
]
