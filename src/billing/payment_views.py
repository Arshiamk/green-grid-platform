import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Bill, Payment

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreatePaymentIntentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        try:
            bill = Bill.objects.get(pk=pk)
            # Check ownership
            if not request.user.is_staff and bill.customer.user != request.user:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            
            if bill.status == "PAID":
                return Response({"detail": "Bill already paid."}, status=status.HTTP_400_BAD_REQUEST)

        except Bill.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Create Stripe PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=int(bill.total_amount_pence),  # Amount in pence/cents
                currency="gbp",
                metadata={"bill_id": str(bill.id)},
                automatic_payment_methods={"enabled": True},
            )

            # Record local payment attempt
            Payment.objects.create(
                bill=bill,
                amount=bill.total_amount_pence / 100,
                stripe_payment_intent_id=intent.id,
                status="PENDING"
            )

            return Response({
                "clientSecret": intent.client_secret
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
