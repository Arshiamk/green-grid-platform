"""
Unit tests for the anomaly detection engine (anomalies.services).

Each detector — z-score spikes/drops, reading gaps, flatlines and negative
values — is exercised with synthetic reading series designed to trigger
exactly the branch under test.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from customers.models import Customer, Meter, Property
from metering.models import MeterReading

from .models import Anomaly
from .services import detect_anomalies


class AnomalyTestBase(TestCase):
    def setUp(self):
        customer = Customer.objects.create(
            account_number="ACC-3001",
            first_name="Alan",
            last_name="Turing",
            email="alan@example.com",
        )
        prop = Property.objects.create(
            customer=customer,
            address_line_1="3 Test Street",
            city="London",
            postcode="E1 6AN",
        )
        self.meter = Meter.objects.create(
            property=prop,
            mpan="1200000000003",
            serial_number="SN-0003",
            fuel_type="electricity",
            is_smart=True,
        )
        # Anchor the series well inside the default 7-day lookback window
        self.start = timezone.now() - timedelta(days=3)

    def seed_series(self, values, interval=timedelta(minutes=30), start=None):
        """Create readings spaced `interval` apart; None values skip a slot (gap)."""
        ts = start or self.start
        readings = []
        for value in values:
            if value is not None:
                readings.append(MeterReading(
                    meter=self.meter,
                    reading_at=ts,
                    value_kwh=Decimal(str(value)),
                ))
            ts += interval
        MeterReading.objects.bulk_create(readings)

    @staticmethod
    def wobble(n, low=0.9, high=1.1):
        """Alternating baseline that avoids accidental flatlines."""
        return [low if i % 2 == 0 else high for i in range(n)]


class SpikeAndDropTests(AnomalyTestBase):
    def test_extreme_spike_flagged_critical(self):
        # 50 normal readings around 1.0, one reading of 50 kWh (z-score > 5)
        self.seed_series(self.wobble(50) + [50.0])

        anomalies = detect_anomalies(str(self.meter.pk))

        spikes = [a for a in anomalies if a.anomaly_type == "spike"]
        self.assertEqual(len(spikes), 1)
        self.assertEqual(spikes[0].severity, "critical")
        self.assertEqual(spikes[0].value_kwh, Decimal("50"))
        # Expected value recorded as the series mean
        self.assertGreater(spikes[0].expected_kwh, Decimal("1"))
        self.assertLess(spikes[0].expected_kwh, Decimal("3"))

    def test_sudden_drop_flagged(self):
        # Baseline around 10 kWh with a single near-zero reading
        self.seed_series(self.wobble(50, low=9.5, high=10.5) + [0.5])

        anomalies = detect_anomalies(str(self.meter.pk))

        drops = [a for a in anomalies if a.anomaly_type == "drop"]
        self.assertEqual(len(drops), 1)
        self.assertEqual(drops[0].value_kwh, Decimal("0.5"))

    def test_normal_series_produces_no_anomalies(self):
        self.seed_series(self.wobble(48))

        anomalies = detect_anomalies(str(self.meter.pk))

        self.assertEqual(anomalies, [])
        self.assertEqual(Anomaly.objects.count(), 0)


class GapTests(AnomalyTestBase):
    def test_missing_readings_over_two_hours_flagged(self):
        # 20 readings, a 3-hour hole (6 skipped slots), then 20 more
        self.seed_series(self.wobble(20) + [None] * 6 + self.wobble(20))

        anomalies = detect_anomalies(str(self.meter.pk))

        gaps = [a for a in anomalies if a.anomaly_type == "gap"]
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].severity, "warning")  # < 6 hours
        self.assertIn("3.5 hours", gaps[0].title)

    def test_long_gap_flagged_critical(self):
        # 16 skipped slots -> 8.5 hour gap
        self.seed_series(self.wobble(20) + [None] * 16 + self.wobble(20))

        anomalies = detect_anomalies(str(self.meter.pk))

        gaps = [a for a in anomalies if a.anomaly_type == "gap"]
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].severity, "critical")

    def test_regular_half_hourly_series_has_no_gaps(self):
        self.seed_series(self.wobble(48))

        anomalies = detect_anomalies(str(self.meter.pk))
        self.assertEqual([a for a in anomalies if a.anomaly_type == "gap"], [])


class FlatlineTests(AnomalyTestBase):
    def test_identical_readings_over_four_hours_flagged(self):
        # 11 identical readings span 5 hours, then the series varies again
        self.seed_series([0.5] * 11 + self.wobble(20, low=0.45, high=0.55))

        anomalies = detect_anomalies(str(self.meter.pk))

        flatlines = [a for a in anomalies if a.anomaly_type == "flatline"]
        self.assertEqual(len(flatlines), 1)
        self.assertEqual(flatlines[0].severity, "info")
        self.assertEqual(flatlines[0].value_kwh, Decimal("0.5"))

    def test_short_repeat_is_not_a_flatline(self):
        # 5 identical readings span only 2 hours — below the 4-hour threshold
        self.seed_series([0.5] * 5 + self.wobble(20, low=0.45, high=0.55))

        anomalies = detect_anomalies(str(self.meter.pk))
        self.assertEqual([a for a in anomalies if a.anomaly_type == "flatline"], [])


class NegativeReadingTests(AnomalyTestBase):
    def test_negative_reading_flagged_critical(self):
        self.seed_series(self.wobble(50) + [-2.0])

        anomalies = detect_anomalies(str(self.meter.pk))

        negatives = [a for a in anomalies if a.anomaly_type == "negative"]
        self.assertEqual(len(negatives), 1)
        self.assertEqual(negatives[0].severity, "critical")
        self.assertEqual(negatives[0].value_kwh, Decimal("-2"))


class DetectionGuardsTests(AnomalyTestBase):
    def test_fewer_than_ten_readings_skips_detection(self):
        self.seed_series([1.0, 100.0, -5.0, 1.0, 1.0])  # would otherwise trigger

        anomalies = detect_anomalies(str(self.meter.pk))

        self.assertEqual(anomalies, [])
        self.assertEqual(Anomaly.objects.count(), 0)

    def test_detected_anomalies_are_persisted(self):
        self.seed_series(self.wobble(50) + [50.0])

        anomalies = detect_anomalies(str(self.meter.pk))

        self.assertGreater(len(anomalies), 0)
        self.assertEqual(Anomaly.objects.count(), len(anomalies))
        self.assertTrue(all(a.meter_id == self.meter.pk for a in anomalies))
