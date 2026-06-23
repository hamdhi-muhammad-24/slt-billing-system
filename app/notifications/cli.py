"""
app/notifications/cli.py — Notification CLI (Phase 5).

Usage:
    python -m app.notifications.cli send-pending
"""
from __future__ import annotations

import typer

from app.core.logging import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.callback()
def _callback() -> None:
    """SLT Notifications CLI."""


@app.command("send-pending")
def send_pending() -> None:
    """Enqueue unnotified invoices then send all pending notifications.

    Idempotent: running twice sends nothing the second time.
    """
    from app.db.base import SessionLocal
    from app.notifications.service import scan_and_send

    db = SessionLocal()
    try:
        result = scan_and_send(db)
    except Exception as exc:
        log.exception("send-pending failed")
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
    finally:
        db.close()

    typer.echo(
        f"Done: queued={result['queued']} sent={result['sent']} failed={result['failed']}"
    )
    if result["failed"]:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
