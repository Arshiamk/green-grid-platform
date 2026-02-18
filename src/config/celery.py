"""
Celery configuration for Green Grid Platform.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("green_grid")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
