"""
Celery tasks for billing.
"""

import logging
from datetime import date

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def generate_bill_task(customer_id: str, period_start: str, period_end: str):
    """Generate a bill for a single customer."""
    from billing.services import generate_bill

    bill = generate_bill(
        customer_id=customer_id,
        period_start=date.fromisoformat(period_start),
        period_end=date.fromisoformat(period_end),
    )
    return {"bill_id": str(bill.pk), "total_pounds": float(bill.total_pounds)}


@shared_task
def generate_all_bills_task(period_start: str, period_end: str):
    """Generate bills for all customers with active tariff assignments."""
    from customers.models import Customer
    from tariffs.models import CustomerTariff

    start = date.fromisoformat(period_start)
    end = date.fromisoformat(period_end)

    # Find customers with active tariffs
    customer_ids = (
        CustomerTariff.objects.filter(
            effective_from__lte=end,
        )
        .values_list("customer_id", flat=True)
        .distinct()
    )

    results = []
    for cid in customer_ids:
        generate_bill_task.delay(str(cid), period_start, period_end)
        results.append(str(cid))

    logger.info("Dispatched %d bill generation tasks", len(results))
    return {"dispatched": len(results)}
