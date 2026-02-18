"""
Anomaly detection engine.

Detects unusual patterns in meter readings using statistical methods:
- Spikes/drops: readings > 3 standard deviations from the mean
- Gaps: missing readings for > 2 hours
- Flatlines: identical readings for > 4 hours
"""

import logging
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from customers.models import Meter
from metering.models import MeterReading

from .models import Anomaly

logger = logging.getLogger(__name__)


def detect_anomalies(
    meter_id: str,
    lookback_days: int = 7,
    spike_threshold: float = 3.0,
) -> list[Anomaly]:
    """
    Scan a meter's recent readings for anomalies.

    Returns a list of newly created Anomaly records.
    """
    meter = Meter.objects.get(pk=meter_id)
    now = timezone.now()
    since = now - timedelta(days=lookback_days)

    readings = list(
        MeterReading.objects.filter(
            meter=meter,
            reading_at__gte=since,
        ).order_by("reading_at")
    )

    if len(readings) < 10:
        return []

    anomalies = []

    # ── Stats ────────────────────────────────────────────────────────────
    values = [float(r.value_kwh) for r in readings]
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std_dev = variance ** 0.5

    if std_dev == 0:
        std_dev = 0.01  # avoid division by zero

    # ── 1. Spikes and Drops ──────────────────────────────────────────────
    for reading in readings:
        val = float(reading.value_kwh)
        z_score = abs(val - mean) / std_dev

        if z_score > spike_threshold:
            anomaly_type = "spike" if val > mean else "drop"
            severity = "critical" if z_score > 5.0 else "warning"

            anomalies.append(Anomaly(
                meter=meter,
                anomaly_type=anomaly_type,
                severity=severity,
                title=f"Usage {'spike' if val > mean else 'drop'} detected",
                description=(
                    f"Reading of {reading.value_kwh} kWh at {reading.reading_at:%Y-%m-%d %H:%M} "
                    f"is {z_score:.1f} standard deviations from the mean ({mean:.2f} kWh). "
                    f"This may indicate a faulty meter or unusual consumption."
                ),
                detected_at=reading.reading_at,
                value_kwh=reading.value_kwh,
                expected_kwh=Decimal(str(round(mean, 4))),
            ))

    # ── 2. Gaps (missing readings > 2 hours) ─────────────────────────────
    for i in range(1, len(readings)):
        gap = readings[i].reading_at - readings[i - 1].reading_at
        if gap > timedelta(hours=2):
            hours = gap.total_seconds() / 3600
            anomalies.append(Anomaly(
                meter=meter,
                anomaly_type="gap",
                severity="warning" if hours < 6 else "critical",
                title=f"Reading gap of {hours:.1f} hours",
                description=(
                    f"No readings between {readings[i-1].reading_at:%Y-%m-%d %H:%M} "
                    f"and {readings[i].reading_at:%Y-%m-%d %H:%M} ({hours:.1f} hours). "
                    f"This may indicate meter communication issues."
                ),
                detected_at=readings[i - 1].reading_at,
            ))

    # ── 3. Flatlines (identical readings > 4 hours) ──────────────────────
    streak_start = 0
    for i in range(1, len(readings)):
        if readings[i].value_kwh != readings[streak_start].value_kwh:
            # Check if streak was long enough
            streak_duration = readings[i - 1].reading_at - readings[streak_start].reading_at
            if streak_duration > timedelta(hours=4):
                hours = streak_duration.total_seconds() / 3600
                anomalies.append(Anomaly(
                    meter=meter,
                    anomaly_type="flatline",
                    severity="info",
                    title=f"Flatline for {hours:.1f} hours",
                    description=(
                        f"Constant reading of {readings[streak_start].value_kwh} kWh "
                        f"from {readings[streak_start].reading_at:%Y-%m-%d %H:%M} "
                        f"to {readings[i-1].reading_at:%Y-%m-%d %H:%M}. "
                        f"This may indicate a stuck meter."
                    ),
                    detected_at=readings[streak_start].reading_at,
                    value_kwh=readings[streak_start].value_kwh,
                ))
            streak_start = i

    # ── 4. Negative readings ─────────────────────────────────────────────
    for reading in readings:
        if reading.value_kwh < 0:
            anomalies.append(Anomaly(
                meter=meter,
                anomaly_type="negative",
                severity="critical",
                title="Negative reading detected",
                description=(
                    f"Reading of {reading.value_kwh} kWh at {reading.reading_at:%Y-%m-%d %H:%M}. "
                    f"Negative readings are invalid and may indicate a meter fault."
                ),
                detected_at=reading.reading_at,
                value_kwh=reading.value_kwh,
                expected_kwh=Decimal(str(round(mean, 4))),
            ))

    if anomalies:
        Anomaly.objects.bulk_create(anomalies)
        logger.info(
            "Detected %d anomalies for meter %s",
            len(anomalies), meter.mpan,
        )

    return anomalies
