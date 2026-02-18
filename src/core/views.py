from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer


class HealthCheckView(APIView):
    """
    Health check endpoint for Green Grid Platform.
    Returns 200 with {"status": "ok"} when the database and Redis are reachable,
    or 503 with error details otherwise.
    """
    permission_classes = [AllowAny]  # Health check should be public

    def get(self, request):
        from django.db import connection
        from redis import Redis
        import logging
        import os

        logger = logging.getLogger(__name__)
        status_data = {"status": "ok", "service": "green-grid-platform"}
        
        # Check DB
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return Response(
                {"status": "error", "detail": "Database unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Check Redis
        try:
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/1")
            r = Redis.from_url(redis_url)
            r.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            # We might treat Redis as non-critical for some apps, but critical here
            return Response(
                {"status": "error", "detail": "Redis unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(status_data)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
