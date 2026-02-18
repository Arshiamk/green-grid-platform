from celery import shared_task


@shared_task
def generate_recommendations_task(customer_id: str):
    from recommendations.services import generate_recommendations
    recs = generate_recommendations(customer_id)
    return {"count": len(recs)}


@shared_task
def generate_all_recommendations_task():
    from customers.models import Customer
    dispatched = 0
    for c in Customer.objects.all():
        generate_recommendations_task.delay(str(c.pk))
        dispatched += 1
    return {"dispatched": dispatched}
