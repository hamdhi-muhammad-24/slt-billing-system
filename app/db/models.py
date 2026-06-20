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


class RunStatus(enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


# ---------------------------------------------------------------------------
# Reusable SQLAlchemy Enum column types (shared across multiple tables)
# ---------------------------------------------------------------------------

_account_status = Enum(AccountStatus, name="account_status")
_service_type   = Enum(ServiceType,   name="service_type")


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
    address_line1 = Column(Text)
    address_line2 = Column(Text)
    city          = Column(Text)
    postal_code   = Column(Text)
    status        = Column(_account_status, nullable=False, default=AccountStatus.ACTIVE)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


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
    status           = Column(_account_status, nullable=False, default=AccountStatus.ACTIVE)
    created_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ServiceAccount(Base):
    __tablename__ = "service_accounts"
    __table_args__ = (
        Index("idx_service_accounts_account", "account_id"),
    )

    id             = Column(BigInteger, Identity(always=True), primary_key=True)
    account_id     = Column(BigInteger, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    service_number = Column(Text, nullable=False)
    service_type   = Column(_service_type, nullable=False)
    label          = Column(Text)
    created_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Package(Base):
    __tablename__ = "packages"

    id                  = Column(BigInteger, Identity(always=True), primary_key=True)
    name                = Column(Text, nullable=False)
    service_type        = Column(_service_type, nullable=False)
    monthly_fee         = Column(Numeric(12, 2), nullable=False, default=0)
    data_limit_gb       = Column(Numeric(10, 2))
    extra_charge_per_gb = Column(Numeric(12, 2), default=0)
    is_active           = Column(Boolean, nullable=False, default=True)


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
    payment_date = Column(Date, nullable=False)
    method       = Column(Enum(PaymentMethod, name="payment_method"), nullable=False, default=PaymentMethod.PHYSICAL)
    amount       = Column(Numeric(12, 2), nullable=False)
    reference    = Column(Text)
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
