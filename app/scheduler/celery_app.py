from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "slt_billing",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.scheduler.tasks", "app.notifications.tasks"],
)

celery_app.conf.beat_schedule = {
    "run_monthly_billing": {
        "task": "app.scheduler.tasks.evaluate_billing_schedules",
        "schedule": crontab(minute="*/15"),
    },
    "notify_pending": {
        "task": "app.notifications.tasks.notify_pending",
        "schedule": crontab(minute="*/15"),
    },
}
