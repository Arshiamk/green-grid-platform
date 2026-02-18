from celery import shared_task


@shared_task
def ping():
    """Simple test task — returns 'pong'."""
    return "pong"
