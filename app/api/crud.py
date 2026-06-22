"""
Read-only database queries for the API layer.

All SQL for the API lives here. The billing engine's repository
(app/billing/repository.py) covers engine-specific reads/writes and is
kept separate so it can be swapped to SLT's real DB independently.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.db.models import (
    Account,
    BillingRun,
    BillingRunFailure,
    Customer,
    Invoice,
    InvoiceLineItem,
    Payment,
    ServiceAccount,
)
from app.api.schemas import (
    AccountOut,
    BillingRunFailureOut,
    BillingRunOut,
    CustomerOut,
    InvoiceLineItemOut,
    InvoiceOut,
    PaymentOut,
    ServiceAccountOut,
    ServiceAccountSummary,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _address(c: Customer) -> str | None:
    parts = [c.address_line1, c.address_line2, c.city, c.postal_code]
    filled = [p for p in parts if p]
    return ", ".join(filled) if filled else None


def _customer_out(c: Customer) -> CustomerOut:
    return CustomerOut(
        id=c.id,
        name=c.full_name,
        address=_address(c),
    )


def _account_out(a: Account) -> AccountOut:
    return AccountOut(
        id=a.id,
        customer_id=a.customer_id,
        account_no=a.account_number,
        status=a.status.value,
    )


def _build_invoice_out(
    inv: Invoice,
    service_accounts: list[ServiceAccountSummary],
    line_items: list[InvoiceLineItemOut],
) -> InvoiceOut:
    return InvoiceOut(
        id=inv.id,
        account_id=inv.account_id,
        period=inv.period_start.strftime("%Y-%m"),
        issue_date=inv.billing_date,
        due_date=inv.due_date,
        balance_bf=inv.balance_bf,
        payments_received=inv.payments_received,
        arrears=inv.balance_bf - inv.payments_received,
        charges_for_period=inv.charges_for_period,
        total_payable=inv.total_payable,
        service_accounts=service_accounts,
        line_items=line_items,
    )


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

def list_customers(
    db: Session, *, limit: int, offset: int
) -> tuple[list[CustomerOut], int]:
    total: int = db.scalar(select(func.count(Customer.id))) or 0
    rows = db.scalars(
        select(Customer).order_by(Customer.id).offset(offset).limit(limit)
    ).all()
    return [_customer_out(r) for r in rows], total


def get_customer(db: Session, customer_id: int) -> CustomerOut | None:
    c = db.get(Customer, customer_id)
    return _customer_out(c) if c is not None else None


def list_accounts_for_customer(
    db: Session, customer_id: int
) -> list[AccountOut]:
    rows = db.scalars(
        select(Account)
        .where(Account.customer_id == customer_id)
        .order_by(Account.id)
    ).all()
    return [_account_out(r) for r in rows]


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

def get_account(db: Session, account_id: int) -> AccountOut | None:
    a = db.get(Account, account_id)
    return _account_out(a) if a is not None else None


def list_service_accounts(
    db: Session, account_id: int
) -> list[ServiceAccountOut]:
    rows = db.scalars(
        select(ServiceAccount)
        .where(ServiceAccount.account_id == account_id)
        .order_by(ServiceAccount.id)
    ).all()
    return [
        ServiceAccountOut(
            id=r.id,
            account_id=r.account_id,
            service_type=r.service_type.value,
            identifier=r.service_number,
        )
        for r in rows
    ]


def list_invoices_for_account(
    db: Session, account_id: int, *, limit: int, offset: int
) -> tuple[list[InvoiceOut], int]:
    total: int = db.scalar(
        select(func.count(Invoice.id)).where(Invoice.account_id == account_id)
    ) or 0
    rows = db.scalars(
        select(Invoice)
        .where(Invoice.account_id == account_id)
        .order_by(Invoice.billing_date.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    # List view: omit line_items/service_accounts (use the detail endpoint)
    return [_build_invoice_out(r, [], []) for r in rows], total


def list_payments_for_account(
    db: Session, account_id: int
) -> list[PaymentOut]:
    rows = db.scalars(
        select(Payment)
        .where(Payment.account_id == account_id)
        .order_by(Payment.payment_date.desc())
    ).all()
    return [
        PaymentOut(
            id=r.id,
            account_id=r.account_id,
            amount=r.amount,
            paid_at=r.payment_date,
            method=r.method.value,
            reference=r.reference,
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------

def get_invoice(db: Session, invoice_id: int) -> InvoiceOut | None:
    inv = db.get(Invoice, invoice_id)
    if inv is None:
        return None

    # Fetch line items ordered for display
    li_rows = db.scalars(
        select(InvoiceLineItem)
        .where(InvoiceLineItem.invoice_id == invoice_id)
        .order_by(InvoiceLineItem.sort_order, InvoiceLineItem.id)
    ).all()

    line_items = [
        InvoiceLineItemOut(
            id=li.id,
            service_account_id=li.service_account_id,
            description=li.description,
            amount=li.amount,
            is_tax=(li.line_type.value == "TAX"),
            sort_order=li.sort_order,
        )
        for li in li_rows
    ]

    # Collect distinct service accounts referenced by line items
    svc_ids = sorted(
        {li.service_account_id for li in li_rows if li.service_account_id is not None}
    )
    service_accounts: list[ServiceAccountSummary] = []
    if svc_ids:
        svc_rows = db.scalars(
            select(ServiceAccount)
            .where(ServiceAccount.id.in_(svc_ids))
            .order_by(ServiceAccount.id)
        ).all()
        service_accounts = [
            ServiceAccountSummary(
                id=s.id,
                service_type=s.service_type.value,
                identifier=s.service_number,
            )
            for s in svc_rows
        ]

    return _build_invoice_out(inv, service_accounts, line_items)


# ---------------------------------------------------------------------------
# Billing runs (used by the billing router)
# ---------------------------------------------------------------------------

def get_invoice_info_for_billing_period(
    db: Session,
    account_id: int,
    year: int,
    month: int,
) -> tuple[int, str, date, date, str] | None:
    """
    Return (invoice_id, account_number, period_start, period_end, status_value)
    for the invoice of account_id issued in billing year/month, or None.

    Matches the same billing_date filter that repository.find_invoice_period uses.
    """
    row = db.execute(
        select(
            Invoice.id,
            Account.account_number,
            Invoice.period_start,
            Invoice.period_end,
            Invoice.status,
        )
        .join(Account, Invoice.account_id == Account.id)
        .where(
            Invoice.account_id == account_id,
            extract("year",  Invoice.period_start) == year,
            extract("month", Invoice.period_start) == month,
        )
    ).one_or_none()
    if row is None:
        return None
    return row.id, row.account_number, row.period_start, row.period_end, row.status.value


def get_bill_coords_for_invoice(
    db: Session, invoice_id: int
) -> tuple[str, date, date] | None:
    """
    Return (account_number, period_start, period_end) for the billing engine, or None.

    These three values are everything build_bill() needs beyond the session.
    """
    row = db.execute(
        select(Account.account_number, Invoice.period_start, Invoice.period_end)
        .join(Account, Invoice.account_id == Account.id)
        .where(Invoice.id == invoice_id)
    ).one_or_none()
    if row is None:
        return None
    return row.account_number, row.period_start, row.period_end


def get_billing_run_out(db: Session, run_id: int) -> BillingRunOut | None:
    """Return BillingRunOut (with failures list) for the given run_id, or None."""
    run = db.get(BillingRun, run_id)
    if run is None:
        return None

    failure_rows = db.scalars(
        select(BillingRunFailure)
        .where(BillingRunFailure.billing_run_id == run_id)
        .order_by(BillingRunFailure.id)
    ).all()

    failures = [
        BillingRunFailureOut(
            id=f.id,
            run_id=f.billing_run_id,
            account_id=f.account_id,
            error=f.error_message,
        )
        for f in failure_rows
    ]

    return BillingRunOut(
        id=run.id,
        period=run.period_start.strftime("%Y-%m"),
        status=run.status.value.lower(),
        total=run.total_accounts,
        succeeded=run.succeeded,
        failed=run.failed,
        started_at=run.started_at,
        finished_at=run.finished_at,
        failures=failures,
    )
