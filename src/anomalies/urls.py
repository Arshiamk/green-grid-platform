from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AnomalyViewSet, DetectAnomaliesView

router = DefaultRouter()
router.register("", AnomalyViewSet, basename="anomaly")

urlpatterns = [
    path("detect/", DetectAnomaliesView.as_view(), name="detect-anomalies"),
    path("", include(router.urls)),
]
