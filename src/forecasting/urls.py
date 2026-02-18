from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DemandForecastViewSet, GenerateForecastView

router = DefaultRouter()
router.register("", DemandForecastViewSet, basename="forecast")

urlpatterns = [
    path("generate/", GenerateForecastView.as_view(), name="generate-forecast"),
    path("", include(router.urls)),
]
