from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BillViewSet, GenerateBillView
from .pdf_views import GenerateBillPDFView
from .payment_views import CreatePaymentIntentView

router = DefaultRouter()
router.register(r"bills", BillViewSet, basename="bill")

urlpatterns = [
    path("generate/", GenerateBillView.as_view(), name="generate-bill"),
    path("bills/<uuid:pk>/pdf/", GenerateBillPDFView.as_view(), name="bill-pdf"),
    path("payments/create-intent/<uuid:pk>/", CreatePaymentIntentView.as_view(), name="create-payment-intent"),
    path("", include(router.urls)),
]
