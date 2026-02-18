from django.contrib import admin
from django.urls import include, path

from core.views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("api/customers/", include("customers.urls")),
    path("api/metering/", include("metering.urls")),
    path("api/tariffs/", include("tariffs.urls")),
    path("api/billing/", include("billing.urls")),
    path("api/forecasting/", include("forecasting.urls")),
    path("api/recommendations/", include("recommendations.urls")),
    path("api/anomalies/", include("anomalies.urls")),
    path("api/", include("core.urls")),
]
