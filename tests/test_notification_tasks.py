from app.scheduler.celery_app import celery_app


def test_notify_pending_task_registered() -> None:
    celery_app.loader.import_default_modules()
    assert "app.notifications.tasks.notify_pending" in celery_app.tasks


def test_notify_pending_beat_schedule_registered() -> None:
    entry = celery_app.conf.beat_schedule["notify_pending"]
    assert entry["task"] == "app.notifications.tasks.notify_pending"
