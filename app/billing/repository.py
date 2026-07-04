"""
The ONLY file that contains SQL for the billing engine.

Swapping to SLT's real database later = rewriting only this file.
All functions return plain dataclasses — no SQLAlchemy types leak out.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy import update as sa_update
from sqlalchemy.orm import Session

from app.db.models import (
    Account,
    AccountStatus,
    BillingRunItem,
    BillingRunItemOverallStatus,
    BillingRun,
    BillingRunFailure,
    Customer,
    DeliveryStatus,
    Invoice,
    InvoiceLineItem,
    InvoiceTemplate,
    Payment,
    PdfGenerationStatus,
    RunStatus,
    ServiceAccount,
    UsageRecord,
)


# ---------------------------------------------------------------------------
# Row types — plain data, safe to pass to the engine / tests / renderer
# ---------------------------------------------------------------------------

@dataclass
class ServiceAccountRow:
    id:             int
    service_number: str
    service_type:   str    # string value, e.g. "BROADBAND"
    label:          str | None


@dataclass
class LineItemRow:
    service_account_id: int | None
    service_number:     str | None   # None for global lines (TAX, FEE, …)
    service_type:       str | None
    line_type:          str          # e.g. "RENTAL", "TAX", "DISCOUNT"
    description:        str
    period_start:       date | None
    period_end:         date | None
    amount:             Decimal
    sort_order:         int


@dataclass
class PaymentRow:
    payment_date: date
    method:       str
    amount:       Decimal
    reference:    str | None


@dataclass
class UsageRecordRow:
    service_number: str
    service_type:   str
    event_time:     datetime | None
    description:    str | None
    charge:         Decimal


@dataclass
class BillInputs:
    # From accounts + customers
    account_number:   str
    telephone_number: str | None
    service_label:    str | None
    customer_name:    str
    address_line1:    str | None
    address_line2:    str | None
    city:             str | None
    postal_code:      str | None
    # From invoices (stored snapshot carries the pre-computed balance_bf)
    invoice_number: str
    billing_date:   date
    period_start:   date
    period_end:     date
    due_date:       date
    balance_bf:     Decimal
    # Nested rows
    service_accounts: list[ServiceAccountRow]
    line_items:       list[LineItemRow]
    payments:         list[PaymentRow]
    usage_records:    list[UsageRecordRow] = field(default_factory=list)
    customer_type:    str = "RESIDENTIAL"


# ---------------------------------------------------------------------------
# Public query
# ---------------------------------------------------------------------------

def get_bill_inputs(
    account_number: str,
    period_start: date,
    period_end: date,
    session: Session,
) -> BillInputs:
    """
    Fetch everything the engine needs for one bill.
    Raises ValueError for unknown accounts or missing invoices.
    """

    # ── 1. Account + Customer ─────────────────────────────────────────────
    acct_row = session.execute(
        select(
            Account.id,
            Account.account_number,
            Account.telephone_number,
            Account.service_label,
            Customer.full_name,
            Customer.customer_type,
            Customer.address_line1,
            Customer.address_line2,
            Customer.city,
            Customer.postal_code,
        )
        .join(Customer, Account.customer_id == Customer.id)
        .where(Account.account_number == account_number)
    ).one_or_none()

    if acct_row is None:
        raise ValueError(f"Account not found: {account_number!r}")

    account_id = acct_row.id

    # ── 2. Service sub-accounts (ordered for consistent PDF grouping) ─────
    svc_rows = session.execute(
        select(
            ServiceAccount.id,
            ServiceAccount.service_number,
            ServiceAccount.service_type,
            ServiceAccount.label,
        )
        .where(ServiceAccount.account_id == account_id)
        .order_by(ServiceAccount.id)
    ).all()

    service_accounts = [
        ServiceAccountRow(
            id=r.id,
            service_number=r.service_number,
            service_type=r.service_type.value,   # ServiceType enum → str
            label=r.label,
        )
        for r in svc_rows
    ]

    # ── 3. Invoice for this period ────────────────────────────────────────
    inv_row = session.execute(
        select(
            Invoice.id,
            Invoice.invoice_number,
            Invoice.billing_date,
            Invoice.period_start,
            Invoice.period_end,
            Invoice.due_date,
            Invoice.balance_bf,
        )
        .where(
            Invoice.account_id == account_id,
            Invoice.period_start == period_start,
            Invoice.period_end == period_end,
        )
    ).one_or_none()

    if inv_row is None:
        raise ValueError(
            f"No invoice for {account_number!r} "
            f"in period {period_start}–{period_end}"
        )

    # ── 4. Line items (LEFT JOIN to resolve service_number) ───────────────
    line_rows = session.execute(
        select(
            InvoiceLineItem.service_account_id,
            ServiceAccount.service_number,
            ServiceAccount.service_type,
            InvoiceLineItem.line_type,
            InvoiceLineItem.description,
            InvoiceLineItem.period_start,
            InvoiceLineItem.period_end,
            InvoiceLineItem.amount,
            InvoiceLineItem.sort_order,
        )
        .outerjoin(
            ServiceAccount,
            InvoiceLineItem.service_account_id == ServiceAccount.id,
        )
        .where(InvoiceLineItem.invoice_id == inv_row.id)
        .order_by(InvoiceLineItem.sort_order, InvoiceLineItem.id)
    ).all()

    line_items = [
        LineItemRow(
            service_account_id=r.service_account_id,
            service_number=r.service_number,
            service_type=r.service_type.value if r.service_type is not None else None,
            line_type=r.line_type.value,          # LineType enum → str
            description=r.description,
            period_start=r.period_start,
            period_end=r.period_end,
            amount=r.amount,                       # Numeric(12,2) → Decimal
            sort_order=r.sort_order,
        )
        for r in line_rows
    ]

    # ── 5. Payments whose payment_date falls within the billing period ─────
    pmt_rows = session.execute(
        select(
            Payment.payment_date,
            Payment.method,
            Payment.amount,
            Payment.reference,
        )
        .where(
            Payment.account_id == account_id,
            Payment.payment_date >= period_start,
            Payment.payment_date <= period_end,
        )
        .order_by(Payment.payment_date)
    ).all()

    payments = [
        PaymentRow(
            payment_date=r.payment_date,
            method=r.method.value,                 # PaymentMethod enum → str
            amount=r.amount,
            reference=r.reference,
        )
        for r in pmt_rows
    ]

    # ── 6. Optional usage detail for the lower-right invoice table ─────────
    svc_ids = [svc.id for svc in service_accounts]
    usage_records: list[UsageRecordRow] = []
    if svc_ids:
        usage_rows = session.execute(
            select(
                ServiceAccount.service_number,
                ServiceAccount.service_type,
                UsageRecord.event_time,
                UsageRecord.description,
                UsageRecord.charge,
            )
            .join(ServiceAccount, UsageRecord.service_account_id == ServiceAccount.id)
            .where(
                UsageRecord.service_account_id.in_(svc_ids),
                UsageRecord.period_start == period_start,
                UsageRecord.period_end == period_end,
            )
            .order_by(UsageRecord.event_time, UsageRecord.id)
        ).all()

        usage_records = [
            UsageRecordRow(
                service_number=r.service_number,
                service_type=r.service_type.value,
                event_time=r.event_time,
                description=r.description,
                charge=r.charge or Decimal("0.00"),
            )
            for r in usage_rows
        ]

    return BillInputs(
        account_number=acct_row.account_number,
        telephone_number=acct_row.telephone_number,
        service_label=acct_row.service_label,
        customer_name=acct_row.full_name,
        customer_type=acct_row.customer_type.value if acct_row.customer_type else "RESIDENTIAL",
        address_line1=acct_row.address_line1,
        address_line2=acct_row.address_line2,
        city=acct_row.city,
        postal_code=acct_row.postal_code,
        invoice_number=inv_row.invoice_number,
        billing_date=inv_row.billing_date,
        period_start=inv_row.period_start,
        period_end=inv_row.period_end,
        due_date=inv_row.due_date,
        balance_bf=inv_row.balance_bf,
        service_accounts=service_accounts,
        line_items=line_items,
        payments=payments,
        usage_records=usage_records,
    )


def find_invoice_period(
    account_number: str,
    billing_year: int,
    billing_month: int,
    session: Session,
) -> tuple[int, date, date]:
    """Return (invoice_id, period_start, period_end) for the invoice billed in billing_year/month.

    Raises ValueError when no matching invoice is found.
    """
    row = session.execute(
        select(Invoice.id, Invoice.period_start, Invoice.period_end)
        .join(Account, Invoice.account_id == Account.id)
        .where(
            Account.account_number == account_number,
            extract("year",  Invoice.billing_date) == billing_year,
            extract("month", Invoice.billing_date) == billing_month,
        )
    ).one_or_none()

    if row is None:
        raise ValueError(
            f"No invoice for {account_number!r} billed in "
            f"{billing_year:04d}-{billing_month:02d}"
        )
    return row.id, row.period_start, row.period_end


def update_invoice_status(invoice_id: int, status: str, session: Session) -> None:
    """Set invoices.status for a single invoice (caller must commit)."""
    session.execute(
        sa_update(Invoice).where(Invoice.id == invoice_id).values(status=status)
    )


def update_invoice_pdf_path(invoice_id: int, pdf_path: str, session: Session) -> None:
    """Record the rendered PDF path on the invoice row (caller must commit)."""
    session.execute(
        sa_update(Invoice).where(Invoice.id == invoice_id).values(pdf_path=pdf_path)
    )


# ---------------------------------------------------------------------------
# Batch-run queries
# ---------------------------------------------------------------------------

@dataclass
class InvoiceForRun:
    inv_id:         int
    period_start:   date
    period_end:     date
    inv_status:     str          # InvoiceStatus enum value
    pdf_path:       str | None
    template_id:    int | None
    account_id:     int
    customer_id:    int
    account_number: str


def list_invoices_for_billing_month(
    year: int, month: int, session: Session
) -> list[InvoiceForRun]:
    """Return one row per ACTIVE account that has an invoice billed in year/month."""
    rows = session.execute(
        select(
            Invoice.id.label("inv_id"),
            Invoice.period_start,
            Invoice.period_end,
            Invoice.status,
            Invoice.pdf_path,
            Invoice.template_id,
            Account.id.label("account_id"),
            Account.customer_id,
            Account.account_number,
        )
        .join(Account, Invoice.account_id == Account.id)
        .where(
            Account.status == AccountStatus.ACTIVE,
            extract("year",  Invoice.billing_date) == year,
            extract("month", Invoice.billing_date) == month,
        )
        .order_by(Account.account_number)
    ).all()
    return [
        InvoiceForRun(
            inv_id=r.inv_id,
            period_start=r.period_start,
            period_end=r.period_end,
            inv_status=r.status.value,
            pdf_path=r.pdf_path,
            template_id=r.template_id,
            account_id=r.account_id,
            customer_id=r.customer_id,
            account_number=r.account_number,
        )
        for r in rows
    ]


def create_billing_run(
    period_start: date,
    period_end: date,
    total_accounts: int,
    session: Session,
    template_id: int | None = None,
) -> int:
    """Insert a RUNNING billing_run row; flush to get the id (caller must commit)."""
    run = BillingRun(
        template_id=template_id,
        period_start=period_start,
        period_end=period_end,
        status=RunStatus.RUNNING,
        total_accounts=total_accounts,
        succeeded=0,
        failed=0,
    )
    session.add(run)
    session.flush()
    return run.id


def record_run_failure(
    run_id: int,
    account_id: int | None,
    error_message: str,
    session: Session,
) -> None:
    """Append a failure row for one account in this billing run."""
    session.add(BillingRunFailure(
        billing_run_id=run_id,
        account_id=account_id,
        error_message=error_message,
    ))


def get_active_invoice_template(session: Session) -> InvoiceTemplate | None:
    return session.scalar(
        select(InvoiceTemplate)
        .where(InvoiceTemplate.is_active.is_(True))
        .order_by(InvoiceTemplate.id)
        .limit(1)
    )


def get_invoice_template(template_id: int, session: Session) -> InvoiceTemplate | None:
    return session.get(InvoiceTemplate, template_id)


def create_run_item(
    run_id: int,
    invoice: InvoiceForRun,
    template_id: int | None,
    session: Session,
) -> int:
    item = BillingRunItem(
        billing_run_id=run_id,
        account_id=invoice.account_id,
        customer_id=invoice.customer_id,
        invoice_id=invoice.inv_id,
        template_id=template_id,
        pdf_status=PdfGenerationStatus.PENDING,
        email_status=DeliveryStatus.NOT_ENABLED,
        sms_status=DeliveryStatus.NOT_ENABLED,
        overall_status=BillingRunItemOverallStatus.PENDING,
        retry_count=0,
    )
    session.add(item)
    session.flush()
    return item.id


def mark_run_item_success(
    item_id: int,
    invoice_id: int,
    template_id: int | None,
    session: Session,
) -> None:
    item = session.get(BillingRunItem, item_id)
    if item is None:
        return
    item.invoice_id = invoice_id
    item.template_id = template_id
    item.pdf_status = PdfGenerationStatus.SUCCESS
    item.email_status = DeliveryStatus.NOT_ENABLED
    item.sms_status = DeliveryStatus.NOT_ENABLED
    item.overall_status = BillingRunItemOverallStatus.GENERATED
    item.failure_reason = None
    item.email_failure_reason = None
    item.sms_failure_reason = None
    item.email_provider_ref = None
    item.sms_provider_ref = None
    item.updated_at = func.now()
    session.flush()


def mark_run_item_failed(
    item_id: int,
    error_message: str,
    session: Session,
) -> None:
    item = session.get(BillingRunItem, item_id)
    if item is None:
        return
    item.pdf_status = PdfGenerationStatus.FAILED
    item.email_status = DeliveryStatus.NOT_ENABLED
    item.sms_status = DeliveryStatus.NOT_ENABLED
    item.overall_status = BillingRunItemOverallStatus.FAILED
    item.failure_reason = error_message[:1000]
    item.email_provider_ref = None
    item.sms_provider_ref = None
    item.retry_count = (item.retry_count or 0) + 1
    item.updated_at = func.now()
    session.flush()


def update_invoice_template_id(
    invoice_id: int,
    template_id: int | None,
    session: Session,
) -> None:
    session.execute(
        sa_update(Invoice).where(Invoice.id == invoice_id).values(template_id=template_id)
    )


def finish_billing_run(
    run_id: int,
    succeeded: int,
    failed: int,
    session: Session,
) -> None:
    """Update the billing_run row with final counts and status (caller must commit)."""
    if failed == 0:
        final_status = RunStatus.DONE
    elif succeeded > 0:
        final_status = RunStatus.PARTIAL
    else:
        final_status = RunStatus.FAILED

    session.execute(
        sa_update(BillingRun)
        .where(BillingRun.id == run_id)
        .values(
            status=final_status,
            succeeded=succeeded,
            failed=failed,
            finished_at=func.now(),
        )
    )
