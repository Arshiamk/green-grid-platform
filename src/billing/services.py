"""
Billing calculation engine.

generate_bill(customer_id, period_start, period_end)
  → creates a Bill with BillLineItems from meter readings × tariff rates.
"""

import logging
from datetime import date, time as dtime
from decimal import Decimal

from django.db.models import Sum

from customers.models import Customer
from metering.models import MeterReading
from tariffs.models import CustomerTariff, RateBand

from .models import Bill, BillLineItem

logger = logging.getLogger(__name__)


def generate_bill(
    customer_id: str,
    period_start: date,
    period_end: date,
) -> Bill:
    """
    Generate a bill for a customer over a date range.

    1. Find the active tariff assignment for the period.
    2. Query all meter readings in the period.
    3. Calculate usage charges (flat or time-of-use).
    4. Calculate standing charge.
    5. Create Bill + BillLineItems.
    """
    customer = Customer.objects.get(pk=customer_id)

    # ── 1. Find active tariff ────────────────────────────────────────────
    assignment = (
        CustomerTariff.objects.filter(
            customer=customer,
            effective_from__lte=period_end,
        )
        .filter(
            # effective_to is null (ongoing) or extends into the period
            effective_to__isnull=True,
        )
        .select_related("tariff")
        .order_by("-effective_from")
        .first()
    )

    if not assignment:
        # Try with effective_to >= period_start
        assignment = (
            CustomerTariff.objects.filter(
                customer=customer,
                effective_from__lte=period_end,
                effective_to__gte=period_start,
            )
            .select_related("tariff")
            .order_by("-effective_from")
            .first()
        )

    if not assignment:
        raise ValueError(f"No active tariff found for {customer.account_number} in {period_start}–{period_end}")

    tariff = assignment.tariff
    rate_bands = list(RateBand.objects.filter(tariff=tariff).order_by("start_time"))

    # ── 2. Get meter readings ────────────────────────────────────────────
    meters = list(customer.properties.values_list("meters__id", flat=True))
    readings = MeterReading.objects.filter(
        meter_id__in=meters,
        reading_at__date__gte=period_start,
        reading_at__date__lte=period_end,
    ).select_related("meter")

    # ── 3. Calculate usage charges ───────────────────────────────────────
    line_items = []

    if tariff.tariff_type == "time_of_use" and len(rate_bands) > 1:
        # Bucket readings by rate band
        band_usage = {rb.id: Decimal("0") for rb in rate_bands}

        for reading in readings:
            reading_time = reading.reading_at.time()
            matched_band = _match_rate_band(reading_time, rate_bands)
            if matched_band:
                band_usage[matched_band.id] += reading.value_kwh

        for rb in rate_bands:
            kwh = band_usage[rb.id]
            if kwh > 0:
                amount = (kwh * rb.rate_pence_per_kwh).quantize(Decimal("0.01"))
                line_items.append({
                    "description": f"{tariff.name} — {rb.label or 'Band'} usage",
                    "rate_band_label": rb.label or "",
                    "kwh": kwh,
                    "rate_pence_per_kwh": rb.rate_pence_per_kwh,
                    "amount_pence": amount,
                })
    else:
        # Flat rate — use the first (only) rate band
        flat_rate = rate_bands[0] if rate_bands else None
        if not flat_rate:
            raise ValueError(f"Tariff {tariff.code} has no rate bands")

        total_kwh = readings.aggregate(total=Sum("value_kwh"))["total"] or Decimal("0")
        amount = (total_kwh * flat_rate.rate_pence_per_kwh).quantize(Decimal("0.01"))
        line_items.append({
            "description": f"{tariff.name} — usage",
            "rate_band_label": flat_rate.label or "Standard",
            "kwh": total_kwh,
            "rate_pence_per_kwh": flat_rate.rate_pence_per_kwh,
            "amount_pence": amount,
        })

    # ── 4. Standing charge ───────────────────────────────────────────────
    days = (period_end - period_start).days
    if days < 1:
        days = 1
    standing_total = (tariff.standing_charge_pence * days).quantize(Decimal("0.01"))

    line_items.append({
        "description": f"Standing charge ({days} days × {tariff.standing_charge_pence}p/day)",
        "rate_band_label": "",
        "kwh": Decimal("0"),
        "rate_pence_per_kwh": Decimal("0"),
        "amount_pence": standing_total,
    })

    # ── 5. Create Bill ───────────────────────────────────────────────────
    total_kwh = sum(li["kwh"] for li in line_items)
    usage_charge = sum(li["amount_pence"] for li in line_items if li["kwh"] > 0)
    total_amount = sum(li["amount_pence"] for li in line_items)

    bill = Bill.objects.create(
        customer=customer,
        period_start=period_start,
        period_end=period_end,
        total_kwh=total_kwh,
        standing_charge_pence=standing_total,
        usage_charge_pence=usage_charge,
        total_amount_pence=total_amount,
    )

    # Create line items
    meter = customer.properties.first().meters.first() if customer.properties.exists() else None
    BillLineItem.objects.bulk_create([
        BillLineItem(
            bill=bill,
            meter=meter,
            tariff=tariff,
            **li,
        )
        for li in line_items
    ])

    logger.info(
        "Generated bill %s for %s: £%.2f (%s kWh)",
        bill.pk, customer.account_number,
        total_amount / 100, total_kwh,
    )
    return bill


def _match_rate_band(reading_time: dtime, rate_bands: list[RateBand]) -> RateBand | None:
    """Match a reading time to the correct rate band."""
    for rb in rate_bands:
        if rb.start_time is None:
            return rb  # Flat-rate fallback

        # Handle overnight bands (e.g. 20:00 → 00:00)
        if rb.start_time <= rb.end_time:
            if rb.start_time <= reading_time < rb.end_time:
                return rb
        else:
            # Wraps midnight
            if reading_time >= rb.start_time or reading_time < rb.end_time:
                return rb

    # Fallback to first band
    return rate_bands[0] if rate_bands else None
