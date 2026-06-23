from __future__ import annotations

from datetime import date, timedelta

from app.core.logging import get_logger
from app.scheduler.celery_app import celery_app

log = get_logger(__name__)


@celery_app.task
def ping() -> str:
    return "pong"


@celery_app.task
def run_monthly_billing(period: str | None = None) -> dict:
    if period is None:
        today = date.today()
        # first day of current month minus one day = last day of previous month
        first_of_this_month = today.replace(day=1)
        last_month = first_of_this_month - timedelta(days=1)
        period = last_month.strftime("%Y-%m")

    log.info("run_monthly_billing starting: period=%s", period)

    from app.billing.batch import run_billing_batch

    summary = run_billing_batch(period)

    log.info(
        "run_monthly_billing complete: period=%s run_id=%s succeeded=%s failed=%s",
        period,
        summary.get("run_id"),
        summary.get("succeeded"),
        summary.get("failed"),
    )
    return summary
