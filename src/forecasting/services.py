"""
Demand forecasting engine.

Uses a weighted moving average with day-of-week seasonality
to predict future energy consumption from historical readings.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

from django.utils import timezone

from customers.models import Meter
from metering.models import MeterReading

from .models import DemandForecast, ForecastPoint

logger = logging.getLogger(__name__)

# More recent days get higher weight
DAY_WEIGHTS = [1.0, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]  # oldest → newest


def generate_forecast(
    meter_id: str,
    days_ahead: int = 7,
    lookback_days: int = 7,
    granularity: str = "half_hourly",
) -> DemandForecast:
    """
    Generate a demand forecast for a meter.

    Algorithm:
    1. Fetch historical readings for the lookback period
    2. Build an average consumption profile per half-hour slot, grouped by day-of-week
    3. Apply weighted moving average (recent days matter more)
    4. Project forward for the requested period
    5. Add confidence intervals (±20% as a simple heuristic)
    """
    meter = Meter.objects.get(pk=meter_id)

    now = timezone.now().replace(minute=0, second=0, microsecond=0)
    lookback_start = now - timedelta(days=lookback_days)

    # ── 1. Fetch historical readings ────────────────────────────────────
    readings = list(
        MeterReading.objects.filter(
            meter=meter,
            reading_at__gte=lookback_start,
            reading_at__lt=now,
        ).order_by("reading_at")
    )

    if not readings:
        raise ValueError(f"No readings found for meter {meter.mpan} in the last {lookback_days} days")

    # ── 2. Build consumption profile ────────────────────────────────────
    # Key: (day_of_week, hour, half_hour_slot) → list of (value, weight)
    profile = defaultdict(list)

    for reading in readings:
        rt = reading.reading_at
        dow = rt.weekday()  # 0=Monday
        slot = (rt.hour, 0 if rt.minute < 30 else 30)

        # Weight based on how recent the day is
        days_ago = (now.date() - rt.date()).days
        if 0 <= days_ago < len(DAY_WEIGHTS):
            weight = DAY_WEIGHTS[-(days_ago + 1)]
        else:
            weight = DAY_WEIGHTS[0]

        profile[(dow, slot[0], slot[1])].append(
            (float(reading.value_kwh), weight)
        )

    # ── 3. Compute weighted averages ────────────────────────────────────
    avg_profile = {}
    for key, entries in profile.items():
        total_weighted = sum(v * w for v, w in entries)
        total_weight = sum(w for _, w in entries)
        avg = total_weighted / total_weight if total_weight > 0 else 0
        # Standard deviation for confidence
        variance = sum(w * (v - avg) ** 2 for v, w in entries) / total_weight if total_weight > 0 else 0
        std_dev = variance ** 0.5
        avg_profile[key] = (avg, std_dev)

    # ── 4. Project forward ──────────────────────────────────────────────
    forecast_start = now
    forecast_end = now + timedelta(days=days_ahead)

    # Determine step based on granularity
    if granularity == "daily":
        step_minutes = 1440
    elif granularity == "hourly":
        step_minutes = 60
    else:
        step_minutes = 30

    points = []
    total_predicted = Decimal("0")
    current = forecast_start

    # Fallback: overall average if no matching day-of-week slot
    all_values = [avg for avg, _ in avg_profile.values()]
    global_avg = sum(all_values) / len(all_values) if all_values else 0.1

    while current < forecast_end:
        dow = current.weekday()

        if granularity == "daily":
            # Sum all slots for this day of week
            day_total = 0
            day_std = 0
            slots_found = 0
            for h in range(24):
                for m in (0, 30):
                    key = (dow, h, m)
                    if key in avg_profile:
                        avg, std = avg_profile[key]
                        day_total += avg
                        day_std += std
                        slots_found += 1
            if slots_found == 0:
                day_total = global_avg * 48
                day_std = day_total * 0.2
            predicted = day_total
            std_dev = day_std
        else:
            slot = (current.hour, 0 if current.minute < 30 else 30)
            key = (dow, slot[0], slot[1])
            if key in avg_profile:
                predicted, std_dev = avg_profile[key]
            else:
                predicted = global_avg
                std_dev = global_avg * 0.2

        predicted_dec = Decimal(str(round(max(predicted, 0), 4)))
        margin = Decimal(str(round(max(std_dev * 1.96, predicted * 0.2), 4)))  # 95% CI or 20%

        points.append(ForecastPoint(
            timestamp=current,
            predicted_kwh=predicted_dec,
            lower_bound_kwh=max(predicted_dec - margin, Decimal("0")),
            upper_bound_kwh=predicted_dec + margin,
        ))
        total_predicted += predicted_dec
        current += timedelta(minutes=step_minutes)

    # ── 5. Save ─────────────────────────────────────────────────────────
    forecast = DemandForecast.objects.create(
        meter=meter,
        granularity=granularity,
        forecast_start=forecast_start,
        forecast_end=forecast_end,
        lookback_days=lookback_days,
        total_predicted_kwh=total_predicted,
    )

    for pt in points:
        pt.forecast = forecast
    ForecastPoint.objects.bulk_create(points)

    logger.info(
        "Forecast %s for %s: %d points, %.2f kWh total",
        forecast.pk, meter.mpan, len(points), total_predicted,
    )
    return forecast
