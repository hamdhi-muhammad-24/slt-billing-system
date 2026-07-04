from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.billing.batch import run_billing_batch
from app.db.models import (
    BillingApprovalStatus,
    BillingRunApproval,
    BillingSchedule,
    BillingScheduleMode,
    User,
)


def previous_billing_period(now: datetime) -> str:
    first_of_month = now.date().replace(day=1)
    previous_month_last = first_of_month - timedelta(days=1)
    return previous_month_last.strftime("%Y-%m")


def get_or_create_default_schedule(db: Session) -> BillingSchedule:
    schedule = db.scalar(select(BillingSchedule).order_by(BillingSchedule.id).limit(1))
    if schedule is not None:
        return schedule
    schedule = BillingSchedule(
        name="Monthly SLT billing",
        day_of_month=1,
        run_time="02:00",
        timezone="Asia/Colombo",
        schedule_mode=BillingScheduleMode.AUTOMATIC,
        is_active=True,
        send_email=True,
        send_sms=True,
        approval_lead_days=1,
    )
    db.add(schedule)
    db.flush()
    return schedule


def apply_schedule_update(db: Session, body) -> BillingSchedule:
    schedule = get_or_create_default_schedule(db)
    schedule.name = body.name or schedule.name
    schedule.day_of_month = body.day_of_month
    schedule.run_time = body.run_time
    schedule.timezone = body.timezone
    schedule.schedule_mode = BillingScheduleMode(body.schedule_mode)
    schedule.is_active = body.is_active
    schedule.send_email = body.send_email
    schedule.send_sms = body.send_sms
    schedule.approval_lead_days = body.approval_lead_days
    schedule.approval_email = body.approval_email
    db.flush()
    return schedule


def list_approvals(db: Session, *, limit: int = 20) -> list[BillingRunApproval]:
    return db.scalars(
        select(BillingRunApproval)
        .order_by(BillingRunApproval.requested_at.desc(), BillingRunApproval.id.desc())
        .limit(limit)
    ).all()


def get_or_create_approval(
    db: Session,
    schedule: BillingSchedule,
    period: str,
    now: datetime,
) -> BillingRunApproval:
    approval = db.scalar(
        select(BillingRunApproval).where(
            BillingRunApproval.billing_schedule_id == schedule.id,
            BillingRunApproval.period == period,
        )
    )
    if approval is not None:
        return approval
    approval = BillingRunApproval(
        billing_schedule_id=schedule.id,
        period=period,
        status=BillingApprovalStatus.PENDING,
        requested_to=schedule.approval_email,
        requested_at=now,
        expires_at=now + timedelta(days=schedule.approval_lead_days),
    )
    db.add(approval)
    db.flush()
    return approval


def approve_billing_run(
    db: Session,
    approval_id: int,
    *,
    user_id: int | None,
    notes: str | None = None,
) -> BillingRunApproval:
    approval = db.get(BillingRunApproval, approval_id)
    if approval is None:
        raise ValueError(f"Billing run approval {approval_id} not found")
    approval.status = BillingApprovalStatus.APPROVED
    approval.approved_at = datetime.now(tz=ZoneInfo("Asia/Colombo"))
    approval.decided_by_user_id = user_id if user_id is not None and db.get(User, user_id) else None
    approval.notes = notes
    db.flush()
    return approval


def reject_billing_run(
    db: Session,
    approval_id: int,
    *,
    user_id: int | None,
    notes: str | None = None,
) -> BillingRunApproval:
    approval = db.get(BillingRunApproval, approval_id)
    if approval is None:
        raise ValueError(f"Billing run approval {approval_id} not found")
    approval.status = BillingApprovalStatus.REJECTED
    approval.rejected_at = datetime.now(tz=ZoneInfo("Asia/Colombo"))
    approval.decided_by_user_id = user_id if user_id is not None and db.get(User, user_id) else None
    approval.notes = notes
    db.flush()
    return approval


def _local_now(schedule: BillingSchedule, now: datetime | None = None) -> datetime:
    tz = ZoneInfo(schedule.timezone or "Asia/Colombo")
    if now is None:
        return datetime.now(tz=tz)
    if now.tzinfo is None:
        return now.replace(tzinfo=tz)
    return now.astimezone(tz)


def _schedule_time_reached(schedule: BillingSchedule, now: datetime) -> bool:
    hour, minute = [int(part) for part in schedule.run_time.split(":", 1)]
    return now.day == schedule.day_of_month and (now.hour, now.minute) >= (hour, minute)


def _approval_request_due(schedule: BillingSchedule, now: datetime) -> bool:
    request_day = max(1, schedule.day_of_month - schedule.approval_lead_days)
    return now.day >= request_day


def evaluate_billing_schedules(db: Session, *, now: datetime | None = None) -> dict:
    schedule = get_or_create_default_schedule(db)
    local_now = _local_now(schedule, now)
    period = previous_billing_period(local_now)
    result = {
        "schedule_id": schedule.id,
        "period": period,
        "action": "inactive",
        "run_id": None,
        "approval_id": None,
    }

    if not schedule.is_active:
        return result
    if schedule.last_triggered_period == period:
        result["action"] = "already_triggered"
        return result

    if schedule.schedule_mode == BillingScheduleMode.APPROVAL_REQUIRED:
        if _approval_request_due(schedule, local_now):
            approval = get_or_create_approval(db, schedule, period, local_now)
            result["approval_id"] = approval.id
            if approval.status == BillingApprovalStatus.REJECTED:
                result["action"] = "rejected"
                return result
            if (
                approval.status == BillingApprovalStatus.PENDING
                and approval.expires_at is not None
                and local_now > approval.expires_at
            ):
                approval.status = BillingApprovalStatus.EXPIRED
                result["action"] = "approval_expired"
                return result
            if approval.status == BillingApprovalStatus.PENDING:
                result["action"] = "awaiting_approval"
                return result
            if approval.status == BillingApprovalStatus.EXPIRED:
                result["action"] = "approval_expired"
                return result
        else:
            result["action"] = "waiting_for_approval_window"
            return result

    if not _schedule_time_reached(schedule, local_now):
        result["action"] = "waiting_for_schedule_time"
        return result

    batch = run_billing_batch(
        period,
        session=db,
        send_notifications=True,
        send_email=schedule.send_email,
        send_sms=schedule.send_sms,
    )
    run_id = batch.get("run_id")
    schedule.last_triggered_period = period
    if schedule.schedule_mode == BillingScheduleMode.APPROVAL_REQUIRED:
        approval = get_or_create_approval(db, schedule, period, local_now)
        approval.billing_run_id = run_id
    result["action"] = "triggered"
    result["run_id"] = run_id
    return result
