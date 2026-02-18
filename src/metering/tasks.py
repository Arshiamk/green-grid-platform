"""
Celery tasks for meter reading ingestion.
"""

import csv
import io
import json
import logging
from decimal import Decimal, InvalidOperation

from celery import shared_task
from django.utils import timezone
from django.utils.dateparse import parse_datetime

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def process_readings_upload(self, file_id):
    """
    Parse an uploaded CSV, validate each row, and bulk-create MeterReadings.

    Expected CSV columns: mpan, reading_at, value_kwh, reading_type
    """
    from customers.models import Meter
    from metering.models import MeterReading, UploadedFile

    try:
        upload = UploadedFile.objects.get(pk=file_id)
    except UploadedFile.DoesNotExist:
        logger.error("UploadedFile %s not found", file_id)
        return

    upload.status = "processing"
    upload.save(update_fields=["status"])

    errors = []
    readings_to_create = []
    rows_total = 0

    # Build MPAN → Meter lookup
    try:
        content = upload.file.read().decode("utf-8-sig")
    except Exception as exc:
        upload.status = "failed"
        upload.error_log = json.dumps([{"row": 0, "error": f"Cannot read file: {exc}"}])
        upload.completed_at = timezone.now()
        upload.save()
        return

    reader = csv.DictReader(io.StringIO(content))

    # Collect all MPANs from the file first
    rows = list(reader)
    rows_total = len(rows)

    mpan_set = {row.get("mpan", "").strip() for row in rows}
    meters = {m.mpan: m for m in Meter.objects.filter(mpan__in=mpan_set)}

    for i, row in enumerate(rows, start=2):  # row 1 is header
        mpan = row.get("mpan", "").strip()
        reading_at_raw = row.get("reading_at", "").strip()
        value_raw = row.get("value_kwh", "").strip()
        reading_type = row.get("reading_type", "actual").strip()

        # Validate meter
        meter = meters.get(mpan)
        if not meter:
            errors.append({"row": i, "error": f"Unknown MPAN: {mpan}"})
            continue

        # Validate datetime
        reading_at = parse_datetime(reading_at_raw)
        if not reading_at:
            errors.append({"row": i, "error": f"Invalid datetime: {reading_at_raw}"})
            continue

        # Validate value
        try:
            value_kwh = Decimal(value_raw)
            if value_kwh < 0:
                raise InvalidOperation("Negative value")
        except (InvalidOperation, ValueError):
            errors.append({"row": i, "error": f"Invalid kWh value: {value_raw}"})
            continue

        # Validate reading type
        if reading_type not in ("actual", "estimated"):
            reading_type = "actual"

        readings_to_create.append(
            MeterReading(
                meter=meter,
                reading_at=reading_at,
                value_kwh=value_kwh,
                reading_type=reading_type,
            )
        )

    # Bulk create in batches
    batch_size = 1000
    created_count = 0
    for start in range(0, len(readings_to_create), batch_size):
        batch = readings_to_create[start : start + batch_size]
        MeterReading.objects.bulk_create(batch, ignore_conflicts=True)
        created_count += len(batch)

    # Finalise
    upload.rows_total = rows_total
    upload.rows_ok = created_count
    upload.rows_failed = len(errors)
    upload.error_log = json.dumps(errors) if errors else ""
    upload.status = "completed" if not errors else ("completed" if created_count > 0 else "failed")
    upload.completed_at = timezone.now()
    upload.save()

    logger.info(
        "Upload %s: %d/%d rows imported, %d errors",
        file_id, created_count, rows_total, len(errors),
    )
    return {"ok": created_count, "failed": len(errors)}
