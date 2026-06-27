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
    BillingPeriod,
    BillingRun,
    BillingRunFailure,
    Customer,
    DailyUsageRecord,
    Invoice,
    InvoiceLineItem,
    Package,
    Payment,
    ServiceAccount,
    UsageSummary,
)
from app.notifications.models import NotificationOutbox
from app.api.schemas import (
    AdminDashboardSummaryOut,
    AccountOut,
    BillingRunFailureOut,
    BillingRunOut,
    CustomerOut,
    DashboardAlertOut,
    DashboardRecentInvoiceOut,
    DailyUsageRecordOut,
    InvoiceLineItemOut,
    InvoiceOut,
    PaymentOut,
    ServiceAccountOut,
    ServiceAccountSummary,
    UsageSummaryOut,
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
        nic=c.nic,
        email=c.email,
        phone=c.mobile_number,
        alternate_phone=c.alternate_phone,
        title=c.title,
        first_name=c.first_name,
        last_name=c.last_name,
        preferred_language=c.preferred_language,
        customer_type=c.customer_type.value if c.customer_type else None,
        address=_address(c),
    )


def _account_out(a: Account) -> AccountOut:
    return AccountOut(
        id=a.id,
        customer_id=a.customer_id,
        account_no=a.account_number,
        status=a.status.value,
        billing_cycle=a.billing_cycle,
        service_label=a.service_label,
        telephone_number=a.telephone_number,
        bill_delivery_method=a.bill_delivery_method.value if a.bill_delivery_method else None,
        credit_limit=a.credit_limit,
        deposit_amount=a.deposit_amount,
        notify_email=a.notify_email,
        notify_sms=a.notify_sms,
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
    rows = db.execute(
        select(ServiceAccount, Package.name)
        .outerjoin(Package, ServiceAccount.package_id == Package.id)
        .where(ServiceAccount.account_id == account_id)
        .order_by(ServiceAccount.id)
    ).all()
    return [
        ServiceAccountOut(
            id=svc.id,
            account_id=svc.account_id,
            service_type=svc.service_type.value,
            identifier=svc.service_number,
            package_id=svc.package_id,
            package_name=package_name,
            connection_type=svc.connection_type.value if svc.connection_type else None,
            label=svc.label,
            status=svc.status.value if svc.status else None,
        )
        for svc, package_name in rows
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
            status=r.status.value if r.status else None,
            receipt_number=r.receipt_number,
            provider=r.provider,
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
# Usage
# ---------------------------------------------------------------------------

def list_usage_for_account(
    db: Session,
    account_id: int,
    *,
    period: str | None = None,
    months: int | None = None,
) -> list[UsageSummaryOut]:
    query = (
        select(UsageSummary, BillingPeriod.code)
        .join(ServiceAccount, UsageSummary.service_account_id == ServiceAccount.id)
        .join(BillingPeriod, UsageSummary.billing_period_id == BillingPeriod.id)
        .where(ServiceAccount.account_id == account_id)
        .order_by(BillingPeriod.period_start.desc(), ServiceAccount.id)
    )
    if period is not None:
        query = query.where(BillingPeriod.code == period)
    if months is not None:
        query = query.limit(months * 10)

    rows = db.execute(query).all()
    return [
        UsageSummaryOut(
            id=summary.id,
            service_account_id=summary.service_account_id,
            period=period_code,
            metric=summary.metric,
            included_quantity=summary.included_quantity,
            used_quantity=summary.used_quantity,
            remaining_quantity=summary.remaining_quantity,
            overage_quantity=summary.overage_quantity,
            charge=summary.charge,
        )
        for summary, period_code in rows
    ]


def list_daily_usage_for_service(
    db: Session,
    service_account_id: int,
    *,
    period: str,
) -> list[DailyUsageRecordOut]:
    rows = db.scalars(
        select(DailyUsageRecord)
        .join(BillingPeriod, DailyUsageRecord.billing_period_id == BillingPeriod.id)
        .where(
            DailyUsageRecord.service_account_id == service_account_id,
            BillingPeriod.code == period,
        )
        .order_by(DailyUsageRecord.usage_date, DailyUsageRecord.id)
    ).all()
    return [
        DailyUsageRecordOut(
            id=row.id,
            service_account_id=row.service_account_id,
            usage_date=row.usage_date,
            bucket=row.bucket,
            protocol=row.protocol,
            app_category=row.app_category,
            download_gb=row.download_gb,
            upload_gb=row.upload_gb,
            total_gb=row.total_gb,
            charge=row.charge,
        )
        for row in rows
    ]


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
            extract("year",  Invoice.billing_date) == year,
            extract("month", Invoice.billing_date) == month,
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


def get_admin_dashboard_summary(db: Session) -> AdminDashboardSummaryOut:
    total_customers = db.scalar(select(func.count(Customer.id))) or 0
    active_accounts = db.scalar(
        select(func.count(Account.id)).where(Account.status == "ACTIVE")
    ) or 0
    generated_invoices = db.scalar(
        select(func.count(Invoice.id)).where(Invoice.status == "GENERATED")
    ) or 0
    failed_billing_runs = db.scalar(
        select(func.count(BillingRun.id)).where(BillingRun.status.in_(["FAILED", "PARTIAL"]))
    ) or 0
    notifications_sent = db.scalar(
        select(func.count(NotificationOutbox.id)).where(NotificationOutbox.status == "SENT")
    ) or 0
    notifications_failed = db.scalar(
        select(func.count(NotificationOutbox.id)).where(NotificationOutbox.status == "FAILED")
    ) or 0

    run_rows = db.scalars(
        select(BillingRun)
        .order_by(BillingRun.started_at.desc(), BillingRun.id.desc())
        .limit(6)
    ).all()
    recent_runs = []
    for run in run_rows:
        failures = db.scalars(
            select(BillingRunFailure)
            .where(BillingRunFailure.billing_run_id == run.id)
            .order_by(BillingRunFailure.id)
        ).all()
        recent_runs.append(BillingRunOut(
            id=run.id,
            period=run.period_start.strftime("%Y-%m"),
            status=run.status.value.lower(),
            total=run.total_accounts,
            succeeded=run.succeeded,
            failed=run.failed,
            started_at=run.started_at,
            finished_at=run.finished_at,
            failures=[
                BillingRunFailureOut(
                    id=f.id,
                    run_id=f.billing_run_id,
                    account_id=f.account_id,
                    error=f.error_message,
                )
                for f in failures
            ],
        ))

    invoice_rows = db.execute(
        select(Invoice, Account.account_number, Customer.full_name)
        .join(Account, Invoice.account_id == Account.id)
        .join(Customer, Account.customer_id == Customer.id)
        .order_by(Invoice.billing_date.desc(), Invoice.id.desc())
        .limit(8)
    ).all()
    recent_invoices = [
        DashboardRecentInvoiceOut(
            id=invoice.id,
            account_id=invoice.account_id,
            account_no=account_number,
            customer_name=customer_name,
            period=invoice.period_start.strftime("%Y-%m"),
            issue_date=invoice.billing_date,
            total_payable=invoice.total_payable,
            status=invoice.status.value,
        )
        for invoice, account_number, customer_name in invoice_rows
    ]

    alerts: list[DashboardAlertOut] = []
    if failed_billing_runs:
        alerts.append(DashboardAlertOut(
            level="critical",
            title="Billing runs need review",
            detail=f"{failed_billing_runs} failed or partial billing run(s) are recorded.",
        ))
    if notifications_failed:
        alerts.append(DashboardAlertOut(
            level="warning",
            title="Notification delivery failures",
            detail=f"{notifications_failed} notification(s) failed and may need retry.",
        ))
    overdue_invoices = db.scalar(
        select(func.count(Invoice.id)).where(Invoice.status == "OVERDUE")
    ) or 0
    if overdue_invoices:
        alerts.append(DashboardAlertOut(
            level="warning",
            title="Overdue invoices present",
            detail=f"{overdue_invoices} invoice(s) are marked overdue.",
        ))
    if not alerts:
        alerts.append(DashboardAlertOut(
            level="success",
            title="Billing operations normal",
            detail="No failed runs or notification failures require immediate action.",
        ))

    return AdminDashboardSummaryOut(
        total_customers=total_customers,
        active_accounts=active_accounts,
        generated_invoices=generated_invoices,
        failed_billing_runs=failed_billing_runs,
        notifications_sent=notifications_sent,
        notifications_failed=notifications_failed,
        recent_billing_runs=recent_runs,
        recent_invoices=recent_invoices,
        alerts=alerts,
    )
