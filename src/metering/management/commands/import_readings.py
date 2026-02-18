"""
Management command to import meter readings from a CSV file (synchronous).

Usage:
    python manage.py import_readings path/to/readings.csv
"""

import csv
import sys
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime

from customers.models import Meter
from metering.models import MeterReading


class Command(BaseCommand):
    help = "Import meter readings from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to the CSV file")
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Bulk-create batch size (default: 1000)",
        )

    def handle(self, *args, **options):
        csv_path = options["csv_file"]
        batch_size = options["batch_size"]

        try:
            fh = open(csv_path, "r", encoding="utf-8-sig")
        except FileNotFoundError:
            raise CommandError(f"File not found: {csv_path}")

        reader = csv.DictReader(fh)
        required = {"mpan", "reading_at", "value_kwh"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise CommandError(f"CSV must have columns: {', '.join(required)}")

        rows = list(reader)
        fh.close()

        self.stdout.write(f"Found {len(rows)} rows in {csv_path}")

        # Lookup all MPANs
        mpan_set = {r.get("mpan", "").strip() for r in rows}
        meters = {m.mpan: m for m in Meter.objects.filter(mpan__in=mpan_set)}

        to_create = []
        errors = 0

        for i, row in enumerate(rows, start=2):
            mpan = row.get("mpan", "").strip()
            meter = meters.get(mpan)
            if not meter:
                self.stderr.write(f"  Row {i}: unknown MPAN {mpan}")
                errors += 1
                continue

            reading_at = parse_datetime(row.get("reading_at", "").strip())
            if not reading_at:
                self.stderr.write(f"  Row {i}: invalid datetime")
                errors += 1
                continue

            try:
                value = Decimal(row.get("value_kwh", "").strip())
            except (InvalidOperation, ValueError):
                self.stderr.write(f"  Row {i}: invalid kWh value")
                errors += 1
                continue

            reading_type = row.get("reading_type", "actual").strip()
            if reading_type not in ("actual", "estimated"):
                reading_type = "actual"

            to_create.append(
                MeterReading(
                    meter=meter,
                    reading_at=reading_at,
                    value_kwh=value,
                    reading_type=reading_type,
                )
            )

        # Bulk create
        created = 0
        for start in range(0, len(to_create), batch_size):
            batch = to_create[start : start + batch_size]
            MeterReading.objects.bulk_create(batch, ignore_conflicts=True)
            created += len(batch)

        self.stdout.write(
            self.style.SUCCESS(f"Done: {created} readings imported, {errors} errors")
        )
