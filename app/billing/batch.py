"""
Framework-independent batch billing service.

Called by the API, CLI, Celery tasks, and tests. This module owns the shared
bulk-run behavior: active template selection, PDF rendering, run-item status
tracking, optional delivery, and manual retry.
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


def _parse_period(period: str) -> datetime:
    try:
        return datetime.strptime(period, "%Y-%m")
    except ValueError:
        raise ValueError(f"--period {period!r} must be YYYY-MM (e.g. 2026-06)")


def _template_metadata(template) -> dict[str, str | None] | None:
    if template is None:
        return None
    return {
        "name": template.name,
        "template_code": template.template_code,
        "header_message": template.header_message,
        "footer_message": template.footer_message,
        "promotion_message": template.promotion_message,
        "theme_name": template.theme_name,
        "theme_color": template.theme_color,
    }


def _resolve_output_dir(output_dir: Path | None) -> Path:
    resolved = output_dir or Path(settings.output_dir)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _set_delivery_overall(item) -> None:
    from app.db.models import BillingRunItemOverallStatus

    def value(status) -> str:
        return status.value if hasattr(status, "value") else str(status)

    email_value = value(item.email_status)
    sms_value = value(item.sms_status)
    failures = []
    if email_value == "FAILED":
        failures.append(item.email_failure_reason or "Email delivery failed")
    if sms_value == "FAILED":
        failures.append(item.sms_failure_reason or "SMS delivery failed")
    if failures:
        item.overall_status = BillingRunItemOverallStatus.FAILED
        item.failure_reason = "; ".join(failures)[:1000]
    elif email_value == "PENDING" or sms_value == "PENDING":
        item.overall_status = BillingRunItemOverallStatus.READY_TO_SEND
    elif email_value == "NOT_ENABLED" and sms_value == "NOT_ENABLED":
        item.overall_status = BillingRunItemOverallStatus.GENERATED
        item.failure_reason = None
    else:
        item.overall_status = BillingRunItemOverallStatus.COMPLETED
        item.failure_reason = None


def deliver_run_item(
    item_id: int,
    *,
    session: Session,
    send_email: bool = True,
    send_sms: bool = True,
) -> None:
    from app.db.models import Account, BillingRunItem, Customer, DeliveryStatus, Invoice
    from app.notifications.senders.email import get_email_sender
    from app.notifications.senders.sms import get_sms_sender
    from app.notifications.templates.email_template import (
        render_email_attachments,
        render_email_html,
        render_email_subject,
    )
    from app.notifications.templates.sms_template import render_sms_body

    item = session.get(BillingRunItem, item_id)
    if item is None:
        raise ValueError(f"Billing run item {item_id} not found")
    invoice = session.get(Invoice, item.invoice_id) if item.invoice_id else None
    account = session.get(Account, item.account_id) if item.account_id else None
    customer = session.get(Customer, item.customer_id) if item.customer_id else None

    if invoice is None or account is None:
        item.email_status = DeliveryStatus.FAILED if send_email else DeliveryStatus.NOT_ENABLED
        item.sms_status = DeliveryStatus.FAILED if send_sms else DeliveryStatus.NOT_ENABLED
        reason = "Invoice or account missing for delivery"
        item.email_failure_reason = reason if send_email else None
        item.sms_failure_reason = reason if send_sms else None
        _set_delivery_overall(item)
        session.flush()
        return

    if send_email:
        item.email_status = DeliveryStatus.PENDING
        item.email_failure_reason = None
        item.email_provider_ref = None
        session.flush()
        try:
            recipient = customer.email if customer else None
            if not recipient:
                raise ValueError("Customer email missing")
            attachments, inline_link = render_email_attachments(invoice)
            html = render_email_html(invoice, account, customer)
            if inline_link:
                html = html.replace(
                    "</body>",
                    f"<p><a href='{inline_link}'>Download your bill PDF</a></p></body>",
                )
            ref = get_email_sender().send(
                to=recipient,
                subject=render_email_subject(invoice, account),
                html=html,
                attachments=attachments,
            )
            item.email_status = DeliveryStatus.SUCCESS
            item.email_provider_ref = ref
        except Exception as exc:
            item.email_status = DeliveryStatus.FAILED
            item.email_failure_reason = str(exc)[:500]
    else:
        item.email_status = DeliveryStatus.NOT_ENABLED
        item.email_failure_reason = None
        item.email_provider_ref = None

    if send_sms:
        item.sms_status = DeliveryStatus.PENDING
        item.sms_failure_reason = None
        item.sms_provider_ref = None
        session.flush()
        try:
            recipient = (customer.mobile_number if customer else None) or account.telephone_number
            if not recipient:
                raise ValueError("Customer phone number missing")
            ref = get_sms_sender().send(to=recipient, body=render_sms_body(invoice, account))
            item.sms_status = DeliveryStatus.SUCCESS
            item.sms_provider_ref = ref
        except Exception as exc:
            item.sms_status = DeliveryStatus.FAILED
            item.sms_failure_reason = str(exc)[:500]
    else:
        item.sms_status = DeliveryStatus.NOT_ENABLED
        item.sms_failure_reason = None
        item.sms_provider_ref = None

    _set_delivery_overall(item)
    session.flush()


def send_billing_run_notifications(
    run_id: int,
    *,
    session: Optional[Session] = None,
    send_email: bool = True,
    send_sms: bool = True,
) -> dict:
    from app.db.base import SessionLocal
    from app.db.models import BillingRunItem, PdfGenerationStatus

    own_session = session is None
    if own_session:
        session = SessionLocal()

    assert session is not None
    try:
        items = session.query(BillingRunItem).filter(
            BillingRunItem.billing_run_id == run_id,
            BillingRunItem.pdf_status == PdfGenerationStatus.SUCCESS,
        ).order_by(BillingRunItem.id).all()

        for item in items:
            deliver_run_item(item.id, session=session, send_email=send_email, send_sms=send_sms)

        if own_session:
            session.commit()
        return {"run_id": run_id, "processed": len(items)}
    except Exception:
        if own_session:
            session.rollback()
        raise
    finally:
        if own_session:
            session.close()


def run_billing_batch(
    period: str,
    output_dir: Path | None = None,
    session: Optional[Session] = None,
    account_ids: list[int] | None = None,
    send_notifications: bool = False,
    send_email: bool = True,
    send_sms: bool = True,
) -> dict:
    """Run the monthly billing batch for *period* (YYYY-MM)."""
    dt = _parse_period(period)
    output_dir = _resolve_output_dir(output_dir)

    from app.db.base import SessionLocal
    from app.billing import engine as billing_engine, repository
    from app.pdf.renderer import render_bill

    own_session = session is None
    if own_session:
        session = SessionLocal()

    assert session is not None
    try:
        all_invoices = repository.list_invoices_for_billing_month(dt.year, dt.month, session)
        if account_ids is not None:
            id_set = set(account_ids)
            invoices = [inv for inv in all_invoices if inv.account_id in id_set]
        else:
            invoices = all_invoices

        if not invoices:
            return {"period": period, "run_id": None, "succeeded": 0, "failed": 0, "invoices": 0}

        active_template = repository.get_active_invoice_template(session)
        template_id = active_template.id if active_template is not None else None
        template_metadata = _template_metadata(active_template)
        run_period_start = date(dt.year, dt.month, 1)
        run_period_end = date(dt.year, dt.month, monthrange(dt.year, dt.month)[1])

        run_id = repository.create_billing_run(
            run_period_start,
            run_period_end,
            len(invoices),
            session,
            template_id=template_id,
        )

        succeeded = 0
        failed = 0

        for inv in invoices:
            item_id = repository.create_run_item(run_id, inv, template_id, session)
            sp = session.begin_nested()
            try:
                pdf_matches_template = template_id is None or inv.template_id == template_id
                pdf_exists = bool(inv.pdf_path and Path(inv.pdf_path).exists())

                if inv.inv_status == "GENERATED" and pdf_exists and pdf_matches_template:
                    repository.mark_run_item_success(item_id, inv.inv_id, template_id, session)
                    if send_notifications:
                        deliver_run_item(item_id, session=session, send_email=send_email, send_sms=send_sms)
                    succeeded += 1
                    sp.commit()
                    continue

                bill = billing_engine.build_bill(session, inv.account_number, inv.period_start, inv.period_end)
                safe = inv.account_number.replace(" ", "-")
                template_suffix = active_template.template_code if active_template is not None else "default"
                out_path = str(output_dir / f"{safe}_{inv.period_start}_{inv.period_end}_{template_suffix}.pdf")
                render_bill(bill, out_path, template_metadata=template_metadata)

                repository.update_invoice_status(inv.inv_id, "GENERATED", session)
                repository.update_invoice_pdf_path(inv.inv_id, out_path, session)
                repository.update_invoice_template_id(inv.inv_id, template_id, session)
                repository.mark_run_item_success(item_id, inv.inv_id, template_id, session)
                if send_notifications:
                    deliver_run_item(item_id, session=session, send_email=send_email, send_sms=send_sms)
                sp.commit()
                succeeded += 1
                log.info("  [OK]   %s -> %s", inv.account_number, out_path)

            except Exception as exc:
                sp.rollback()
                failed += 1
                log.error("  [FAIL] %s: %s", inv.account_number, exc)
                sp2 = session.begin_nested()
                try:
                    repository.mark_run_item_failed(item_id, str(exc), session)
                    repository.record_run_failure(run_id, inv.account_id, str(exc), session)
                    sp2.commit()
                except Exception:
                    sp2.rollback()

        repository.finish_billing_run(run_id, succeeded, failed, session)
        if own_session:
            session.commit()

        return {
            "period": period,
            "run_id": run_id,
            "succeeded": succeeded,
            "failed": failed,
            "invoices": len(invoices),
        }

    except Exception:
        if own_session:
            session.rollback()
        raise
    finally:
        if own_session:
            session.close()


def retry_billing_run_item(
    item_id: int,
    *,
    output_dir: Path | None = None,
    session: Optional[Session] = None,
    send_notifications: bool = True,
    send_email: bool = True,
    send_sms: bool = True,
) -> dict:
    from app.db.base import SessionLocal
    from app.billing import engine as billing_engine, repository
    from app.db.models import Account, BillingRun, BillingRunItem, Invoice, InvoiceTemplate
    from app.pdf.renderer import render_bill

    output_dir = _resolve_output_dir(output_dir)
    own_session = session is None
    if own_session:
        session = SessionLocal()

    assert session is not None
    try:
        item = session.get(BillingRunItem, item_id)
        if item is None:
            raise ValueError(f"Billing run item {item_id} not found")
        invoice = session.get(Invoice, item.invoice_id) if item.invoice_id else None
        account = session.get(Account, item.account_id) if item.account_id else None
        run = session.get(BillingRun, item.billing_run_id)
        if invoice is None or account is None or run is None:
            raise ValueError("Billing run item is missing invoice, account, or run data")

        template_id = item.template_id or run.template_id
        template = session.get(InvoiceTemplate, template_id) if template_id else repository.get_active_invoice_template(session)
        template_id = template.id if template is not None else None
        template_metadata = _template_metadata(template)

        sp = session.begin_nested()
        try:
            bill = billing_engine.build_bill(session, account.account_number, invoice.period_start, invoice.period_end)
            safe = account.account_number.replace(" ", "-")
            template_suffix = template.template_code if template is not None else "default"
            out_path = str(output_dir / f"{safe}_{invoice.period_start}_{invoice.period_end}_{template_suffix}.pdf")
            render_bill(bill, out_path, template_metadata=template_metadata)
            repository.update_invoice_status(invoice.id, "GENERATED", session)
            repository.update_invoice_pdf_path(invoice.id, out_path, session)
            repository.update_invoice_template_id(invoice.id, template_id, session)
            repository.mark_run_item_success(item.id, invoice.id, template_id, session)
            if send_notifications:
                deliver_run_item(item.id, session=session, send_email=send_email, send_sms=send_sms)
            sp.commit()
        except Exception as exc:
            sp.rollback()
            repository.mark_run_item_failed(item.id, str(exc), session)
            repository.record_run_failure(item.billing_run_id, item.account_id, str(exc), session)

        if own_session:
            session.commit()
        return {"run_id": item.billing_run_id, "item_id": item.id}
    except Exception:
        if own_session:
            session.rollback()
        raise
    finally:
        if own_session:
            session.close()
