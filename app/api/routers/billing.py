from __future__ import annotations

from calendar import monthrange
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import crud
from app.api.deps import get_db
from app.api.errors import DuplicateInvoice, NotFound
from app.api.schemas import AdminDashboardSummaryOut, BillingRunOut, GenerateBatchRequest, GenerateOneRequest, InvoiceOut
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
    year  = int(body.period[:4])
    month = int(body.period[5:])

    all_invoices = repository.list_invoices_for_billing_month(year, month, db)

    if body.account_ids is not None:
        id_set   = set(body.account_ids)
        invoices = [inv for inv in all_invoices if inv.account_id in id_set]
    else:
        invoices = all_invoices

    run_period_start = date(year, month, 1)
    run_period_end   = date(year, month, monthrange(year, month)[1])

    # create_billing_run flushes internally so run_id is available immediately
    run_id = repository.create_billing_run(
        run_period_start, run_period_end, len(invoices), db
    )

    succeeded = 0
    failed    = 0

    for inv in invoices:
        sp = db.begin_nested()  # savepoint — isolates each account's failure
        try:
            if inv.inv_status == "GENERATED":
                # Already a frozen snapshot; idempotent skip counts as success
                succeeded += 1
                sp.commit()
                continue

            billing_engine.build_bill(db, inv.account_number, inv.period_start, inv.period_end)
            repository.update_invoice_status(inv.inv_id, "GENERATED", db)
            sp.commit()
            succeeded += 1

        except Exception as exc:
            sp.rollback()
            failed += 1
            # Record the failure in a fresh savepoint; outer transaction is still live
            sp2 = db.begin_nested()
            try:
                repository.record_run_failure(run_id, inv.account_id, str(exc), db)
                sp2.commit()
            except Exception:
                sp2.rollback()

    repository.finish_billing_run(run_id, succeeded, failed, db)
    db.commit()

    out = crud.get_billing_run_out(db, run_id)
    assert out is not None  # run was just created
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
