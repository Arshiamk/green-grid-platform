"""
Seed the database with a realistic demo dataset.

Creates a demo login, customer, property and smart meter, five weeks of
half-hourly readings with a believable daily/weekly usage profile, a
time-of-use tariff, a generated bill, an anomaly scan and a demand forecast —
so a fresh clone shows a working dashboard instead of empty screens.

Usage:
    python manage.py seed_demo

The command is idempotent: re-running it resets the demo account's data.
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from anomalies.models import Anomaly
from anomalies.services import detect_anomalies
from billing.models import Bill
from billing.services import generate_bill
from customers.models import Customer, Meter, Property
from forecasting.models import DemandForecast
from forecasting.services import generate_forecast
from metering.models import MeterReading
from tariffs.models import CustomerTariff, RateBand, Tariff

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "greengrid-demo"
DEMO_ACCOUNT = "GG-DEMO-001"
DEMO_MPAN = "1200051234567"
SEED_DAYS = 35


class Command(BaseCommand):
    help = "Seed a demo customer, meter readings, tariff, bill, anomalies and forecast."

    @transaction.atomic
    def handle(self, *args, **options):
        user = self._create_user()
        customer, meter = self._create_customer(user)
        tariff = self._create_tariff(customer)
        readings = self._create_readings(meter)
        bill = self._create_bill(customer)
        anomalies = self._run_anomaly_scan(meter)
        forecast = self._create_forecast(meter)

        self.stdout.write(self.style.SUCCESS("Demo data seeded:"))
        self.stdout.write(
            f"  Customer   : {customer.account_number} "
            f"({customer.first_name} {customer.last_name})"
        )
        self.stdout.write(f"  Meter      : {meter.mpan}")
        self.stdout.write(f"  Tariff     : {tariff.name} ({tariff.rate_bands.count()} rate bands)")
        self.stdout.write(f"  Readings   : {readings} half-hourly readings over {SEED_DAYS} days")
        self.stdout.write(
            f"  Bill       : GBP {bill.total_pounds:.2f} "
            f"for {bill.period_start} to {bill.period_end}"
        )
        self.stdout.write(f"  Anomalies  : {anomalies} detected")
        self.stdout.write(f"  Forecast   : {forecast.points.count()} hourly points over 7 days")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Log in with  username: {DEMO_USERNAME}  password: {DEMO_PASSWORD}"
        ))

    # ------------------------------------------------------------------
    def _create_user(self):
        user, created = User.objects.get_or_create(
            username=DEMO_USERNAME,
            defaults={"email": "demo@example.com", "first_name": "Jamie", "last_name": "Watts"},
        )
        user.set_password(DEMO_PASSWORD)
        user.save()
        return user

    def _create_customer(self, user):
        customer, _ = Customer.objects.update_or_create(
            account_number=DEMO_ACCOUNT,
            defaults={
                "user": user,
                "first_name": "Jamie",
                "last_name": "Watts",
                "email": "demo@example.com",
                "phone": "0117 496 0000",
            },
        )
        prop, _ = Property.objects.get_or_create(
            customer=customer,
            address_line_1="42 Orchard Lane",
            defaults={"city": "Bristol", "postcode": "BS1 4DJ", "property_type": "house"},
        )
        meter, _ = Meter.objects.update_or_create(
            mpan=DEMO_MPAN,
            defaults={
                "property": prop,
                "serial_number": "ELS-2024-0042",
                "fuel_type": "electricity",
                "is_smart": True,
                "installed_on": timezone.now().date() - timedelta(days=400),
            },
        )
        return customer, meter

    def _create_tariff(self, customer):
        tariff, _ = Tariff.objects.update_or_create(
            code="GG-SAVER-24",
            defaults={
                "name": "GreenGrid Saver",
                "fuel_type": "electricity",
                "tariff_type": "time_of_use",
                "standing_charge_pence": Decimal("55.2000"),
                "is_active": True,
                "valid_from": timezone.now().date() - timedelta(days=365),
            },
        )
        tariff.rate_bands.all().delete()
        RateBand.objects.create(
            tariff=tariff, label="Day",
            start_time="07:00", end_time="23:00",
            rate_pence_per_kwh=Decimal("28.4000"),
        )
        RateBand.objects.create(
            tariff=tariff, label="Night",
            start_time="23:00", end_time="07:00",
            rate_pence_per_kwh=Decimal("13.1000"),
        )
        CustomerTariff.objects.get_or_create(
            customer=customer,
            tariff=tariff,
            defaults={"effective_from": timezone.now().date() - timedelta(days=365)},
        )
        return tariff

    def _create_readings(self, meter):
        """Five weeks of half-hourly readings with a plausible usage profile."""
        MeterReading.objects.filter(meter=meter).delete()

        rng = random.Random(42)  # deterministic between runs
        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        start = now - timedelta(days=SEED_DAYS)

        gap_start = now - timedelta(days=3, hours=14)   # 4-hour comms outage
        gap_end = gap_start + timedelta(hours=4)
        spike_at = now - timedelta(days=2, hours=9)     # one anomalous reading

        readings = []
        ts = start
        while ts < now:
            if gap_start <= ts < gap_end:
                ts += timedelta(minutes=30)
                continue

            hour = ts.hour
            if 0 <= hour < 6:
                base = 0.12            # overnight base load
            elif 6 <= hour < 9:
                base = 0.55            # morning peak
            elif 9 <= hour < 17:
                base = 0.30            # daytime
            elif 17 <= hour < 22:
                base = 0.85            # evening peak
            else:
                base = 0.25            # late evening

            if ts.weekday() >= 5:
                base *= 1.3            # weekend uplift

            value = base + rng.uniform(-0.05, 0.08)
            if ts == spike_at:
                value = 7.5            # anomalous spike

            readings.append(MeterReading(
                meter=meter,
                reading_at=ts,
                value_kwh=Decimal(str(round(max(value, 0.01), 4))),
            ))
            ts += timedelta(minutes=30)

        MeterReading.objects.bulk_create(readings, batch_size=500)
        return len(readings)

    def _create_bill(self, customer):
        Bill.objects.filter(customer=customer).delete()
        today = timezone.now().date()
        bill = generate_bill(
            customer_id=str(customer.pk),
            period_start=today - timedelta(days=30),
            period_end=today - timedelta(days=1),
        )
        bill.status = "issued"
        bill.issued_at = timezone.now()
        bill.save(update_fields=["status", "issued_at"])
        return bill

    def _run_anomaly_scan(self, meter):
        Anomaly.objects.filter(meter=meter).delete()
        return len(detect_anomalies(str(meter.pk), lookback_days=7))

    def _create_forecast(self, meter):
        DemandForecast.objects.filter(meter=meter).delete()
        return generate_forecast(
            meter_id=str(meter.pk),
            days_ahead=7,
            lookback_days=7,
            granularity="hourly",
        )
