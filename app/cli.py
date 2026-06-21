"""
app/cli.py — SLT E-Bill command-line interface (Phase 0).

Usage:
    python -m app.cli generate-one   --account "004 152 4075" --period 2024-02
    python -m app.cli generate-batch --period 2024-02
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from pathlib import Path

import typer

from app.core.logging import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.callback()
def _callback() -> None:
    """SLT E-Bill CLI."""


@app.command("generate-one")
def generate_one(
    account: str = typer.Option(
        ..., "--account", help="Account number, e.g. '004 152 4075'"
    ),
    period: str = typer.Option(
        ..., "--period", help="Billing month as YYYY-MM, e.g. 2024-02"
    ),
    output_dir: Path = typer.Option(
        Path("output"), "--output-dir", help="Directory to write the PDF"
    ),
) -> None:
    """Generate one PDF bill (DB -> engine -> PDF) and mark the invoice as GENERATED."""

    # ── Parse --period ────────────────────────────────────────────────────────
    try:
        dt = datetime.strptime(period, "%Y-%m")
    except ValueError:
        typer.echo(f"Error: --period {period!r} must be YYYY-MM (e.g. 2024-02)", err=True)
        raise typer.Exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Lazy imports (keep startup fast; avoid circular issues at module level) ─
    from app.db.base import SessionLocal
    from app.billing import engine as billing_engine, repository
    from app.pdf.renderer import render_bill

    session = SessionLocal()
    try:
        # 1. Resolve billing month → exact period dates stored on the invoice
        try:
            inv_id, period_start, period_end = repository.find_invoice_period(
                account, dt.year, dt.month, session
            )
        except ValueError as exc:
            typer.echo(f"Error: {exc}", err=True)
            raise typer.Exit(1)

        log.info(
            "Generating bill for %r  period %s – %s  (invoice id=%d)",
            account, period_start, period_end, inv_id,
        )

        # 2. Run the billing engine (pure: fetches rows, assembles Bill)
        bill = billing_engine.build_bill(session, account, period_start, period_end)

        # 3. Render to PDF
        safe = account.replace(" ", "-")
        out_path = str(output_dir / f"{safe}_{period_start}_{period_end}.pdf")
        render_bill(bill, out_path)
        log.info("PDF written: %s", out_path)

        # 4. Persist: mark invoice as GENERATED
        repository.update_invoice_status(inv_id, "GENERATED", session)
        session.commit()
        log.info("Invoice %d marked GENERATED", inv_id)

    except typer.Exit:
        raise
    except Exception as exc:
        session.rollback()
        log.exception("generate-one failed")
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
    finally:
        session.close()

    typer.echo(f"Done: {out_path}")


@app.command("generate-batch")
def generate_batch(
    period: str = typer.Option(
        ..., "--period", help="Billing month as YYYY-MM, e.g. 2024-02"
    ),
    output_dir: Path = typer.Option(
        Path("output"), "--output-dir", help="Directory to write PDFs"
    ),
) -> None:
    """Generate PDF bills for all active accounts billed in a month.

    Per-account failures are recorded in billing_run_failures and do NOT stop
    the run. Re-running is safe: accounts whose PDF already exists are skipped.
    """
    try:
        dt = datetime.strptime(period, "%Y-%m")
    except ValueError:
        typer.echo(f"Error: --period {period!r} must be YYYY-MM (e.g. 2024-02)", err=True)
        raise typer.Exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    from app.db.base import SessionLocal
    from app.billing import engine as billing_engine, repository
    from app.pdf.renderer import render_bill

    session = SessionLocal()
    try:
        invoices = repository.list_invoices_for_billing_month(dt.year, dt.month, session)

        if not invoices:
            typer.echo(f"No active-account invoices found for {period}.")
            raise typer.Exit(0)

        # billing_run period covers the whole calendar month
        run_period_start = date(dt.year, dt.month, 1)
        run_period_end   = date(dt.year, dt.month, monthrange(dt.year, dt.month)[1])

        run_id = repository.create_billing_run(
            run_period_start, run_period_end, len(invoices), session
        )
        # flush so run_id is available for failure rows, but don't commit yet
        session.flush()

        log.info(
            "Batch run %d started: %d accounts, billing month %s",
            run_id, len(invoices), period,
        )

        succeeded = 0
        failed    = 0

        for inv in invoices:
            sp = session.begin_nested()   # savepoint — isolates per-account failure
            try:
                # Idempotency: skip accounts whose PDF was already written
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

                # Record the failure in a fresh savepoint (outer tx is still live)
                sp2 = session.begin_nested()
                try:
                    repository.record_run_failure(run_id, inv.account_id, str(exc), session)
                    sp2.commit()
                except Exception:
                    sp2.rollback()

        repository.finish_billing_run(run_id, succeeded, failed, session)
        session.commit()

        typer.echo(f"Batch run {run_id} complete: {succeeded} OK, {failed} failed.")
        if failed:
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as exc:
        session.rollback()
        log.exception("generate-batch failed")
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    app()
