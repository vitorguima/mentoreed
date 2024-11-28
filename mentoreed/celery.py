import os

from celery import Celery
from django.conf import settings

# TODO: change this in prod
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mentoreed.settings.local")

app = Celery("mentoreed")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
