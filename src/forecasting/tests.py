"""
Unit tests for the demand forecasting engine (forecasting.services).

Uses synthetic half-hourly readings so the weighted-moving-average maths,
day-of-week seasonality, and confidence intervals are fully deterministic.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from customers.models import Customer, Meter, Property
from metering.models import MeterReading

from .models import ForecastPoint
from .services import generate_forecast


def hour_floor(dt):
    return dt.replace(minute=0, second=0, microsecond=0)


class ForecastTestBase(TestCase):
    def setUp(self):
        customer = Customer.objects.create(
            account_number="ACC-2001",
            first_name="Grace",
            last_name="Hopper",
            email="grace@example.com",
        )
        prop = Property.objects.create(
            customer=customer,
            address_line_1="2 Test Street",
            city="London",
            postcode="E1 6AN",
        )
        self.meter = Meter.objects.create(
            property=prop,
            mpan="1200000000002",
            serial_number="SN-0002",
            fuel_type="electricity",
            is_smart=True,
        )
        # Mirror the anchor used inside generate_forecast()
        self.now = hour_floor(timezone.now())

    def seed_half_hourly(self, days, value_fn):
        """Create one reading per half-hour slot for the past `days` days.

        value_fn(reading_datetime) -> float kWh value for that slot.
        """
        start = self.now - timedelta(days=days)
        readings = []
        for i in range(days * 48):
            ts = start + timedelta(minutes=30 * i)
            readings.append(MeterReading(
                meter=self.meter,
                reading_at=ts,
                value_kwh=Decimal(str(value_fn(ts))),
            ))
        MeterReading.objects.bulk_create(readings)


class GenerateForecastTests(ForecastTestBase):
    def test_constant_history_gives_constant_prediction(self):
        self.seed_half_hourly(7, lambda ts: 1.0)

        forecast = generate_forecast(
            str(self.meter.pk), days_ahead=1, lookback_days=7, granularity="hourly",
        )

        points = list(forecast.points.order_by("timestamp"))
        self.assertEqual(len(points), 24)
        for pt in points:
            # Weighted average of a constant series is the constant itself
            self.assertEqual(pt.predicted_kwh, Decimal("1"))
            # Zero variance -> the 20% floor drives the confidence interval
            self.assertEqual(pt.lower_bound_kwh, Decimal("0.8"))
            self.assertEqual(pt.upper_bound_kwh, Decimal("1.2"))
        self.assertEqual(forecast.total_predicted_kwh, Decimal("24"))

    def test_day_of_week_seasonality_is_preserved(self):
        # Weekends consume twice as much as weekdays
        self.seed_half_hourly(
            7, lambda ts: 2.0 if ts.weekday() >= 5 else 1.0,
        )

        forecast = generate_forecast(
            str(self.meter.pk), days_ahead=7, lookback_days=7, granularity="daily",
        )

        points = list(forecast.points.order_by("timestamp"))
        self.assertEqual(len(points), 7)
        for pt in points:
            expected = Decimal("96") if pt.timestamp.weekday() >= 5 else Decimal("48")
            self.assertEqual(pt.predicted_kwh, expected)

    def test_confidence_bounds_bracket_prediction(self):
        # Varied profile: consumption depends on hour of day
        self.seed_half_hourly(7, lambda ts: 0.2 + ts.hour * 0.1)

        forecast = generate_forecast(
            str(self.meter.pk), days_ahead=2, lookback_days=7, granularity="half_hourly",
        )

        points = list(forecast.points.all())
        self.assertEqual(len(points), 2 * 48)
        for pt in points:
            self.assertLessEqual(pt.lower_bound_kwh, pt.predicted_kwh)
            self.assertGreaterEqual(pt.upper_bound_kwh, pt.predicted_kwh)
            self.assertGreaterEqual(pt.lower_bound_kwh, Decimal("0"))

    def test_forecast_metadata_persisted(self):
        self.seed_half_hourly(3, lambda ts: 0.5)

        forecast = generate_forecast(
            str(self.meter.pk), days_ahead=1, lookback_days=3, granularity="hourly",
        )

        self.assertEqual(forecast.meter_id, self.meter.pk)
        self.assertEqual(forecast.granularity, "hourly")
        self.assertEqual(forecast.lookback_days, 3)
        self.assertEqual(
            forecast.forecast_end - forecast.forecast_start, timedelta(days=1),
        )
        self.assertEqual(
            ForecastPoint.objects.filter(forecast=forecast).count(), 24,
        )

    def test_no_readings_raises(self):
        with self.assertRaises(ValueError):
            generate_forecast(str(self.meter.pk), days_ahead=1, lookback_days=7)
