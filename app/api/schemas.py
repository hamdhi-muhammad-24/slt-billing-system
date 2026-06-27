"""
Pydantic v2 request/response models for the SLT E-Bill API.

No DB access and no business logic here. All monetary fields use the Money
annotated type so they serialise to 2-dp strings in JSON responses.
"""
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Generic, Optional, TypeVar

from pydantic import BaseModel, Field, PlainSerializer, field_validator

# ---------------------------------------------------------------------------
# Money — Decimal internally, 2-dp string in JSON (e.g. "4628.52")
# ---------------------------------------------------------------------------

Money = Annotated[
    Decimal,
    PlainSerializer(lambda v: f"{v:.2f}", return_type=str),
]

# ---------------------------------------------------------------------------
# Pagination envelope
# ---------------------------------------------------------------------------

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class CustomerOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    nic: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    title: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_language: Optional[str] = None
    customer_type: Optional[str] = None
    address: Optional[str] = None


class AccountOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    customer_id: int
    account_no: str
    status: str
    billing_cycle: Optional[str] = None
    service_label: Optional[str] = None
    telephone_number: Optional[str] = None
    bill_delivery_method: Optional[str] = None
    credit_limit: Optional[Money] = None
    deposit_amount: Optional[Money] = None
    notify_email: bool = True
    notify_sms: bool = True


class ServiceAccountOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    account_id: int
    service_type: str
    identifier: str
    package_id: Optional[int] = None
    package_name: Optional[str] = None
    connection_type: Optional[str] = None
    label: Optional[str] = None
    status: Optional[str] = None


class ServiceAccountSummary(BaseModel):
    """Embedded in InvoiceOut — lighter than the full ServiceAccountOut."""

    model_config = {"from_attributes": True}

    id: int
    service_type: str
    identifier: str


class PackageOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    service_type: str
    monthly_rental: Money


class InvoiceLineItemOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    service_account_id: Optional[int] = None
    description: str
    amount: Money          # negative for discounts
    is_tax: bool           # True when line_type == TAX
    sort_order: int


class InvoiceOut(BaseModel):
    """Frozen snapshot — totals are read as stored, never recomputed."""

    model_config = {"from_attributes": True}

    id: int
    account_id: int
    period: str            # "YYYY-MM", derived from period_start by the repo
    issue_date: date       # billing_date in the DB
    due_date: date
    balance_bf: Money
    payments_received: Money
    arrears: Money         # balance_bf − payments_received, pre-computed by repo
    charges_for_period: Money
    total_payable: Money
    service_accounts: list[ServiceAccountSummary] = []
    line_items: list[InvoiceLineItemOut] = []


class PaymentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    account_id: int
    amount: Money
    paid_at: date          # payment_date in the DB
    method: str
    reference: Optional[str] = None
    status: Optional[str] = None
    receipt_number: Optional[str] = None
    provider: Optional[str] = None


class UsageSummaryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    service_account_id: int
    period: str
    metric: str
    included_quantity: Decimal
    used_quantity: Decimal
    remaining_quantity: Decimal
    overage_quantity: Decimal
    charge: Money


class DailyUsageRecordOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    service_account_id: int
    usage_date: date
    bucket: str
    protocol: Optional[str] = None
    app_category: Optional[str] = None
    download_gb: Decimal
    upload_gb: Decimal
    total_gb: Decimal
    charge: Money


class BillingRunFailureOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    run_id: int            # billing_run_id in the DB
    account_id: Optional[int] = None
    error: str             # error_message in the DB


class BillingRunOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    period: str            # "YYYY-MM", derived from period_start by the repo
    status: str            # pending | running | done | failed | partial
    total: int             # total_accounts in the DB
    succeeded: int
    failed: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    failures: list[BillingRunFailureOut] = []


class DashboardRecentInvoiceOut(BaseModel):
    id: int
    account_id: int
    account_no: str
    customer_name: str
    period: str
    issue_date: date
    total_payable: Money
    status: str


class DashboardAlertOut(BaseModel):
    level: str
    title: str
    detail: str


class AdminDashboardSummaryOut(BaseModel):
    total_customers: int
    active_accounts: int
    generated_invoices: int
    failed_billing_runs: int
    notifications_sent: int
    notifications_failed: int
    recent_billing_runs: list[BillingRunOut]
    recent_invoices: list[DashboardRecentInvoiceOut]
    alerts: list[DashboardAlertOut]


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _validate_period(v: str) -> str:
    if not _PERIOD_RE.match(v):
        raise ValueError("period must be YYYY-MM (e.g. '2024-12')")
    return v


class GenerateOneRequest(BaseModel):
    account_id: int
    period: str = Field(..., examples=["2024-12"])

    @field_validator("period")
    @classmethod
    def period_format(cls, v: str) -> str:
        return _validate_period(v)


class GenerateBatchRequest(BaseModel):
    period: str = Field(..., examples=["2024-12"])
    account_ids: Optional[list[int]] = Field(
        default=None,
        description="Omit to run all active accounts.",
    )

    @field_validator("period")
    @classmethod
    def period_format(cls, v: str) -> str:
        return _validate_period(v)
