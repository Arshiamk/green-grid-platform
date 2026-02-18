from celery import shared_task


@shared_task
def detect_anomalies_task(meter_id: str, lookback_days: int = 7):
    from anomalies.services import detect_anomalies
    anomalies = detect_anomalies(meter_id, lookback_days)
    return {"count": len(anomalies)}


@shared_task
def detect_all_anomalies_task(lookback_days: int = 7):
    from customers.models import Meter
    dispatched = 0
    for meter in Meter.objects.filter(is_smart=True):
        detect_anomalies_task.delay(str(meter.pk), lookback_days)
        dispatched += 1
    return {"dispatched": dispatched}
