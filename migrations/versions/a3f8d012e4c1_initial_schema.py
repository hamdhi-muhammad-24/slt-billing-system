"""initial_schema

Revision ID: a3f8d012e4c1
Revises:
Create Date: 2026-06-20 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from alembic import op

revision: str = "a3f8d012e4c1"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# Column-type singletons — create_type=False because we create types
# explicitly in upgrade() via DO blocks.  PgEnum (not sa.Enum) is used here
# because postgresql.ENUM reliably honours create_type=False in op.create_table;
# sa.Enum does not in SQLAlchemy 2.x.
# ---------------------------------------------------------------------------
_user_role      = PgEnum("ADMIN", "CUSTOMER",                                    name="user_role",      create_type=False)
_account_status = PgEnum("ACTIVE", "SUSPENDED", "CLOSED",                        name="account_status", create_type=False)
_service_type   = PgEnum("VOICE", "BROADBAND", "PEOTV", "BUNDLE", "OTHER",       name="service_type",   create_type=False)
_line_type      = PgEnum("RENTAL", "USAGE", "DISCOUNT", "TAX", "FEE", "ADJUSTMENT", name="line_type",   create_type=False)
_invoice_status = PgEnum("DRAFT", "GENERATED", "SENT", "PAID", "OVERDUE", "CANCELLED", name="invoice_status", create_type=False)
_payment_method = PgEnum("PHYSICAL", "ONLINE", "CARD", "CHEQUE", "BANK_TRANSFER", name="payment_method", create_type=False)
_run_status     = PgEnum("PENDING", "RUNNING", "DONE", "PARTIAL", "FAILED",       name="run_status",     create_type=False)


def _create_enum(name: str, *values: str) -> None:
    """Create a PG enum type; silently no-ops if it already exists."""
    labels = ", ".join(f"'{v}'" for v in values)
    op.execute(sa.text(
        f"DO $$ BEGIN "
        f"  CREATE TYPE {name} AS ENUM ({labels}); "
        f"EXCEPTION WHEN duplicate_object THEN NULL; "
        f"END $$"
    ))


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. PostgreSQL enum types — one per call, idempotent
    # ------------------------------------------------------------------
    _create_enum("user_role",      "ADMIN", "CUSTOMER")
    _create_enum("account_status", "ACTIVE", "SUSPENDED", "CLOSED")
    _create_enum("service_type",   "VOICE", "BROADBAND", "PEOTV", "BUNDLE", "OTHER")
    _create_enum("line_type",      "RENTAL", "USAGE", "DISCOUNT", "TAX", "FEE", "ADJUSTMENT")
    _create_enum("invoice_status", "DRAFT", "GENERATED", "SENT", "PAID", "OVERDUE", "CANCELLED")
    _create_enum("payment_method", "PHYSICAL", "ONLINE", "CARD", "CHEQUE", "BANK_TRANSFER")
    _create_enum("run_status",     "PENDING", "RUNNING", "DONE", "PARTIAL", "FAILED")

    # ------------------------------------------------------------------
    # 2. Tables (FK dependency order)
    # ------------------------------------------------------------------

    op.create_table(
        "users",
        sa.Column("id",            sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("email",         sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role",          _user_role, nullable=False, server_default=sa.text("'CUSTOMER'")),
        sa.Column("is_active",     sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at",    sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "customers",
        sa.Column("id",            sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("user_id",       sa.BigInteger(), nullable=True),
        sa.Column("full_name",     sa.Text(), nullable=False),
        sa.Column("address_line1", sa.Text(), nullable=True),
        sa.Column("address_line2", sa.Text(), nullable=True),
        sa.Column("city",          sa.Text(), nullable=True),
        sa.Column("postal_code",   sa.Text(), nullable=True),
        sa.Column("status",        _account_status, nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column("created_at",    sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "accounts",
        sa.Column("id",               sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("customer_id",      sa.BigInteger(), nullable=False),
        sa.Column("account_number",   sa.Text(), nullable=False),
        sa.Column("telephone_number", sa.Text(), nullable=True),
        sa.Column("service_label",    sa.Text(), nullable=True),
        sa.Column("status",           _account_status, nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column("created_at",       sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_number"),
    )

    op.create_table(
        "service_accounts",
        sa.Column("id",             sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("account_id",     sa.BigInteger(), nullable=False),
        sa.Column("service_number", sa.Text(), nullable=False),
        sa.Column("service_type",   _service_type, nullable=False),
        sa.Column("label",          sa.Text(), nullable=True),
        sa.Column("created_at",     sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "packages",
        sa.Column("id",                  sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("name",                sa.Text(), nullable=False),
        sa.Column("service_type",        _service_type, nullable=False),
        sa.Column("monthly_fee",         sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("data_limit_gb",       sa.Numeric(10, 2), nullable=True),
        sa.Column("extra_charge_per_gb", sa.Numeric(12, 2), nullable=True, server_default=sa.text("0")),
        sa.Column("is_active",           sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "usage_records",
        sa.Column("id",                 sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("service_account_id", sa.BigInteger(), nullable=False),
        sa.Column("period_start",       sa.Date(), nullable=False),
        sa.Column("period_end",         sa.Date(), nullable=False),
        sa.Column("metric",             sa.Text(), nullable=True),
        sa.Column("description",        sa.Text(), nullable=True),
        sa.Column("quantity",           sa.Numeric(12, 3), nullable=True),
        sa.Column("charge",             sa.Numeric(12, 2), nullable=True, server_default=sa.text("0")),
        sa.Column("event_time",         sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["service_account_id"], ["service_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "invoices",
        sa.Column("id",                 sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("account_id",         sa.BigInteger(), nullable=False),
        sa.Column("invoice_number",     sa.Text(), nullable=False),
        sa.Column("billing_date",       sa.Date(), nullable=False),
        sa.Column("period_start",       sa.Date(), nullable=False),
        sa.Column("period_end",         sa.Date(), nullable=False),
        sa.Column("due_date",           sa.Date(), nullable=False),
        sa.Column("balance_bf",         sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("payments_received",  sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("charges_total",      sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("taxes_total",        sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("charges_for_period", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("total_payable",      sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("status",             _invoice_status, nullable=False,
                  server_default=sa.text("'GENERATED'")),
        sa.Column("pdf_path",           sa.Text(), nullable=True),
        sa.Column("created_at",         sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_number"),
        sa.UniqueConstraint("account_id", "period_start", "period_end"),
    )

    op.create_table(
        "invoice_line_items",
        sa.Column("id",                 sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("invoice_id",         sa.BigInteger(), nullable=False),
        sa.Column("service_account_id", sa.BigInteger(), nullable=True),
        sa.Column("line_type",          _line_type, nullable=False),
        sa.Column("description",        sa.Text(), nullable=False),
        sa.Column("period_start",       sa.Date(), nullable=True),
        sa.Column("period_end",         sa.Date(), nullable=True),
        sa.Column("amount",             sa.Numeric(12, 2), nullable=False),
        sa.Column("sort_order",         sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["invoice_id"],         ["invoices.id"],         ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_account_id"], ["service_accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "payments",
        sa.Column("id",           sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("account_id",   sa.BigInteger(), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("method",       _payment_method, nullable=False,
                  server_default=sa.text("'PHYSICAL'")),
        sa.Column("amount",       sa.Numeric(12, 2), nullable=False),
        sa.Column("reference",    sa.Text(), nullable=True),
        sa.Column("created_at",   sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "billing_runs",
        sa.Column("id",             sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("period_start",   sa.Date(), nullable=False),
        sa.Column("period_end",     sa.Date(), nullable=False),
        sa.Column("status",         _run_status, nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("total_accounts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("succeeded",      sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("failed",         sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("started_at",     sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("finished_at",    sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "billing_run_failures",
        sa.Column("id",             sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("billing_run_id", sa.BigInteger(), nullable=False),
        sa.Column("account_id",     sa.BigInteger(), nullable=True),
        sa.Column("error_message",  sa.Text(), nullable=False),
        sa.Column("created_at",     sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["billing_run_id"], ["billing_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"],     ["accounts.id"],     ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # 3. Indexes
    # ------------------------------------------------------------------
    op.create_index("idx_accounts_customer",        "accounts",           ["customer_id"])
    op.create_index("idx_service_accounts_account", "service_accounts",   ["account_id"])
    op.create_index("idx_usage_service",            "usage_records",      ["service_account_id"])
    op.create_index("idx_invoices_account",         "invoices",           ["account_id"])
    op.create_index("idx_invoices_period",          "invoices",           ["period_start", "period_end"])
    op.create_index("idx_line_items_invoice",       "invoice_line_items", ["invoice_id"])
    op.create_index("idx_payments_account",         "payments",           ["account_id"])


def downgrade() -> None:
    # Indexes
    op.drop_index("idx_payments_account",         table_name="payments")
    op.drop_index("idx_line_items_invoice",        table_name="invoice_line_items")
    op.drop_index("idx_invoices_period",           table_name="invoices")
    op.drop_index("idx_invoices_account",          table_name="invoices")
    op.drop_index("idx_usage_service",             table_name="usage_records")
    op.drop_index("idx_service_accounts_account",  table_name="service_accounts")
    op.drop_index("idx_accounts_customer",         table_name="accounts")

    # Tables (reverse FK dependency order)
    op.drop_table("billing_run_failures")
    op.drop_table("billing_runs")
    op.drop_table("payments")
    op.drop_table("invoice_line_items")
    op.drop_table("invoices")
    op.drop_table("usage_records")
    op.drop_table("packages")
    op.drop_table("service_accounts")
    op.drop_table("accounts")
    op.drop_table("customers")
    op.drop_table("users")

    # Enum types — IF EXISTS so downgrade is safe even on a partial upgrade
    op.execute(sa.text("DROP TYPE IF EXISTS run_status"))
    op.execute(sa.text("DROP TYPE IF EXISTS payment_method"))
    op.execute(sa.text("DROP TYPE IF EXISTS invoice_status"))
    op.execute(sa.text("DROP TYPE IF EXISTS line_type"))
    op.execute(sa.text("DROP TYPE IF EXISTS service_type"))
    op.execute(sa.text("DROP TYPE IF EXISTS account_status"))
    op.execute(sa.text("DROP TYPE IF EXISTS user_role"))
