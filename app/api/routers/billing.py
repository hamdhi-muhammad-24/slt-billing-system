from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import crud
from app.api.deps import get_db
from app.api.errors import DuplicateInvoice, NotFound
from app.api.schemas import (
    AdminDashboardSummaryOut,
    ApprovalDecisionRequest,
    BillingRunApprovalOut,
    BillingRunOut,
    BillingScheduleOut,
    BillingScheduleUpdateRequest,
    EvaluateBillingSchedulesRequest,
    GenerateBatchRequest,
    GenerateOneRequest,
    InvoiceOut,
    Page,
    RetryBillingRunItemRequest,
    SendBillingRunRequest,
)
from app.auth.dependencies import require_admin
from app.auth.schemas import UserOut
from app.billing import engine as billing_engine
from app.billing import repository

router = APIRouter(prefix="/billing", tags=["billing"])

@router.get(
    "/admin-summary",
    response_model=AdminDashboardSummaryOut,
    summary="Admin billing dashboard summary",
    description="Returns operational billing counts, recent runs, recent invoices, notifications, and alerts.",
)
def admin_dashboard_summary(
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
) -> AdminDashboardSummaryOut:
    return crud.get_admin_dashboard_summary(db)


@router.post(
    "/generate-one",
    response_model=InvoiceOut,
    status_code=201,
    summary="Generate one invoice",
    description=(
        "Runs the billing engine for a single account + billing month and "
        "transitions the invoice from DRAFT to GENERATED. "
        "Returns `409` if the invoice is already a frozen (GENERATED) snapshot."
    ),
)
def generate_one(
    body: GenerateOneRequest,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
) -> InvoiceOut:
    year  = int(body.period[:4])
    month = int(body.period[5:])

    info = crud.get_invoice_info_for_billing_period(db, body.account_id, year, month)
    if info is None:
        raise NotFound(
            f"No invoice found for account {body.account_id} in period {body.period}"
        )

    invoice_id, account_number, period_start, period_end, status = info

    if status == "GENERATED":
        raise DuplicateInvoice(
            f"Invoice for account {body.account_id} period {body.period} "
            "already exists as a frozen snapshot"
        )

    # Run the billing engine — validates all line-item data is present and
    # consistent; does not overwrite the stored totals (frozen snapshot rule).
    billing_engine.build_bill(db, account_number, period_start, period_end)

    repository.update_invoice_status(invoice_id, "GENERATED", db)
    db.commit()

    out = crud.get_invoice(db, invoice_id)
    assert out is not None  # invoice was just updated; cannot be missing
    return out


@router.get(
    "/runs",
    response_model=Page[BillingRunOut],
    summary="List billing runs",
    description="Returns recent billing runs with summary counts. Use the detail endpoint for per-account rows.",
)
def list_billing_runs(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
) -> Page[BillingRunOut]:
    safe_limit = max(1, min(limit, 200))
    safe_offset = max(0, offset)
    items, total = crud.list_billing_run_outs(db, limit=safe_limit, offset=safe_offset)
    return Page(items=items, total=total, limit=safe_limit, offset=safe_offset)


@router.get(
    "/schedule",
    response_model=BillingScheduleOut,
    summary="Get billing schedule",
)
def get_billing_schedule(
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
) -> BillingScheduleOut:
    from app.billing.schedules import get_or_create_default_schedule

    schedule = get_or_create_default_schedule(db)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.put(
    "/schedule",
    response_model=BillingScheduleOut,
    summary="Update billing schedule",
)
def update_billing_schedule(
    body: BillingScheduleUpdateRequest,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
) -> BillingScheduleOut:
    from app.billing.schedules import apply_schedule_update

    schedule = apply_schedule_update(db, body)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.post(
    "/schedule/evaluate",
    summary="Evaluate billing schedule now",
)
def evaluate_billing_schedule(
    body: EvaluateBillingSchedulesRequest,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
) -> dict:
    from app.billing.schedules import evaluate_billing_schedules

    result = evaluate_billing_schedules(db, now=body.now)
    db.commit()
    return result


@router.get(
    "/schedule/approvals",
    response_model=list[BillingRunApprovalOut],
    summary="List billing run approvals",
)
def list_billing_run_approvals(
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
) -> list[BillingRunApprovalOut]:
    from app.billing.schedules import list_approvals

    return list_approvals(db)


@router.post(
    "/schedule/approvals/{approval_id}/approve",
    response_model=BillingRunApprovalOut,
    summary="Approve scheduled billing run",
)
def approve_scheduled_billing_run(
    approval_id: int,
    body: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_admin),
) -> BillingRunApprovalOut:
    from app.billing.schedules import approve_billing_run

    try:
        approval = approve_billing_run(db, approval_id, user_id=user.id, notes=body.notes)
    except ValueError as exc:
        raise NotFound(str(exc))
    db.commit()
    db.refresh(approval)
    return approval


@router.post(
    "/schedule/approvals/{approval_id}/reject",
    response_model=BillingRunApprovalOut,
    summary="Reject scheduled billing run",
)
def reject_scheduled_billing_run(
    approval_id: int,
    body: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_admin),
) -> BillingRunApprovalOut:
    from app.billing.schedules import reject_billing_run

    try:
        approval = reject_billing_run(db, approval_id, user_id=user.id, notes=body.notes)
    except ValueError as exc:
        raise NotFound(str(exc))
    db.commit()
    db.refresh(approval)
    return approval


@router.post(
    "/runs/{run_id}/send",
    response_model=BillingRunOut,
    summary="Send generated invoices for a billing run",
)
def send_billing_run(
    run_id: int,
    body: SendBillingRunRequest,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
) -> BillingRunOut:
    from app.billing.batch import send_billing_run_notifications

    if crud.get_billing_run_out(db, run_id, include_items=False) is None:
        raise NotFound(f"Billing run {run_id} not found")
    send_billing_run_notifications(
        run_id,
        session=db,
        send_email=body.send_email,
        send_sms=body.send_sms,
    )
    db.commit()
    out = crud.get_billing_run_out(db, run_id)
    assert out is not None
    return out


@router.post(
    "/run-items/{item_id}/retry",
    response_model=BillingRunOut,
    summary="Retry one billing run item",
)
def retry_billing_run_item(
    item_id: int,
    body: RetryBillingRunItemRequest,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
) -> BillingRunOut:
    from app.billing.batch import retry_billing_run_item as retry_item

    try:
        result = retry_item(
            item_id,
            session=db,
            send_notifications=body.send_notifications,
            send_email=body.send_email,
            send_sms=body.send_sms,
        )
    except ValueError as exc:
        raise NotFound(str(exc))
    db.commit()
    out = crud.get_billing_run_out(db, result["run_id"])
    assert out is not None
    return out


@router.post(
    "/generate-batch",
    response_model=BillingRunOut,
    status_code=202,
    summary="Generate batch",
    description=(
        "Synchronously generates invoices for all active accounts billed in a given month, "
        "or for the specified `account_ids` subset. Per-account failures are recorded in "
        "`billing_run_failures` and do not abort the run. "
        "Returns `202` with the billing run summary including any recorded failures."
    ),
)
def generate_batch(
    body: GenerateBatchRequest,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
) -> BillingRunOut:
    from app.billing.batch import run_billing_batch

    result = run_billing_batch(
        body.period,
        session=db,
        account_ids=body.account_ids,
        send_notifications=body.send_notifications,
    )
    db.commit()

    run_id = result.get("run_id")
    if run_id is None:
        raise NotFound(f"No active-account invoices found for period {body.period}")
    out = crud.get_billing_run_out(db, run_id)
    assert out is not None
    return out


@router.get(
    "/runs/{run_id}",
    response_model=BillingRunOut,
    summary="Get billing run",
    description=(
        "Returns the status, account counts, and per-account failure details "
        "for a batch billing run."
    ),
)
def get_billing_run(
    run_id: int,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
) -> BillingRunOut:
    out = crud.get_billing_run_out(db, run_id)
    if out is None:
        raise NotFound(f"Billing run {run_id} not found")
    return out
