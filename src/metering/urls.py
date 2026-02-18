from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MeterReadingViewSet, ReadingsUploadView, UploadStatusViewSet

router = DefaultRouter()
router.register("readings", MeterReadingViewSet, basename="reading")
router.register("uploads", UploadStatusViewSet, basename="upload")

urlpatterns = [
    path("upload/", ReadingsUploadView.as_view(), name="readings-upload"),
    path("", include(router.urls)),
]
