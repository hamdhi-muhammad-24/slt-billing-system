"""
Read-only database queries for the API layer.

All SQL for the API lives here. The billing engine's repository
(app/billing/repository.py) covers engine-specific reads/writes and is
kept separate so it can be swapped to SLT's real DB independently.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    Account,
    Customer,
    Invoice,
    InvoiceLineItem,
    Payment,
    ServiceAccount,
)
from app.api.schemas import (
    AccountOut,
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
