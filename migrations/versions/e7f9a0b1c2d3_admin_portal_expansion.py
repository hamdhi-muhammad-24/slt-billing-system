"""admin_portal_expansion

Revision ID: e7f9a0b1c2d3
Revises: d9e8f7a6b5c4
Create Date: 2026-07-03 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from alembic import op

revision: str = "e7f9a0b1c2d3"
down_revision: Union[str, Sequence[str], None] = "d9e8f7a6b5c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_pdf_generation_status = PgEnum("PENDING", "SUCCESS", "FAILED", name="pdf_generation_status", create_type=False)
_delivery_status = PgEnum("NOT_ENABLED", "PENDING", "SUCCESS", "FAILED", name="delivery_status", create_type=False)
_billing_run_item_overall_status = PgEnum(
    "PENDING",
    "GENERATED",
    "FAILED",
    "READY_TO_SEND",
    "COMPLETED",
    name="billing_run_item_overall_status",
    create_type=False,
)


def _create_enum(name: str, *values: str) -> None:
    labels = ", ".join(f"'{v}'" for v in values)
    op.execute(sa.text(
        f"DO $$ BEGIN "
        f"  CREATE TYPE {name} AS ENUM ({labels}); "
        f"EXCEPTION WHEN duplicate_object THEN NULL; "
        f"END $$"
    ))


def upgrade() -> None:
    _create_enum("pdf_generation_status", "PENDING", "SUCCESS", "FAILED")
    _create_enum("delivery_status", "NOT_ENABLED", "PENDING", "SUCCESS", "FAILED")
    _create_enum(
        "billing_run_item_overall_status",
        "PENDING",
        "GENERATED",
        "FAILED",
        "READY_TO_SEND",
        "COMPLETED",
    )

    op.create_table(
        "invoice_templates",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template_code", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_system_template", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("base_template_id", sa.BigInteger(), nullable=True),
        sa.Column("header_message", sa.Text(), nullable=True),
        sa.Column("footer_message", sa.Text(), nullable=True),
        sa.Column("promotion_message", sa.Text(), nullable=True),
        sa.Column("theme_name", sa.Text(), nullable=True),
        sa.Column("theme_color", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["base_template_id"], ["invoice_templates.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_code"),
    )
    op.create_index("idx_invoice_templates_active", "invoice_templates", ["is_active"])
    op.create_index("idx_invoice_templates_base", "invoice_templates", ["base_template_id"])

    op.add_column("billing_runs", sa.Column("template_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_billing_runs_template_id",
        "billing_runs",
        "invoice_templates",
        ["template_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("invoices", sa.Column("template_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_invoices_template_id",
        "invoices",
        "invoice_templates",
        ["template_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_invoices_template", "invoices", ["template_id"])

    op.create_table(
        "billing_run_items",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("billing_run_id", sa.BigInteger(), nullable=False),
        sa.Column("account_id", sa.BigInteger(), nullable=True),
        sa.Column("customer_id", sa.BigInteger(), nullable=True),
        sa.Column("invoice_id", sa.BigInteger(), nullable=True),
        sa.Column("template_id", sa.BigInteger(), nullable=True),
        sa.Column("pdf_status", _pdf_generation_status, nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("email_status", _delivery_status, nullable=False, server_default=sa.text("'NOT_ENABLED'")),
        sa.Column("sms_status", _delivery_status, nullable=False, server_default=sa.text("'NOT_ENABLED'")),
        sa.Column("overall_status", _billing_run_item_overall_status, nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["billing_run_id"], ["billing_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["template_id"], ["invoice_templates.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("billing_run_id", "account_id", name="uq_billing_run_items_run_account"),
    )
    op.create_index("idx_billing_run_items_run", "billing_run_items", ["billing_run_id"])
    op.create_index("idx_billing_run_items_account", "billing_run_items", ["account_id"])
    op.create_index("idx_billing_run_items_customer", "billing_run_items", ["customer_id"])
    op.create_index("idx_billing_run_items_invoice", "billing_run_items", ["invoice_id"])


def downgrade() -> None:
    op.drop_index("idx_billing_run_items_invoice", table_name="billing_run_items")
    op.drop_index("idx_billing_run_items_customer", table_name="billing_run_items")
    op.drop_index("idx_billing_run_items_account", table_name="billing_run_items")
    op.drop_index("idx_billing_run_items_run", table_name="billing_run_items")
    op.drop_table("billing_run_items")

    op.drop_index("idx_invoices_template", table_name="invoices")
    op.drop_constraint("fk_invoices_template_id", "invoices", type_="foreignkey")
    op.drop_column("invoices", "template_id")

    op.drop_constraint("fk_billing_runs_template_id", "billing_runs", type_="foreignkey")
    op.drop_column("billing_runs", "template_id")

    op.drop_index("idx_invoice_templates_base", table_name="invoice_templates")
    op.drop_index("idx_invoice_templates_active", table_name="invoice_templates")
    op.drop_table("invoice_templates")

    op.execute(sa.text("DROP TYPE IF EXISTS billing_run_item_overall_status"))
    op.execute(sa.text("DROP TYPE IF EXISTS delivery_status"))
    op.execute(sa.text("DROP TYPE IF EXISTS pdf_generation_status"))
