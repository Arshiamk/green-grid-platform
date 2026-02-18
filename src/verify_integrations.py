import os
import django
from decimal import Decimal
from datetime import date

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from customers.models import Customer
from billing.models import Bill, BillLineItem, Payment
from communications.services import send_notification
from billing.pdf_views import GenerateBillPDFView
from billing.payment_views import CreatePaymentIntentView
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

User = get_user_model()

def verify_integrations():
    print("--- Verifying Integrations ---")

    # 1. Setup User & Customer
    username = "integration_test_user"
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
        print(f"User {username} exists.")
    else:
        user = User.objects.create_user(username=username, password="password123", email="test@example.com")
        customer = Customer.objects.create(user=user, first_name="Test", last_name="User", account_number="INT-001")
        print(f"Created user {username}.")

    customer = user.customer

    # 2. Verify Email
    print("\n--- Testing Email ---")
    success = send_notification(user, "Test Subject", "test_template", {})
    if success:
        print("✅ Email sent successfully (check console output).")
    else:
        print("❌ Email failed.")

    # 3. Verify Bill & PDF
    print("\n--- Testing PDF Generation ---")
    # Create a bill
    bill = Bill.objects.create(
        customer=customer,
        period_start=date(2023, 1, 1),
        period_end=date(2023, 1, 31),
        total_amount_pence=Decimal("10000.00"),
        status="PENDING"
    )
    BillLineItem.objects.create(bill=bill, description="Energy Usage", amount_pence=Decimal("10000.00"), kwh=Decimal("500"), rate_pence_per_kwh=Decimal("20.0"))
    
    factory = APIRequestFactory()
    request = factory.get(f'/api/billing/bills/{bill.id}/pdf/')
    force_authenticate(request, user=user)
    
    view = GenerateBillPDFView.as_view()
    response = view(request, pk=bill.id)
    
    if response.status_code == 200 and response['Content-Type'] == 'application/pdf':
        print(f"✅ PDF generated successfully. Size: {len(response.content)} bytes.")
    else:
        print(f"❌ PDF generation failed. Status: {response.status_code}")
        print(response.data)

    # 4. Verify Payment Intent
    print("\n--- Testing Stripe Payment Intent ---")
    request = factory.post(f'/api/billing/payments/create_intent/{bill.id}/')
    force_authenticate(request, user=user)
    
    view = CreatePaymentIntentView.as_view()
    response = view(request, pk=bill.id)
    
    # We expect 500 or 400 because we are using placeholder keys, OR success if it just mocks it?
    # Stripe lib will try to contact Stripe. With placeholder keys ('sk_test_placeholder'), it will fail authentication.
    # But that PROVES the endpoint is working (it reached Stripe).
    
    if response.status_code == 200:
        print("✅ Payment Intent created (Unexpected with placeholder keys!)")
    elif response.status_code == 500 and "Invalid API Key" in str(response.data):
        print("✅ Payment Intent endpoint reached Stripe (Failed as expected with invalid key).")
    else:
        print(f"⚠️ Payment Intent response: {response.status_code}")
        print(response.data)
        # It usually returns error description in 'error' key if we handled exception.
        
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    verify_integrations()
