from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Bill
from .serializers import (
    BillListSerializer,
    BillSerializer,
    GenerateBillSerializer,
)
from .services import generate_bill


class BillViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Bill.objects.select_related("customer").prefetch_related("line_items").all()
        if user.is_staff:
            return qs
        return qs.filter(customer__user=user)

    def get_serializer_class(self):
        if self.action == "list":
            return BillListSerializer
        return BillSerializer


class GenerateBillView(APIView):
    """Synchronously generate a bill for a customer + period."""

    def post(self, request):
        serializer = GenerateBillSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            bill = generate_bill(
                customer_id=str(serializer.validated_data["customer_id"]),
                period_start=serializer.validated_data["period_start"],
                period_end=serializer.validated_data["period_end"],
            )
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            BillSerializer(bill).data,
            status=status.HTTP_201_CREATED,
        )
