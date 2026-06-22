from __future__ import annotations

from calendar import monthrange
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import crud
from app.api.deps import get_db
from app.api.schemas import BillingRunOut, GenerateBatchRequest, GenerateOneRequest, InvoiceOut
from app.billing import engine as billing_engine
from app.billing import repository

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/generate-one", response_model=InvoiceOut, status_code=201)
def generate_one(
    body: GenerateOneRequest,
    db: Session = Depends(get_db),
) -> InvoiceOut:
    year  = int(body.period[:4])
    month = int(body.period[5:])

    info = crud.get_invoice_info_for_billing_period(db, body.account_id, year, month)
    if info is None:
        raise HTTPException(
            status_code=404,
            detail=f"No invoice found for account {body.account_id} in period {body.period}",
        )

    invoice_id, account_number, period_start, period_end, status = info

    if status == "GENERATED":
        raise HTTPException(
            status_code=409,
            detail=(
                f"Invoice for account {body.account_id} period {body.period} "
                "already exists as a frozen snapshot"
            ),
        )

    # Run the billing engine — validates all line-item data is present and
    # consistent; does not overwrite the stored totals (frozen snapshot rule).
    billing_engine.build_bill(db, account_number, period_start, period_end)

    repository.update_invoice_status(invoice_id, "GENERATED", db)
    db.commit()

    out = crud.get_invoice(db, invoice_id)
    assert out is not None  # invoice was just updated; cannot be missing
    return out


@router.post("/generate-batch", response_model=BillingRunOut, status_code=202)
def generate_batch(
    body: GenerateBatchRequest,
    db: Session = Depends(get_db),
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


@router.get("/runs/{run_id}", response_model=BillingRunOut)
def get_billing_run(
    run_id: int,
    db: Session = Depends(get_db),
) -> BillingRunOut:
    out = crud.get_billing_run_out(db, run_id)
    if out is None:
        raise HTTPException(status_code=404, detail=f"Billing run {run_id} not found")
    return out
