"""Notification service — scan-and-send outbox pattern.

Reads invoices and notification_outbox. Writes only to notification_outbox.
No frozen files are modified.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Account, Customer, Invoice, User
from app.notifications.models import (
    NotificationChannel,
    NotificationOutbox,
    NotificationStatus,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Recipient resolution
# ---------------------------------------------------------------------------

def resolve_recipient(
    invoice: Invoice,
    channel: NotificationChannel,
    db: Session,
) -> Optional[str]:
    """Return the recipient string for *channel*, or None if unresolvable.

    EMAIL  → users.email  (via invoice→account→customer→user)
    SMS    → accounts.telephone_number  (via invoice→account)
    """
    account: Optional[Account] = db.get(Account, invoice.account_id)
    if account is None:
        return None

    if channel == NotificationChannel.SMS:
        return account.telephone_number or None

    # EMAIL path: account → customer → user
    if account.customer_id is None:
        return None
    customer: Optional[Customer] = db.get(Customer, account.customer_id)
    if customer is None or customer.user_id is None:
        return None
    user: Optional[User] = db.get(User, customer.user_id)
    if user is None:
        return None
    return user.email or None


# ---------------------------------------------------------------------------
# Enqueue
# ---------------------------------------------------------------------------

def enqueue_pending(db: Session) -> int:
    """Insert QUEUED outbox rows for invoices that have no row yet for a channel.

    Returns the number of rows inserted (including FAILED "no X on file" rows).
    Idempotency is enforced by the (invoice_id, channel) unique constraint —
    IntegrityError on duplicate is silently skipped.
    """
    # Find invoice IDs that are missing an EMAIL outbox row
    existing_email_ids = db.scalars(
        select(NotificationOutbox.invoice_id).where(
            NotificationOutbox.channel == NotificationChannel.EMAIL
        )
    ).all()

    invoices = db.scalars(
        select(Invoice).where(Invoice.id.notin_(existing_email_ids))
    ).all()

    inserted = 0

    for inv in invoices:
        email = resolve_recipient(inv, NotificationChannel.EMAIL, db)
        row = NotificationOutbox(
            invoice_id=inv.id,
            channel=NotificationChannel.EMAIL,
            recipient=email or "",
            status=NotificationStatus.QUEUED if email else NotificationStatus.FAILED,
            last_error=None if email else "no email on file",
        )
        try:
            db.add(row)
            db.flush()
            inserted += 1
            log.info("outbox enqueue EMAIL invoice_id=%d status=%s", inv.id, row.status.value)
        except IntegrityError:
            db.rollback()
            log.debug("outbox EMAIL invoice_id=%d already exists, skipped", inv.id)

    # SMS: only when SMS backend is not console (i.e. actually configured)
    sms_enabled = settings.sms_backend.lower() != "console"
    if sms_enabled:
        existing_sms_ids = db.scalars(
            select(NotificationOutbox.invoice_id).where(
                NotificationOutbox.channel == NotificationChannel.SMS
            )
        ).all()

        sms_invoices = db.scalars(
            select(Invoice).where(Invoice.id.notin_(existing_sms_ids))
        ).all()

        for inv in sms_invoices:
            phone = resolve_recipient(inv, NotificationChannel.SMS, db)
            if phone is None:
                continue  # no phone → no SMS row at all (unlike email which always gets a row)
            row = NotificationOutbox(
                invoice_id=inv.id,
                channel=NotificationChannel.SMS,
                recipient=phone,
                status=NotificationStatus.QUEUED,
            )
            try:
                db.add(row)
                db.flush()
                inserted += 1
                log.info("outbox enqueue SMS invoice_id=%d", inv.id)
            except IntegrityError:
                db.rollback()
                log.debug("outbox SMS invoice_id=%d already exists, skipped", inv.id)

    db.commit()
    return inserted


# ---------------------------------------------------------------------------
# Send pending
# ---------------------------------------------------------------------------

def _get_sendable_rows(db: Session) -> list[NotificationOutbox]:
    """QUEUED rows + FAILED rows eligible for retry (not a permanent failure)."""
    rows = db.scalars(select(NotificationOutbox)).all()
    result = []
    for row in rows:
        if row.status == NotificationStatus.SENT:
            continue
        if row.status == NotificationStatus.FAILED:
            if row.last_error and "on file" in row.last_error:
                continue  # permanent — missing contact info
            if row.attempts >= settings.notify_max_attempts:
                continue  # dead-letter
        result.append(row)
    return result


def send_pending(db: Session) -> tuple[int, int]:
    """Send all sendable outbox rows. Returns (sent_count, failed_count)."""
    from app.notifications.templates.email_template import (
        render_email_subject,
        render_email_html,
        render_email_attachments,
    )
    from app.notifications.templates.sms_template import render_sms_body
    from app.notifications.senders.email import get_email_sender
    from app.notifications.senders.sms import get_sms_sender
    from app.auth.pdf_tokens import mint_pdf_token

    rows = _get_sendable_rows(db)
    sent = 0
    failed = 0

    for row in rows:
        invoice: Optional[Invoice] = db.get(Invoice, row.invoice_id)
        if invoice is None:
            log.error("outbox row %d references missing invoice %d", row.id, row.invoice_id)
            continue

        account: Optional[Account] = db.get(Account, invoice.account_id)
        if account is None:
            log.error("outbox row %d: account %d missing", row.id, invoice.account_id)
            continue

        try:
            if row.channel == NotificationChannel.EMAIL:
                customer: Optional[Customer] = (
                    db.get(Customer, account.customer_id)
                    if account.customer_id else None
                )
                subject = render_email_subject(invoice, account)
                html    = render_email_html(invoice, account, customer)

                signed_link: Optional[str] = None
                if settings.email_use_signed_link:
                    signed_link = mint_pdf_token(invoice.id)

                attachments, inline_link = render_email_attachments(invoice, signed_link)

                if inline_link:
                    html = html.replace(
                        "</body>",
                        f"<p><a href='{inline_link}'>Download your bill PDF</a></p></body>",
                    )

                sender = get_email_sender()
                ref = sender.send(
                    to=row.recipient,
                    subject=subject,
                    html=html,
                    attachments=attachments,
                )

            else:  # SMS
                body = render_sms_body(invoice, account)
                sender = get_sms_sender()
                ref = sender.send(to=row.recipient, body=body)

            row.status       = NotificationStatus.SENT
            row.provider_ref = ref
            row.sent_at      = datetime.now(tz=timezone.utc)
            db.flush()
            sent += 1
            log.info(
                "outbox SENT invoice_id=%d channel=%s ref=%s",
                row.invoice_id, row.channel.value, ref,
            )

        except Exception as exc:
            short_error = str(exc)[:200]
            row.attempts   += 1
            row.status      = NotificationStatus.FAILED
            row.last_error  = short_error
            db.flush()
            failed += 1
            log.error(
                "outbox FAILED invoice_id=%d channel=%s attempts=%d error=%r",
                row.invoice_id, row.channel.value, row.attempts, short_error,
            )

    db.commit()
    return sent, failed


# ---------------------------------------------------------------------------
# scan_and_send
# ---------------------------------------------------------------------------

def scan_and_send(db: Session) -> dict:
    """Enqueue new invoices then send all pending rows.

    Returns {"queued": int, "sent": int, "failed": int}.
    """
    queued = enqueue_pending(db)
    sent, failed = send_pending(db)
    return {"queued": queued, "sent": sent, "failed": failed}
