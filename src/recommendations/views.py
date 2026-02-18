from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Recommendation
from .serializers import (
    GenerateRecommendationsSerializer,
    RecommendationSerializer,
)
from .services import generate_recommendations


class RecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Recommendation.objects.select_related("customer").all()
        if user.is_staff:
            return qs
        return qs.filter(customer__user=user)

    @action(detail=True, methods=["post"])
    def dismiss(self, request, pk=None):
        """Dismiss a recommendation."""
        rec = self.get_object()
        rec.is_dismissed = True
        rec.save(update_fields=["is_dismissed"])
        return Response(RecommendationSerializer(rec).data)


class GenerateRecommendationsView(APIView):
    """Generate recommendations for a customer."""

    def post(self, request):
        serializer = GenerateRecommendationsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            recs = generate_recommendations(
                customer_id=str(serializer.validated_data["customer_id"]),
            )
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            RecommendationSerializer(recs, many=True).data,
            status=status.HTTP_201_CREATED,
        )
