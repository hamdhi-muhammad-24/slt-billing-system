import enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Identity,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    ForeignKey,
    func,
)

from app.db.base import Base


# ---------------------------------------------------------------------------
# Python enum definitions (values match the PostgreSQL enum labels exactly)
# ---------------------------------------------------------------------------

class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"


class AccountStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class CustomerType(enum.Enum):
    RESIDENTIAL = "RESIDENTIAL"
    BUSINESS = "BUSINESS"


class AddressType(enum.Enum):
    BILLING = "BILLING"
    SERVICE = "SERVICE"
    POSTAL = "POSTAL"


class ServiceType(enum.Enum):
    VOICE = "VOICE"
    BROADBAND = "BROADBAND"
    PEOTV = "PEOTV"
    BUNDLE = "BUNDLE"
    OTHER = "OTHER"


class LineType(enum.Enum):
    RENTAL = "RENTAL"
    USAGE = "USAGE"
    DISCOUNT = "DISCOUNT"
    TAX = "TAX"
    FEE = "FEE"
    ADJUSTMENT = "ADJUSTMENT"


class InvoiceStatus(enum.Enum):
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    SENT = "SENT"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class PaymentMethod(enum.Enum):
    PHYSICAL = "PHYSICAL"
    ONLINE = "ONLINE"
    CARD = "CARD"
    CHEQUE = "CHEQUE"
    BANK_TRANSFER = "BANK_TRANSFER"


class PaymentStatus(enum.Enum):
    PENDING = "PENDING"
    POSTED = "POSTED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"


class RunStatus(enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class BillDeliveryMethod(enum.Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    POSTAL = "POSTAL"
    PORTAL = "PORTAL"


class ConnectionType(enum.Enum):
    FTTH = "FTTH"
    ADSL = "ADSL"
    LTE = "LTE"
    VOICE = "VOICE"
    PEOTV = "PEOTV"
    OTHER = "OTHER"


class RequestType(enum.Enum):
    NEW_SERVICE = "NEW_SERVICE"
    PACKAGE_UPGRADE = "PACKAGE_UPGRADE"
    PACKAGE_DOWNGRADE = "PACKAGE_DOWNGRADE"
    RELOCATION = "RELOCATION"
    DISCONNECTION = "DISCONNECTION"


class RequestStatus(enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class FaultStatus(enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


# ---------------------------------------------------------------------------
# Reusable SQLAlchemy Enum column types (shared across multiple tables)
# ---------------------------------------------------------------------------

_account_status = Enum(AccountStatus, name="account_status")
_service_type   = Enum(ServiceType,   name="service_type")
_customer_type  = Enum(CustomerType,  name="customer_type")
_address_type   = Enum(AddressType,   name="address_type")
_bill_delivery  = Enum(BillDeliveryMethod, name="bill_delivery_method")
_connection_type = Enum(ConnectionType, name="connection_type")


# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id            = Column(BigInteger, Identity(always=True), primary_key=True)
    email         = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    role          = Column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.CUSTOMER)
    is_active     = Column(Boolean, nullable=False, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Customer(Base):
    __tablename__ = "customers"

    id            = Column(BigInteger, Identity(always=True), primary_key=True)
    user_id       = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    full_name     = Column(Text, nullable=False)
    nic           = Column(Text, unique=True)
    title         = Column(Text)
    first_name    = Column(Text)
    last_name     = Column(Text)
    email         = Column(Text)
    mobile_number = Column(Text)
    alternate_phone = Column(Text)
    preferred_language = Column(Text, nullable=False, default="en")
    date_of_birth = Column(Date)
    customer_type = Column(_customer_type, nullable=False, default=CustomerType.RESIDENTIAL)
    address_line1 = Column(Text)
    address_line2 = Column(Text)
    city          = Column(Text)
    postal_code   = Column(Text)
    status        = Column(_account_status, nullable=False, default=AccountStatus.ACTIVE)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CustomerAddress(Base):
    __tablename__ = "customer_addresses"
    __table_args__ = (
        Index("idx_customer_addresses_customer", "customer_id"),
    )

    id           = Column(BigInteger, Identity(always=True), primary_key=True)
    customer_id  = Column(BigInteger, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    address_type = Column(_address_type, nullable=False)
    line1        = Column(Text, nullable=False)
    line2        = Column(Text)
    city         = Column(Text)
    district     = Column(Text)
    province     = Column(Text)
    postal_code  = Column(Text)
    country      = Column(Text, nullable=False, default="Sri Lanka")
    is_primary   = Column(Boolean, nullable=False, default=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        Index("idx_accounts_customer", "customer_id"),
    )

    id               = Column(BigInteger, Identity(always=True), primary_key=True)
    customer_id      = Column(BigInteger, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    account_number   = Column(Text, nullable=False, unique=True)
    telephone_number = Column(Text)
    service_label    = Column(Text)
    billing_cycle    = Column(Text, nullable=False, default="MONTHLY_25")
    bill_delivery_method = Column(_bill_delivery, nullable=False, default=BillDeliveryMethod.PORTAL)
    credit_limit     = Column(Numeric(12, 2), nullable=False, default=0)
    deposit_amount   = Column(Numeric(12, 2), nullable=False, default=0)
    opened_on        = Column(Date)
    closed_on        = Column(Date)
    last_billed_at   = Column(DateTime(timezone=True))
    notify_email     = Column(Boolean, nullable=False, default=True)
    notify_sms       = Column(Boolean, nullable=False, default=True)
    status           = Column(_account_status, nullable=False, default=AccountStatus.ACTIVE)
    created_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ServiceAccount(Base):
    __tablename__ = "service_accounts"
    __table_args__ = (
        Index("idx_service_accounts_account", "account_id"),
    )

    id             = Column(BigInteger, Identity(always=True), primary_key=True)
    account_id     = Column(BigInteger, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    package_id     = Column(BigInteger, ForeignKey("packages.id", ondelete="SET NULL"), nullable=True)
    installation_address_id = Column(BigInteger, ForeignKey("customer_addresses.id", ondelete="SET NULL"), nullable=True)
    service_number = Column(Text, nullable=False)
    service_type   = Column(_service_type, nullable=False)
    connection_type = Column(_connection_type, nullable=False, default=ConnectionType.OTHER)
    label          = Column(Text)
    activated_on   = Column(Date)
    contract_number = Column(Text)
    router_serial  = Column(Text)
    ont_serial     = Column(Text)
    service_username = Column(Text)
    status         = Column(_account_status, nullable=False, default=AccountStatus.ACTIVE)
    created_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Package(Base):
    __tablename__ = "packages"

    id                  = Column(BigInteger, Identity(always=True), primary_key=True)
    package_code        = Column(Text, unique=True)
    name                = Column(Text, nullable=False)
    service_type        = Column(_service_type, nullable=False)
    monthly_fee         = Column(Numeric(12, 2), nullable=False, default=0)
    speed_tier          = Column(Text)
    data_limit_gb       = Column(Numeric(10, 2))
    anytime_gb          = Column(Numeric(10, 2))
    peak_gb             = Column(Numeric(10, 2))
    offpeak_gb          = Column(Numeric(10, 2))
    included_voice_minutes = Column(Numeric(12, 3))
    extra_charge_per_gb = Column(Numeric(12, 2), default=0)
    active_from         = Column(Date)
    active_to           = Column(Date)
    tax_applicable      = Column(Boolean, nullable=False, default=True)
    is_active           = Column(Boolean, nullable=False, default=True)


class BillingPeriod(Base):
    __tablename__ = "billing_periods"

    id           = Column(BigInteger, Identity(always=True), primary_key=True)
    code         = Column(Text, nullable=False, unique=True)
    period_start = Column(Date, nullable=False)
    period_end   = Column(Date, nullable=False)
    billing_date = Column(Date, nullable=False)
    due_date     = Column(Date, nullable=False)


class UsageSummary(Base):
    __tablename__ = "usage_summaries"
    __table_args__ = (
        UniqueConstraint("service_account_id", "billing_period_id", "metric", name="uq_usage_summary_service_period_metric"),
        Index("idx_usage_summaries_service", "service_account_id"),
        Index("idx_usage_summaries_period", "billing_period_id"),
    )

    id                 = Column(BigInteger, Identity(always=True), primary_key=True)
    service_account_id = Column(BigInteger, ForeignKey("service_accounts.id", ondelete="CASCADE"), nullable=False)
    billing_period_id  = Column(BigInteger, ForeignKey("billing_periods.id", ondelete="CASCADE"), nullable=False)
    period_start       = Column(Date, nullable=False)
    period_end         = Column(Date, nullable=False)
    metric             = Column(Text, nullable=False)
    included_quantity  = Column(Numeric(12, 3), nullable=False, default=0)
    used_quantity      = Column(Numeric(12, 3), nullable=False, default=0)
    remaining_quantity = Column(Numeric(12, 3), nullable=False, default=0)
    overage_quantity   = Column(Numeric(12, 3), nullable=False, default=0)
    charge             = Column(Numeric(12, 2), nullable=False, default=0)
    created_at         = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DailyUsageRecord(Base):
    __tablename__ = "daily_usage_records"
    __table_args__ = (
        Index("idx_daily_usage_service_date", "service_account_id", "usage_date"),
        Index("idx_daily_usage_period", "billing_period_id"),
    )

    id                 = Column(BigInteger, Identity(always=True), primary_key=True)
    service_account_id = Column(BigInteger, ForeignKey("service_accounts.id", ondelete="CASCADE"), nullable=False)
    billing_period_id  = Column(BigInteger, ForeignKey("billing_periods.id", ondelete="CASCADE"), nullable=False)
    usage_date         = Column(Date, nullable=False)
    bucket             = Column(Text, nullable=False, default="ANYTIME")
    protocol           = Column(Text)
    app_category       = Column(Text)
    download_gb        = Column(Numeric(12, 3), nullable=False, default=0)
    upload_gb          = Column(Numeric(12, 3), nullable=False, default=0)
    total_gb           = Column(Numeric(12, 3), nullable=False, default=0)
    charge             = Column(Numeric(12, 2), nullable=False, default=0)


class ServiceAddon(Base):
    __tablename__ = "service_addons"
    __table_args__ = (
        Index("idx_service_addons_service", "service_account_id"),
        Index("idx_service_addons_period", "billing_period_id"),
    )

    id                 = Column(BigInteger, Identity(always=True), primary_key=True)
    service_account_id = Column(BigInteger, ForeignKey("service_accounts.id", ondelete="CASCADE"), nullable=False)
    billing_period_id  = Column(BigInteger, ForeignKey("billing_periods.id", ondelete="CASCADE"), nullable=False)
    addon_name         = Column(Text, nullable=False)
    addon_type         = Column(Text, nullable=False, default="EXTRA_GB")
    purchased_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    valid_from         = Column(Date, nullable=False)
    valid_to           = Column(Date, nullable=False)
    quantity_gb        = Column(Numeric(10, 2), nullable=False, default=0)
    remaining_gb       = Column(Numeric(10, 2), nullable=False, default=0)
    charge             = Column(Numeric(12, 2), nullable=False, default=0)


class UsageRecord(Base):
    __tablename__ = "usage_records"
    __table_args__ = (
        Index("idx_usage_service", "service_account_id"),
    )

    id                 = Column(BigInteger, Identity(always=True), primary_key=True)
    service_account_id = Column(BigInteger, ForeignKey("service_accounts.id", ondelete="CASCADE"), nullable=False)
    period_start       = Column(Date, nullable=False)
    period_end         = Column(Date, nullable=False)
    metric             = Column(Text)
    description        = Column(Text)
    quantity           = Column(Numeric(12, 3))
    charge             = Column(Numeric(12, 2), default=0)
    event_time         = Column(DateTime(timezone=True))


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("account_id", "period_start", "period_end"),
        Index("idx_invoices_account", "account_id"),
        Index("idx_invoices_period", "period_start", "period_end"),
    )

    id                 = Column(BigInteger, Identity(always=True), primary_key=True)
    account_id         = Column(BigInteger, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False)
    invoice_number     = Column(Text, nullable=False, unique=True)
    billing_date       = Column(Date, nullable=False)
    period_start       = Column(Date, nullable=False)
    period_end         = Column(Date, nullable=False)
    due_date           = Column(Date, nullable=False)
    snapshot_customer_name = Column(Text)
    snapshot_customer_nic = Column(Text)
    snapshot_bill_address = Column(Text)
    snapshot_account_number = Column(Text)
    snapshot_telephone_number = Column(Text)
    snapshot_package_name = Column(Text)
    snapshot_service_label = Column(Text)
    balance_bf         = Column(Numeric(12, 2), nullable=False, default=0)
    payments_received  = Column(Numeric(12, 2), nullable=False, default=0)
    charges_total      = Column(Numeric(12, 2), nullable=False, default=0)
    taxes_total        = Column(Numeric(12, 2), nullable=False, default=0)
    charges_for_period = Column(Numeric(12, 2), nullable=False, default=0)
    total_payable      = Column(Numeric(12, 2), nullable=False, default=0)
    status             = Column(Enum(InvoiceStatus, name="invoice_status"), nullable=False, default=InvoiceStatus.GENERATED)
    pdf_path           = Column(Text)
    created_at         = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"
    __table_args__ = (
        Index("idx_line_items_invoice", "invoice_id"),
    )

    id                 = Column(BigInteger, Identity(always=True), primary_key=True)
    invoice_id         = Column(BigInteger, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    service_account_id = Column(BigInteger, ForeignKey("service_accounts.id", ondelete="SET NULL"), nullable=True)
    line_type          = Column(Enum(LineType, name="line_type"), nullable=False)
    description        = Column(Text, nullable=False)
    period_start       = Column(Date)
    period_end         = Column(Date)
    amount             = Column(Numeric(12, 2), nullable=False)
    sort_order         = Column(Integer, nullable=False, default=0)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        Index("idx_payments_account", "account_id"),
    )

    id           = Column(BigInteger, Identity(always=True), primary_key=True)
    account_id   = Column(BigInteger, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    invoice_id   = Column(BigInteger, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    payment_date = Column(Date, nullable=False)
    method       = Column(Enum(PaymentMethod, name="payment_method"), nullable=False, default=PaymentMethod.PHYSICAL)
    status       = Column(Enum(PaymentStatus, name="payment_status"), nullable=False, default=PaymentStatus.POSTED)
    amount       = Column(Numeric(12, 2), nullable=False)
    reference    = Column(Text)
    receipt_number = Column(Text)
    provider     = Column(Text)
    provider_reference = Column(Text)
    posted_at    = Column(DateTime(timezone=True))
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class BillingRun(Base):
    __tablename__ = "billing_runs"

    id             = Column(BigInteger, Identity(always=True), primary_key=True)
    period_start   = Column(Date, nullable=False)
    period_end     = Column(Date, nullable=False)
    status         = Column(Enum(RunStatus, name="run_status"), nullable=False, default=RunStatus.PENDING)
    total_accounts = Column(Integer, nullable=False, default=0)
    succeeded      = Column(Integer, nullable=False, default=0)
    failed         = Column(Integer, nullable=False, default=0)
    started_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at    = Column(DateTime(timezone=True))


class BillingRunFailure(Base):
    __tablename__ = "billing_run_failures"

    id             = Column(BigInteger, Identity(always=True), primary_key=True)
    billing_run_id = Column(BigInteger, ForeignKey("billing_runs.id", ondelete="CASCADE"), nullable=False)
    account_id     = Column(BigInteger, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    error_message  = Column(Text, nullable=False)
    created_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ServiceRequest(Base):
    __tablename__ = "service_requests"
    __table_args__ = (
        Index("idx_service_requests_customer", "customer_id"),
        Index("idx_service_requests_account", "account_id"),
    )

    id                 = Column(BigInteger, Identity(always=True), primary_key=True)
    customer_id        = Column(BigInteger, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    account_id         = Column(BigInteger, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    service_account_id = Column(BigInteger, ForeignKey("service_accounts.id", ondelete="SET NULL"), nullable=True)
    request_type       = Column(Enum(RequestType, name="request_type"), nullable=False)
    status             = Column(Enum(RequestStatus, name="request_status"), nullable=False, default=RequestStatus.OPEN)
    requested_package_id = Column(BigInteger, ForeignKey("packages.id", ondelete="SET NULL"), nullable=True)
    notes              = Column(Text)
    created_at         = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at        = Column(DateTime(timezone=True))


class FaultTicket(Base):
    __tablename__ = "fault_tickets"
    __table_args__ = (
        Index("idx_fault_tickets_customer", "customer_id"),
        Index("idx_fault_tickets_account", "account_id"),
    )

    id                 = Column(BigInteger, Identity(always=True), primary_key=True)
    customer_id        = Column(BigInteger, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    account_id         = Column(BigInteger, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    service_account_id = Column(BigInteger, ForeignKey("service_accounts.id", ondelete="SET NULL"), nullable=True)
    ticket_number      = Column(Text, nullable=False, unique=True)
    status             = Column(Enum(FaultStatus, name="fault_status"), nullable=False, default=FaultStatus.OPEN)
    category           = Column(Text, nullable=False)
    description        = Column(Text, nullable=False)
    opened_at          = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at        = Column(DateTime(timezone=True))
