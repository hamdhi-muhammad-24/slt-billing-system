import logging
from datetime import date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
import asyncio

from app.db.base import SessionLocal
from app.db.models import BillingSchedule, GmfUpload, GmfUploadStatus, BillingRun, RunStatus, NotificationEvent, NotificationEventType

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def run_approved_gmfs():
    """Finds all APPROVED GMFs and triggers generation for them."""
    logger.info("Scheduler triggered: checking for APPROVED GMFs to generate...")
    with SessionLocal() as db:
        uploads = db.query(GmfUpload).filter(
            GmfUpload.status == GmfUploadStatus.APPROVED
        ).all()
        
        if not uploads:
            logger.info("No APPROVED GMFs found. Nothing to do.")
            return

        for upload in uploads:
            logger.info(f"Starting scheduled run for upload: {upload.filename}")
            upload.status = GmfUploadStatus.GENERATING
            
            run = BillingRun(
                batch_name=upload.filename,
                cycle_number=upload.cycle_number,
                period_start=date.today(),
                period_end=date.today(),
                status=RunStatus.RUNNING,
                succeeded=0,
                failed=0,
            )
            db.add(run)
            db.flush()
            
            upload.billing_run_id = run.id
            
            notif = NotificationEvent(
                event_type=NotificationEventType.BATCH_STARTED,
                title="Scheduled Batch Generation Started",
                message=f"Invoice generation started automatically for '{upload.filename}'.",
                upload_id=upload.id,
                run_id=run.id,
            )
            db.add(notif)
            db.commit()
            db.refresh(run)
            
            # Fire and forget the synchronous generation task in a thread
            from app.api.routers.billing import _background_generate
            asyncio.get_running_loop().run_in_executor(None, _background_generate, upload.id, run.id)

def reload_schedules():
    """Clears all jobs and reloads them from the database."""
    scheduler.remove_all_jobs()
    with SessionLocal() as db:
        schedules = db.query(BillingSchedule).filter(BillingSchedule.is_active == True).all()
        
        for sched in schedules:
            try:
                hour, minute = map(int, sched.run_time.split(':'))
                
                # Add job for this schedule
                scheduler.add_job(
                    run_approved_gmfs,
                    'cron',
                    day=sched.day_of_month,
                    hour=hour,
                    minute=minute,
                    timezone=sched.timezone,
                    id=f'schedule_{sched.id}',
                    name=sched.name,
                    replace_existing=True
                )
                logger.info(f"Loaded schedule: {sched.name} (Day {sched.day_of_month} at {sched.run_time})")
            except Exception as e:
                logger.error(f"Failed to load schedule {sched.id}: {e}")

def start_scheduler():
    """Starts the scheduler if not already running."""
    if not scheduler.running:
        reload_schedules()
        scheduler.start()
        logger.info("Billing Scheduler started.")
