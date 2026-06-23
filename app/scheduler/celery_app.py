from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "slt_billing",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.scheduler.tasks"],
)

celery_app.conf.beat_schedule = {
    "run_monthly_billing": {
        "task": "app.scheduler.tasks.run_monthly_billing",
        "schedule": crontab(day_of_month=1, hour=2, minute=0),
        "kwargs": {"period": None},
    },
}
