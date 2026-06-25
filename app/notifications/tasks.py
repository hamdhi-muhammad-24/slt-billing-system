from __future__ import annotations

from app.core.logging import get_logger
from app.scheduler.celery_app import celery_app

log = get_logger(__name__)


@celery_app.task
def notify_pending() -> dict:
    """Enqueue and send pending invoice notifications via the outbox."""
    from app.db.base import SessionLocal
    from app.notifications.service import scan_and_send

    log.info("notify_pending starting")

    db = SessionLocal()
    try:
        summary = scan_and_send(db)
    finally:
        db.close()

    log.info(
        "notify_pending complete: queued=%s sent=%s failed=%s",
        summary.get("queued"),
        summary.get("sent"),
        summary.get("failed"),
    )
    return summary
