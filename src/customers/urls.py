from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomerViewSet, MeterViewSet, PropertyViewSet

router = DefaultRouter()
router.register("", CustomerViewSet, basename="customer")

# Nested routes for properties and meters
property_router = DefaultRouter()
property_router.register("", PropertyViewSet, basename="property")

meter_router = DefaultRouter()
meter_router.register("", MeterViewSet, basename="meter")

urlpatterns = [
    path(
        "<uuid:customer_pk>/properties/",
        include((property_router.urls, "properties")),
    ),
    path(
        "<uuid:customer_pk>/properties/<uuid:property_pk>/meters/",
        include((meter_router.urls, "meters")),
    ),
    path("", include(router.urls)),
]
