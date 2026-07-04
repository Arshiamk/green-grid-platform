"""
Unit tests for the billing calculation engine (billing.services).

Covers flat vs time-of-use tariffs, standing charges, rate-band matching
(including bands that wrap midnight), period filtering, and error paths.
"""

from datetime import date, datetime, time, timezone as dt_timezone
from decimal import Decimal

from django.test import TestCase

from customers.models import Customer, Meter, Property
from metering.models import MeterReading
from tariffs.models import CustomerTariff, RateBand, Tariff

from .models import Bill, BillLineItem
from .services import _match_rate_band, generate_bill


def utc(*args):
    """Shorthand for a UTC-aware datetime."""
    return datetime(*args, tzinfo=dt_timezone.utc)


class BillingTestBase(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            account_number="ACC-1001",
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
        )
        self.property = Property.objects.create(
            customer=self.customer,
            address_line_1="1 Test Street",
            city="London",
            postcode="E1 6AN",
        )
        self.meter = Meter.objects.create(
            property=self.property,
            mpan="1200000000001",
            serial_number="SN-0001",
            fuel_type="electricity",
            is_smart=True,
        )

    def add_reading(self, dt, kwh):
        return MeterReading.objects.create(
            meter=self.meter,
            reading_at=dt,
            value_kwh=Decimal(str(kwh)),
        )

    def make_flat_tariff(self, rate="28.0000", standing="50.0000"):
        tariff = Tariff.objects.create(
            name="Standard Fixed",
            code="FLAT-1",
            fuel_type="electricity",
            tariff_type="fixed",
            standing_charge_pence=Decimal(standing),
            valid_from=date(2025, 1, 1),
        )
        RateBand.objects.create(
            tariff=tariff,
            label="Standard",
            rate_pence_per_kwh=Decimal(rate),
        )
        return tariff

    def assign(self, tariff, effective_from=date(2025, 1, 1), effective_to=None):
        return CustomerTariff.objects.create(
            customer=self.customer,
            tariff=tariff,
            effective_from=effective_from,
            effective_to=effective_to,
        )


class FlatTariffBillTests(BillingTestBase):
    def test_flat_tariff_usage_and_standing_charge(self):
        tariff = self.make_flat_tariff(rate="28.0000", standing="50.0000")
        self.assign(tariff)

        # 10 readings x 2.5 kWh = 25 kWh inside the billing period
        for day in range(1, 11):
            self.add_reading(utc(2025, 3, day, 9, 0), "2.5")

        bill = generate_bill(str(self.customer.pk), date(2025, 3, 1), date(2025, 3, 31))

        self.assertEqual(bill.total_kwh, Decimal("25"))
        # 30 days x 50p standing charge
        self.assertEqual(bill.standing_charge_pence, Decimal("1500.00"))
        # 25 kWh x 28p
        self.assertEqual(bill.usage_charge_pence, Decimal("700.00"))
        self.assertEqual(bill.total_amount_pence, Decimal("2200.00"))
        self.assertEqual(bill.line_items.count(), 2)  # usage + standing charge

    def test_readings_outside_period_are_excluded(self):
        tariff = self.make_flat_tariff(rate="10.0000", standing="0.0000")
        self.assign(tariff)

        self.add_reading(utc(2025, 2, 28, 12, 0), "99")   # before period
        self.add_reading(utc(2025, 3, 15, 12, 0), "4")    # inside period
        self.add_reading(utc(2025, 4, 1, 0, 30), "99")    # after period

        bill = generate_bill(str(self.customer.pk), date(2025, 3, 1), date(2025, 3, 31))

        self.assertEqual(bill.total_kwh, Decimal("4"))
        self.assertEqual(bill.usage_charge_pence, Decimal("40.00"))

    def test_standing_charge_minimum_one_day(self):
        tariff = self.make_flat_tariff(rate="10.0000", standing="60.0000")
        self.assign(tariff)
        self.add_reading(utc(2025, 3, 1, 9, 0), "1")

        # Same-day period still bills one day of standing charge
        bill = generate_bill(str(self.customer.pk), date(2025, 3, 1), date(2025, 3, 1))
        self.assertEqual(bill.standing_charge_pence, Decimal("60.00"))

    def test_expired_assignment_covering_period_is_used(self):
        tariff = self.make_flat_tariff(rate="20.0000", standing="0.0000")
        # Assignment has an end date, but it covers the billing period
        self.assign(tariff, effective_from=date(2025, 1, 1), effective_to=date(2025, 4, 30))
        self.add_reading(utc(2025, 3, 10, 9, 0), "3")

        bill = generate_bill(str(self.customer.pk), date(2025, 3, 1), date(2025, 3, 31))
        self.assertEqual(bill.usage_charge_pence, Decimal("60.00"))


class TimeOfUseBillTests(BillingTestBase):
    def setUp(self):
        super().setUp()
        self.tariff = Tariff.objects.create(
            name="Economy Saver",
            code="TOU-1",
            fuel_type="electricity",
            tariff_type="time_of_use",
            standing_charge_pence=Decimal("60.0000"),
            valid_from=date(2025, 1, 1),
        )
        self.day_band = RateBand.objects.create(
            tariff=self.tariff,
            label="Day",
            start_time=time(7, 0),
            end_time=time(22, 0),
            rate_pence_per_kwh=Decimal("30.0000"),
        )
        self.night_band = RateBand.objects.create(
            tariff=self.tariff,
            label="Night",
            start_time=time(22, 0),
            end_time=time(7, 0),  # wraps midnight
            rate_pence_per_kwh=Decimal("12.0000"),
        )
        self.assign(self.tariff)

    def test_usage_split_across_day_and_night_bands(self):
        # Day readings: 3 x 2 kWh = 6 kWh
        self.add_reading(utc(2025, 3, 3, 8, 0), "2")
        self.add_reading(utc(2025, 3, 3, 12, 0), "2")
        self.add_reading(utc(2025, 3, 4, 21, 59), "2")
        # Night readings: 2 x 1.5 kWh = 3 kWh (one after 22:00, one overnight)
        self.add_reading(utc(2025, 3, 3, 23, 0), "1.5")
        self.add_reading(utc(2025, 3, 4, 3, 0), "1.5")

        bill = generate_bill(str(self.customer.pk), date(2025, 3, 1), date(2025, 3, 31))

        day_item = bill.line_items.get(rate_band_label="Day")
        night_item = bill.line_items.get(rate_band_label="Night")

        self.assertEqual(day_item.kwh, Decimal("6"))
        self.assertEqual(day_item.amount_pence, Decimal("180.00"))  # 6 x 30p
        self.assertEqual(night_item.kwh, Decimal("3"))
        self.assertEqual(night_item.amount_pence, Decimal("36.00"))  # 3 x 12p

        self.assertEqual(bill.total_kwh, Decimal("9"))
        self.assertEqual(bill.usage_charge_pence, Decimal("216.00"))
        self.assertEqual(bill.standing_charge_pence, Decimal("1800.00"))  # 30 days x 60p
        self.assertEqual(bill.total_amount_pence, Decimal("2016.00"))

    def test_band_with_no_usage_produces_no_line_item(self):
        self.add_reading(utc(2025, 3, 3, 8, 0), "2")  # day only

        bill = generate_bill(str(self.customer.pk), date(2025, 3, 1), date(2025, 3, 31))

        labels = list(bill.line_items.values_list("rate_band_label", flat=True))
        self.assertIn("Day", labels)
        self.assertNotIn("Night", labels)


class RateBandMatchingTests(TestCase):
    """Pure-logic tests for _match_rate_band, including midnight wrap-around."""

    def setUp(self):
        self.day = RateBand(
            label="Day", start_time=time(7, 0), end_time=time(22, 0),
            rate_pence_per_kwh=Decimal("30"),
        )
        self.night = RateBand(
            label="Night", start_time=time(22, 0), end_time=time(7, 0),
            rate_pence_per_kwh=Decimal("12"),
        )
        self.bands = [self.day, self.night]

    def test_daytime_matches_day_band(self):
        self.assertIs(_match_rate_band(time(7, 0), self.bands), self.day)
        self.assertIs(_match_rate_band(time(12, 30), self.bands), self.day)
        self.assertIs(_match_rate_band(time(21, 59), self.bands), self.day)

    def test_overnight_wraps_midnight(self):
        self.assertIs(_match_rate_band(time(22, 0), self.bands), self.night)
        self.assertIs(_match_rate_band(time(23, 30), self.bands), self.night)
        self.assertIs(_match_rate_band(time(0, 0), self.bands), self.night)
        self.assertIs(_match_rate_band(time(6, 59), self.bands), self.night)

    def test_null_start_time_acts_as_flat_fallback(self):
        flat = RateBand(label="Flat", rate_pence_per_kwh=Decimal("25"))
        self.assertIs(_match_rate_band(time(15, 0), [flat]), flat)

    def test_empty_band_list_returns_none(self):
        self.assertIsNone(_match_rate_band(time(15, 0), []))


class BillingErrorTests(BillingTestBase):
    def test_no_tariff_assignment_raises(self):
        with self.assertRaises(ValueError):
            generate_bill(str(self.customer.pk), date(2025, 3, 1), date(2025, 3, 31))
        self.assertEqual(Bill.objects.count(), 0)
        self.assertEqual(BillLineItem.objects.count(), 0)

    def test_tariff_without_rate_bands_raises(self):
        tariff = Tariff.objects.create(
            name="Broken",
            code="BROKEN-1",
            fuel_type="electricity",
            tariff_type="fixed",
            standing_charge_pence=Decimal("10.0000"),
            valid_from=date(2025, 1, 1),
        )
        self.assign(tariff)
        with self.assertRaises(ValueError):
            generate_bill(str(self.customer.pk), date(2025, 3, 1), date(2025, 3, 31))
