"""
app/billing/batch.py — Framework-independent batch billing service.

Called by the CLI, Celery tasks, or tests — no Typer/FastAPI imports.
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger

log = get_logger(__name__)


def run_billing_batch(
    period: str,
    output_dir: Path = Path("output"),
    session: Optional[Session] = None,
) -> dict:
    """Run the monthly billing batch for *period* (YYYY-MM).

    Raises ValueError on bad period format.
    Returns {"period", "run_id", "succeeded", "failed", "invoices"}.
    Manages its own DB session when none is passed.
    """
    try:
        dt = datetime.strptime(period, "%Y-%m")
    except ValueError:
        raise ValueError(f"--period {period!r} must be YYYY-MM (e.g. 2024-02)")

    output_dir.mkdir(parents=True, exist_ok=True)

    from app.db.base import SessionLocal
    from app.billing import engine as billing_engine, repository
    from app.pdf.renderer import render_bill

    own_session = session is None
    if own_session:
        session = SessionLocal()

    try:
        invoices = repository.list_invoices_for_billing_month(dt.year, dt.month, session)

        if not invoices:
            return {"period": period, "run_id": None, "succeeded": 0, "failed": 0, "invoices": 0}

        run_period_start = date(dt.year, dt.month, 1)
        run_period_end   = date(dt.year, dt.month, monthrange(dt.year, dt.month)[1])

        run_id = repository.create_billing_run(
            run_period_start, run_period_end, len(invoices), session
        )
        session.flush()

        log.info(
            "Batch run %d started: %d accounts, billing month %s",
            run_id, len(invoices), period,
        )

        succeeded = 0
        failed    = 0

        for inv in invoices:
            sp = session.begin_nested()
            try:
                if inv.inv_status == "GENERATED" and inv.pdf_path and Path(inv.pdf_path).exists():
                    log.info("  [SKIP] %s — already generated", inv.account_number)
                    succeeded += 1
                    sp.commit()
                    continue

                bill = billing_engine.build_bill(
                    session, inv.account_number, inv.period_start, inv.period_end
                )
                safe     = inv.account_number.replace(" ", "-")
                out_path = str(output_dir / f"{safe}_{inv.period_start}_{inv.period_end}.pdf")
                render_bill(bill, out_path)

                repository.update_invoice_status(inv.inv_id, "GENERATED", session)
                repository.update_invoice_pdf_path(inv.inv_id, out_path, session)
                sp.commit()

                succeeded += 1
                log.info("  [OK]   %s -> %s", inv.account_number, out_path)

            except Exception as exc:
                sp.rollback()
                failed += 1
                log.error("  [FAIL] %s: %s", inv.account_number, exc)

                sp2 = session.begin_nested()
                try:
                    repository.record_run_failure(run_id, inv.account_id, str(exc), session)
                    sp2.commit()
                except Exception:
                    sp2.rollback()

        repository.finish_billing_run(run_id, succeeded, failed, session)
        session.commit()

        log.info("Batch run %d complete: %d OK, %d failed.", run_id, succeeded, failed)
        return {
            "period":    period,
            "run_id":    run_id,
            "succeeded": succeeded,
            "failed":    failed,
            "invoices":  len(invoices),
        }

    except Exception:
        session.rollback()
        raise
    finally:
        if own_session:
            session.close()
