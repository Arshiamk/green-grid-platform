from rest_framework import viewsets

from .models import Customer, Meter, Property
from .serializers import (
    CustomerListSerializer,
    CustomerSerializer,
    MeterSerializer,
    PropertySerializer,
)


from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from core.permissions import IsCustomerOwner

from .models import Customer, Meter, Property
from .serializers import (
    CustomerListSerializer,
    CustomerSerializer,
    MeterSerializer,
    PropertySerializer,
)


class CustomerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsCustomerOwner]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Customer.objects.prefetch_related("properties__meters").all()
        return Customer.objects.filter(user=user).prefetch_related("properties__meters")
    
    def get_serializer_class(self):
        if self.action == "list":
            return CustomerListSerializer
        return CustomerSerializer


class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated, IsCustomerOwner]

    def get_queryset(self):
        user = self.request.user
        qs = Property.objects.filter(customer_id=self.kwargs["customer_pk"]).prefetch_related("meters")
        if user.is_staff:
            return qs
        return qs.filter(customer__user=user)

    def perform_create(self, serializer):
        # Ensure user can only create for their own customer (enforced by permission but good to check)
        serializer.save(customer_id=self.kwargs["customer_pk"])


class MeterViewSet(viewsets.ModelViewSet):
    serializer_class = MeterSerializer
    permission_classes = [IsAuthenticated, IsCustomerOwner]

    def get_queryset(self):
        user = self.request.user
        qs = Meter.objects.filter(
            property__customer_id=self.kwargs["customer_pk"],
            property_id=self.kwargs["property_pk"],
        )
        if user.is_staff:
            return qs
        return qs.filter(property__customer__user=user)

    def perform_create(self, serializer):
        serializer.save(property_id=self.kwargs["property_pk"])
