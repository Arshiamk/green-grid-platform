"""
Recommendation engine.

Analyses customer usage patterns and tariff assignments
to generate actionable energy-saving recommendations.
"""

import logging
from decimal import Decimal

from django.db.models import Avg, Sum

from customers.models import Customer
from metering.models import MeterReading
from tariffs.models import CustomerTariff, RateBand, Tariff

from .models import Recommendation

logger = logging.getLogger(__name__)


def generate_recommendations(customer_id: str) -> list[Recommendation]:
    """
    Analyse a customer's usage and tariff, then generate recommendations.

    Checks:
    1. High off-peak usage → suggest time-of-use tariff
    2. High peak usage → suggest peak shifting
    3. Overall high usage → general reduction tips
    4. No smart meter → suggest smart meter upgrade
    """
    customer = Customer.objects.get(pk=customer_id)
    recommendations = []

    # Get meters and recent readings (last 30 days)
    meter_ids = list(
        customer.properties.values_list("meters__id", flat=True)
    )
    meters = list(customer.properties.prefetch_related("meters").all())

    if not meter_ids:
        return recommendations

    from django.utils import timezone
    from datetime import timedelta

    thirty_days_ago = timezone.now() - timedelta(days=30)
    readings = MeterReading.objects.filter(
        meter_id__in=meter_ids,
        reading_at__gte=thirty_days_ago,
    )

    if not readings.exists():
        return recommendations

    # ── 1. Analyse usage patterns ───────────────────────────────────────
    total_kwh = readings.aggregate(total=Sum("value_kwh"))["total"] or Decimal("0")
    avg_per_reading = readings.aggregate(avg=Avg("value_kwh"))["avg"] or Decimal("0")

    # Check peak usage (16:00–20:00)
    peak_kwh = readings.filter(
        reading_at__hour__gte=16,
        reading_at__hour__lt=20,
    ).aggregate(total=Sum("value_kwh"))["total"] or Decimal("0")

    # Check off-peak usage (00:00–07:00)
    offpeak_kwh = readings.filter(
        reading_at__hour__lt=7,
    ).aggregate(total=Sum("value_kwh"))["total"] or Decimal("0")

    peak_ratio = float(peak_kwh / total_kwh) if total_kwh > 0 else 0
    offpeak_ratio = float(offpeak_kwh / total_kwh) if total_kwh > 0 else 0

    # ── 2. Get current tariff ───────────────────────────────────────────
    assignment = (
        CustomerTariff.objects.filter(customer=customer)
        .select_related("tariff")
        .order_by("-effective_from")
        .first()
    )
    current_tariff = assignment.tariff if assignment else None

    # ── 3. Generate recommendations ─────────────────────────────────────

    # High off-peak usage on a flat tariff → suggest time-of-use
    if current_tariff and current_tariff.tariff_type != "time_of_use" and offpeak_ratio > 0.2:
        tou_tariffs = Tariff.objects.filter(
            tariff_type="time_of_use",
            fuel_type=current_tariff.fuel_type,
            is_active=True,
        ).first()

        if tou_tariffs:
            # Estimate savings: off-peak kWh × (current rate - off-peak rate)
            current_rate = RateBand.objects.filter(tariff=current_tariff).first()
            offpeak_rate = RateBand.objects.filter(
                tariff=tou_tariffs, label__icontains="off"
            ).first()

            if current_rate and offpeak_rate:
                monthly_saving = float(offpeak_kwh) * float(
                    current_rate.rate_pence_per_kwh - offpeak_rate.rate_pence_per_kwh
                )
                annual_saving = max(int(monthly_saving * 12), 0)

                recommendations.append(Recommendation(
                    customer=customer,
                    category="tariff_switch",
                    priority="high",
                    title=f"Switch to {tou_tariffs.name}",
                    description=(
                        f"You use {offpeak_ratio:.0%} of your energy during off-peak hours. "
                        f"Switching to {tou_tariffs.name} could save you approximately "
                        f"£{annual_saving / 100:.2f}/year with its lower off-peak rate of "
                        f"{offpeak_rate.rate_pence_per_kwh}p/kWh."
                    ),
                    estimated_saving_pence=annual_saving,
                ))

    # High peak usage → suggest peak shifting
    if peak_ratio > 0.3:
        estimated_shift_saving = int(float(peak_kwh) * 0.1 * 15)  # rough estimate
        recommendations.append(Recommendation(
            customer=customer,
            category="peak_shifting",
            priority="medium",
            title="Shift energy usage away from peak hours",
            description=(
                f"{peak_ratio:.0%} of your usage falls between 4pm–8pm when rates are highest. "
                f"Running dishwashers, washing machines, and EV charging during off-peak hours "
                f"(midnight–7am) could reduce your bill."
            ),
            estimated_saving_pence=estimated_shift_saving,
        ))

    # Overall high usage → general tips
    daily_kwh = float(total_kwh) / 30
    if daily_kwh > 10:  # above UK average ~8 kWh/day
        recommendations.append(Recommendation(
            customer=customer,
            category="usage_reduction",
            priority="medium",
            title="Your usage is above average",
            description=(
                f"Your daily average is {daily_kwh:.1f} kWh, which is above the UK average "
                f"of ~8 kWh/day. Consider checking for draughts, improving insulation, "
                f"or upgrading to energy-efficient appliances."
            ),
            estimated_saving_pence=int((daily_kwh - 8) * 365 * 24.5),  # savings at avg rate
        ))

    # Check for non-smart meters
    has_non_smart = any(
        not meter.is_smart
        for prop in meters
        for meter in prop.meters.all()
    )
    if has_non_smart:
        recommendations.append(Recommendation(
            customer=customer,
            category="appliance",
            priority="low",
            title="Upgrade to a smart meter",
            description=(
                "One or more of your meters is not a smart meter. Smart meters provide "
                "real-time usage data, enabling more accurate billing and better insights "
                "into your consumption patterns."
            ),
            estimated_saving_pence=0,
        ))

    # Bulk create
    if recommendations:
        Recommendation.objects.bulk_create(recommendations)
        logger.info(
            "Generated %d recommendations for %s",
            len(recommendations), customer.account_number,
        )

    return recommendations
