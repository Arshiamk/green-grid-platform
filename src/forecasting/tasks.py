"""
Celery tasks for demand forecasting.
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def generate_forecast_task(
    meter_id: str,
    days_ahead: int = 7,
    lookback_days: int = 7,
    granularity: str = "half_hourly",
):
    """Generate a forecast for a single meter."""
    from forecasting.services import generate_forecast

    forecast = generate_forecast(
        meter_id=meter_id,
        days_ahead=days_ahead,
        lookback_days=lookback_days,
        granularity=granularity,
    )
    return {"forecast_id": str(forecast.pk), "points": forecast.points.count()}


@shared_task
def generate_all_forecasts_task(
    days_ahead: int = 7,
    lookback_days: int = 7,
    granularity: str = "half_hourly",
):
    """Generate forecasts for all smart meters."""
    from customers.models import Meter

    meters = Meter.objects.filter(is_smart=True)
    dispatched = 0
    for meter in meters:
        generate_forecast_task.delay(
            str(meter.pk), days_ahead, lookback_days, granularity,
        )
        dispatched += 1

    logger.info("Dispatched %d forecast tasks", dispatched)
    return {"dispatched": dispatched}
