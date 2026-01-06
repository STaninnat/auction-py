import os

from celery import Celery
from celery.schedules import crontab

# Tell Celery to read the configuration from the Django settings file.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Create an instance of Celery.
app = Celery("auction_core")

# Load the configuration from the Django settings file.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps.
app.autodiscover_tasks()

# Schedule tasks to run at regular intervals.
app.conf.beat_schedule = {
    "close-auctions-every-minute": {
        "task": "auctions.tasks.check_and_close_expired_auctions",
        "schedule": crontab(minute="*"),
    }
}
