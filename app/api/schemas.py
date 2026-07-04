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


class BillingRunItemOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    billing_run_id: int
    account_id: Optional[int] = None
    customer_id: Optional[int] = None
    invoice_id: Optional[int] = None
    template_id: Optional[int] = None
    account_number: Optional[str] = None
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    pdf_status: str
    email_status: str
    sms_status: str
    overall_status: str
    failure_reason: Optional[str] = None
    email_failure_reason: Optional[str] = None
    sms_failure_reason: Optional[str] = None
    email_provider_ref: Optional[str] = None
    sms_provider_ref: Optional[str] = None
    retry_count: int
    pdf_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BillingRunOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    period: str            # "YYYY-MM", derived from period_start by the repo
    status: str            # pending | running | done | failed | partial
    template_id: Optional[int] = None
    template_name: Optional[str] = None
    total: int             # total_accounts in the DB
    succeeded: int
    failed: int
    pdf_success_count: int = 0
    pdf_failed_count: int = 0
    email_status_summary: dict[str, int] = Field(default_factory=dict)
    sms_status_summary: dict[str, int] = Field(default_factory=dict)
    started_at: datetime
    finished_at: Optional[datetime] = None
    failures: list[BillingRunFailureOut] = Field(default_factory=list)
    items: list[BillingRunItemOut] = Field(default_factory=list)


class InvoiceTemplateOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: Optional[str] = None
    template_code: str
    is_active: bool
    is_system_template: bool
    base_template_id: Optional[int] = None
    header_message: Optional[str] = None
    footer_message: Optional[str] = None
    promotion_message: Optional[str] = None
    theme_name: Optional[str] = None
    theme_color: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class InvoiceTemplateEditRequest(BaseModel):
    header_message: Optional[str] = None
    footer_message: Optional[str] = None
    promotion_message: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    theme_name: Optional[str] = None
    theme_color: Optional[str] = None
    confirm_save_original: bool = False


class BillingScheduleOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    day_of_month: int
    run_time: str
    timezone: str
    schedule_mode: str
    is_active: bool
    send_email: bool
    send_sms: bool
    approval_lead_days: int
    approval_email: Optional[str] = None
    last_triggered_period: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BillingScheduleUpdateRequest(BaseModel):
    name: Optional[str] = None
    day_of_month: int = Field(1, ge=1, le=28)
    run_time: str = Field("02:00", pattern=r"^\d{2}:\d{2}$")
    timezone: str = "Asia/Colombo"
    schedule_mode: str = Field("AUTOMATIC", pattern=r"^(AUTOMATIC|APPROVAL_REQUIRED)$")
    is_active: bool = True
    send_email: bool = True
    send_sms: bool = True
    approval_lead_days: int = Field(1, ge=1, le=7)
    approval_email: Optional[str] = None


class BillingRunApprovalOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    billing_schedule_id: int
    billing_run_id: Optional[int] = None
    period: str
    status: str
    requested_to: Optional[str] = None
    requested_at: datetime
    expires_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    decided_by_user_id: Optional[int] = None
    notes: Optional[str] = None


class ApprovalDecisionRequest(BaseModel):
    notes: Optional[str] = None


class SendBillingRunRequest(BaseModel):
    send_email: bool = True
    send_sms: bool = True


class RetryBillingRunItemRequest(BaseModel):
    send_notifications: bool = True
    send_email: bool = True
    send_sms: bool = True


class EvaluateBillingSchedulesRequest(BaseModel):
    now: Optional[datetime] = None


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
    send_notifications: bool = Field(
        default=False,
        description="When true, attempt email/SMS delivery after PDFs are generated.",
    )

    @field_validator("period")
    @classmethod
    def period_format(cls, v: str) -> str:
        return _validate_period(v)
