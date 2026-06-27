"""realistic_slt_database_upgrade

Revision ID: d9e8f7a6b5c4
Revises: c1d2e3f4a5b6
Create Date: 2026-06-27 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from alembic import op

revision: str = "d9e8f7a6b5c4"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_customer_type = PgEnum("RESIDENTIAL", "BUSINESS", name="customer_type", create_type=False)
_address_type = PgEnum("BILLING", "SERVICE", "POSTAL", name="address_type", create_type=False)
_bill_delivery_method = PgEnum("EMAIL", "SMS", "POSTAL", "PORTAL", name="bill_delivery_method", create_type=False)
_connection_type = PgEnum("FTTH", "ADSL", "LTE", "VOICE", "PEOTV", "OTHER", name="connection_type", create_type=False)
_payment_status = PgEnum("PENDING", "POSTED", "FAILED", "REVERSED", name="payment_status", create_type=False)
_request_type = PgEnum(
    "NEW_SERVICE",
    "PACKAGE_UPGRADE",
    "PACKAGE_DOWNGRADE",
    "RELOCATION",
    "DISCONNECTION",
    name="request_type",
    create_type=False,
)
_request_status = PgEnum("OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED", name="request_status", create_type=False)
_fault_status = PgEnum("OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED", name="fault_status", create_type=False)


def _create_enum(name: str, *values: str) -> None:
    labels = ", ".join(f"'{v}'" for v in values)
    op.execute(sa.text(
        f"DO $$ BEGIN "
        f"  CREATE TYPE {name} AS ENUM ({labels}); "
        f"EXCEPTION WHEN duplicate_object THEN NULL; "
        f"END $$"
    ))


def upgrade() -> None:
    _create_enum("customer_type", "RESIDENTIAL", "BUSINESS")
    _create_enum("address_type", "BILLING", "SERVICE", "POSTAL")
    _create_enum("bill_delivery_method", "EMAIL", "SMS", "POSTAL", "PORTAL")
    _create_enum("connection_type", "FTTH", "ADSL", "LTE", "VOICE", "PEOTV", "OTHER")
    _create_enum("payment_status", "PENDING", "POSTED", "FAILED", "REVERSED")
    _create_enum("request_type", "NEW_SERVICE", "PACKAGE_UPGRADE", "PACKAGE_DOWNGRADE", "RELOCATION", "DISCONNECTION")
    _create_enum("request_status", "OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED")
    _create_enum("fault_status", "OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED")

    op.add_column("customers", sa.Column("nic", sa.Text(), nullable=True))
    op.add_column("customers", sa.Column("title", sa.Text(), nullable=True))
    op.add_column("customers", sa.Column("first_name", sa.Text(), nullable=True))
    op.add_column("customers", sa.Column("last_name", sa.Text(), nullable=True))
    op.add_column("customers", sa.Column("email", sa.Text(), nullable=True))
    op.add_column("customers", sa.Column("mobile_number", sa.Text(), nullable=True))
    op.add_column("customers", sa.Column("alternate_phone", sa.Text(), nullable=True))
    op.add_column("customers", sa.Column("preferred_language", sa.Text(), nullable=False, server_default=sa.text("'en'")))
    op.add_column("customers", sa.Column("date_of_birth", sa.Date(), nullable=True))
    op.add_column("customers", sa.Column("customer_type", _customer_type, nullable=False, server_default=sa.text("'RESIDENTIAL'")))
    op.create_unique_constraint("uq_customers_nic", "customers", ["nic"])

    op.create_table(
        "customer_addresses",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("address_type", _address_type, nullable=False),
        sa.Column("line1", sa.Text(), nullable=False),
        sa.Column("line2", sa.Text(), nullable=True),
        sa.Column("city", sa.Text(), nullable=True),
        sa.Column("district", sa.Text(), nullable=True),
        sa.Column("province", sa.Text(), nullable=True),
        sa.Column("postal_code", sa.Text(), nullable=True),
        sa.Column("country", sa.Text(), nullable=False, server_default=sa.text("'Sri Lanka'")),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_customer_addresses_customer", "customer_addresses", ["customer_id"])
    op.execute(sa.text("""
        INSERT INTO customer_addresses (customer_id, address_type, line1, line2, city, postal_code)
        SELECT id, 'BILLING'::address_type, address_line1, address_line2, city, postal_code
        FROM customers
        WHERE address_line1 IS NOT NULL
    """))

    op.add_column("accounts", sa.Column("billing_cycle", sa.Text(), nullable=False, server_default=sa.text("'MONTHLY_25'")))
    op.add_column("accounts", sa.Column("bill_delivery_method", _bill_delivery_method, nullable=False, server_default=sa.text("'PORTAL'")))
    op.add_column("accounts", sa.Column("credit_limit", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")))
    op.add_column("accounts", sa.Column("deposit_amount", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")))
    op.add_column("accounts", sa.Column("opened_on", sa.Date(), nullable=True))
    op.add_column("accounts", sa.Column("closed_on", sa.Date(), nullable=True))
    op.add_column("accounts", sa.Column("last_billed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("accounts", sa.Column("notify_email", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("accounts", sa.Column("notify_sms", sa.Boolean(), nullable=False, server_default=sa.text("true")))

    op.add_column("packages", sa.Column("package_code", sa.Text(), nullable=True))
    op.add_column("packages", sa.Column("speed_tier", sa.Text(), nullable=True))
    op.add_column("packages", sa.Column("anytime_gb", sa.Numeric(10, 2), nullable=True))
    op.add_column("packages", sa.Column("peak_gb", sa.Numeric(10, 2), nullable=True))
    op.add_column("packages", sa.Column("offpeak_gb", sa.Numeric(10, 2), nullable=True))
    op.add_column("packages", sa.Column("included_voice_minutes", sa.Numeric(12, 3), nullable=True))
    op.add_column("packages", sa.Column("active_from", sa.Date(), nullable=True))
    op.add_column("packages", sa.Column("active_to", sa.Date(), nullable=True))
    op.add_column("packages", sa.Column("tax_applicable", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.create_unique_constraint("uq_packages_package_code", "packages", ["package_code"])

    op.add_column("service_accounts", sa.Column("package_id", sa.BigInteger(), nullable=True))
    op.add_column("service_accounts", sa.Column("installation_address_id", sa.BigInteger(), nullable=True))
    op.add_column("service_accounts", sa.Column("connection_type", _connection_type, nullable=False, server_default=sa.text("'OTHER'")))
    op.add_column("service_accounts", sa.Column("activated_on", sa.Date(), nullable=True))
    op.add_column("service_accounts", sa.Column("contract_number", sa.Text(), nullable=True))
    op.add_column("service_accounts", sa.Column("router_serial", sa.Text(), nullable=True))
    op.add_column("service_accounts", sa.Column("ont_serial", sa.Text(), nullable=True))
    op.add_column("service_accounts", sa.Column("service_username", sa.Text(), nullable=True))
    op.add_column("service_accounts", sa.Column("status", sa.Enum("ACTIVE", "SUSPENDED", "CLOSED", name="account_status", create_type=False), nullable=False, server_default=sa.text("'ACTIVE'")))
    op.create_foreign_key("fk_service_accounts_package_id", "service_accounts", "packages", ["package_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_service_accounts_installation_address_id", "service_accounts", "customer_addresses", ["installation_address_id"], ["id"], ondelete="SET NULL")

    op.create_table(
        "billing_periods",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("billing_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "usage_summaries",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("service_account_id", sa.BigInteger(), nullable=False),
        sa.Column("billing_period_id", sa.BigInteger(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("metric", sa.Text(), nullable=False),
        sa.Column("included_quantity", sa.Numeric(12, 3), nullable=False, server_default=sa.text("0")),
        sa.Column("used_quantity", sa.Numeric(12, 3), nullable=False, server_default=sa.text("0")),
        sa.Column("remaining_quantity", sa.Numeric(12, 3), nullable=False, server_default=sa.text("0")),
        sa.Column("overage_quantity", sa.Numeric(12, 3), nullable=False, server_default=sa.text("0")),
        sa.Column("charge", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["billing_period_id"], ["billing_periods.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_account_id"], ["service_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("service_account_id", "billing_period_id", "metric", name="uq_usage_summary_service_period_metric"),
    )
    op.create_index("idx_usage_summaries_service", "usage_summaries", ["service_account_id"])
    op.create_index("idx_usage_summaries_period", "usage_summaries", ["billing_period_id"])

    op.create_table(
        "daily_usage_records",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("service_account_id", sa.BigInteger(), nullable=False),
        sa.Column("billing_period_id", sa.BigInteger(), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("bucket", sa.Text(), nullable=False, server_default=sa.text("'ANYTIME'")),
        sa.Column("protocol", sa.Text(), nullable=True),
        sa.Column("app_category", sa.Text(), nullable=True),
        sa.Column("download_gb", sa.Numeric(12, 3), nullable=False, server_default=sa.text("0")),
        sa.Column("upload_gb", sa.Numeric(12, 3), nullable=False, server_default=sa.text("0")),
        sa.Column("total_gb", sa.Numeric(12, 3), nullable=False, server_default=sa.text("0")),
        sa.Column("charge", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["billing_period_id"], ["billing_periods.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_account_id"], ["service_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_daily_usage_service_date", "daily_usage_records", ["service_account_id", "usage_date"])
    op.create_index("idx_daily_usage_period", "daily_usage_records", ["billing_period_id"])

    op.create_table(
        "service_addons",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("service_account_id", sa.BigInteger(), nullable=False),
        sa.Column("billing_period_id", sa.BigInteger(), nullable=False),
        sa.Column("addon_name", sa.Text(), nullable=False),
        sa.Column("addon_type", sa.Text(), nullable=False, server_default=sa.text("'EXTRA_GB'")),
        sa.Column("purchased_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=False),
        sa.Column("quantity_gb", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("remaining_gb", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("charge", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["billing_period_id"], ["billing_periods.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_account_id"], ["service_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_service_addons_service", "service_addons", ["service_account_id"])
    op.create_index("idx_service_addons_period", "service_addons", ["billing_period_id"])

    op.add_column("invoices", sa.Column("snapshot_customer_name", sa.Text(), nullable=True))
    op.add_column("invoices", sa.Column("snapshot_customer_nic", sa.Text(), nullable=True))
    op.add_column("invoices", sa.Column("snapshot_bill_address", sa.Text(), nullable=True))
    op.add_column("invoices", sa.Column("snapshot_account_number", sa.Text(), nullable=True))
    op.add_column("invoices", sa.Column("snapshot_telephone_number", sa.Text(), nullable=True))
    op.add_column("invoices", sa.Column("snapshot_package_name", sa.Text(), nullable=True))
    op.add_column("invoices", sa.Column("snapshot_service_label", sa.Text(), nullable=True))
    op.execute(sa.text("""
        UPDATE invoices i
        SET snapshot_customer_name = c.full_name,
            snapshot_customer_nic = c.nic,
            snapshot_bill_address = concat_ws(', ', c.address_line1, c.address_line2, c.city, c.postal_code),
            snapshot_account_number = a.account_number,
            snapshot_telephone_number = a.telephone_number,
            snapshot_service_label = a.service_label
        FROM accounts a
        JOIN customers c ON c.id = a.customer_id
        WHERE i.account_id = a.id
    """))

    op.add_column("payments", sa.Column("invoice_id", sa.BigInteger(), nullable=True))
    op.add_column("payments", sa.Column("status", _payment_status, nullable=False, server_default=sa.text("'POSTED'")))
    op.add_column("payments", sa.Column("receipt_number", sa.Text(), nullable=True))
    op.add_column("payments", sa.Column("provider", sa.Text(), nullable=True))
    op.add_column("payments", sa.Column("provider_reference", sa.Text(), nullable=True))
    op.add_column("payments", sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_payments_invoice_id", "payments", "invoices", ["invoice_id"], ["id"], ondelete="SET NULL")

    op.create_table(
        "service_requests",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("service_account_id", sa.BigInteger(), nullable=True),
        sa.Column("request_type", _request_type, nullable=False),
        sa.Column("status", _request_status, nullable=False, server_default=sa.text("'OPEN'")),
        sa.Column("requested_package_id", sa.BigInteger(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_package_id"], ["packages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["service_account_id"], ["service_accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_service_requests_customer", "service_requests", ["customer_id"])
    op.create_index("idx_service_requests_account", "service_requests", ["account_id"])

    op.create_table(
        "fault_tickets",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("service_account_id", sa.BigInteger(), nullable=True),
        sa.Column("ticket_number", sa.Text(), nullable=False),
        sa.Column("status", _fault_status, nullable=False, server_default=sa.text("'OPEN'")),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_account_id"], ["service_accounts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_number"),
    )
    op.create_index("idx_fault_tickets_customer", "fault_tickets", ["customer_id"])
    op.create_index("idx_fault_tickets_account", "fault_tickets", ["account_id"])


def downgrade() -> None:
    op.drop_index("idx_fault_tickets_account", table_name="fault_tickets")
    op.drop_index("idx_fault_tickets_customer", table_name="fault_tickets")
    op.drop_table("fault_tickets")
    op.drop_index("idx_service_requests_account", table_name="service_requests")
    op.drop_index("idx_service_requests_customer", table_name="service_requests")
    op.drop_table("service_requests")
    op.drop_constraint("fk_payments_invoice_id", "payments", type_="foreignkey")
    for column in ("posted_at", "provider_reference", "provider", "receipt_number", "status", "invoice_id"):
        op.drop_column("payments", column)
    for column in (
        "snapshot_service_label",
        "snapshot_package_name",
        "snapshot_telephone_number",
        "snapshot_account_number",
        "snapshot_bill_address",
        "snapshot_customer_nic",
        "snapshot_customer_name",
    ):
        op.drop_column("invoices", column)
    op.drop_index("idx_service_addons_period", table_name="service_addons")
    op.drop_index("idx_service_addons_service", table_name="service_addons")
    op.drop_table("service_addons")
    op.drop_index("idx_daily_usage_period", table_name="daily_usage_records")
    op.drop_index("idx_daily_usage_service_date", table_name="daily_usage_records")
    op.drop_table("daily_usage_records")
    op.drop_index("idx_usage_summaries_period", table_name="usage_summaries")
    op.drop_index("idx_usage_summaries_service", table_name="usage_summaries")
    op.drop_table("usage_summaries")
    op.drop_table("billing_periods")
    op.drop_constraint("fk_service_accounts_installation_address_id", "service_accounts", type_="foreignkey")
    op.drop_constraint("fk_service_accounts_package_id", "service_accounts", type_="foreignkey")
    for column in (
        "status",
        "service_username",
        "ont_serial",
        "router_serial",
        "contract_number",
        "activated_on",
        "connection_type",
        "installation_address_id",
        "package_id",
    ):
        op.drop_column("service_accounts", column)
    op.drop_constraint("uq_packages_package_code", "packages", type_="unique")
    for column in (
        "tax_applicable",
        "active_to",
        "active_from",
        "included_voice_minutes",
        "offpeak_gb",
        "peak_gb",
        "anytime_gb",
        "speed_tier",
        "package_code",
    ):
        op.drop_column("packages", column)
    for column in (
        "notify_sms",
        "notify_email",
        "last_billed_at",
        "closed_on",
        "opened_on",
        "deposit_amount",
        "credit_limit",
        "bill_delivery_method",
        "billing_cycle",
    ):
        op.drop_column("accounts", column)
    op.drop_index("idx_customer_addresses_customer", table_name="customer_addresses")
    op.drop_table("customer_addresses")
    op.drop_constraint("uq_customers_nic", "customers", type_="unique")
    for column in (
        "customer_type",
        "date_of_birth",
        "preferred_language",
        "alternate_phone",
        "mobile_number",
        "email",
        "last_name",
        "first_name",
        "title",
        "nic",
    ):
        op.drop_column("customers", column)
    for enum_name in (
        "fault_status",
        "request_status",
        "request_type",
        "payment_status",
        "connection_type",
        "bill_delivery_method",
        "address_type",
        "customer_type",
    ):
        op.execute(sa.text(f"DROP TYPE IF EXISTS {enum_name}"))
