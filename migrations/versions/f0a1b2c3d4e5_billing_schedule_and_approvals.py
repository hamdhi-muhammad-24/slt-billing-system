"""billing_schedule_and_approvals

Revision ID: f0a1b2c3d4e5
Revises: e7f9a0b1c2d3
Create Date: 2026-07-04 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from alembic import op

revision: str = "f0a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "e7f9a0b1c2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_billing_schedule_mode = PgEnum("AUTOMATIC", "APPROVAL_REQUIRED", name="billing_schedule_mode", create_type=False)
_billing_approval_status = PgEnum("PENDING", "APPROVED", "REJECTED", "EXPIRED", name="billing_approval_status", create_type=False)


def _create_enum(name: str, *values: str) -> None:
    labels = ", ".join(f"'{v}'" for v in values)
    op.execute(sa.text(
        f"DO $$ BEGIN "
        f"  CREATE TYPE {name} AS ENUM ({labels}); "
        f"EXCEPTION WHEN duplicate_object THEN NULL; "
        f"END $$"
    ))


def upgrade() -> None:
    _create_enum("billing_schedule_mode", "AUTOMATIC", "APPROVAL_REQUIRED")
    _create_enum("billing_approval_status", "PENDING", "APPROVED", "REJECTED", "EXPIRED")

    op.add_column("billing_run_items", sa.Column("email_failure_reason", sa.Text(), nullable=True))
    op.add_column("billing_run_items", sa.Column("sms_failure_reason", sa.Text(), nullable=True))
    op.add_column("billing_run_items", sa.Column("email_provider_ref", sa.Text(), nullable=True))
    op.add_column("billing_run_items", sa.Column("sms_provider_ref", sa.Text(), nullable=True))

    op.create_table(
        "billing_schedules",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False, server_default=sa.text("'Monthly SLT billing'")),
        sa.Column("day_of_month", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("run_time", sa.Text(), nullable=False, server_default=sa.text("'02:00'")),
        sa.Column("timezone", sa.Text(), nullable=False, server_default=sa.text("'Asia/Colombo'")),
        sa.Column("schedule_mode", _billing_schedule_mode, nullable=False, server_default=sa.text("'AUTOMATIC'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("send_email", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("send_sms", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("approval_lead_days", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("approval_email", sa.Text(), nullable=True),
        sa.Column("last_triggered_period", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "billing_run_approvals",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("billing_schedule_id", sa.BigInteger(), nullable=False),
        sa.Column("billing_run_id", sa.BigInteger(), nullable=True),
        sa.Column("period", sa.Text(), nullable=False),
        sa.Column("status", _billing_approval_status, nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("requested_to", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["billing_run_id"], ["billing_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["billing_schedule_id"], ["billing_schedules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["decided_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("billing_schedule_id", "period", name="uq_billing_run_approvals_schedule_period"),
    )
    op.create_index("idx_billing_run_approvals_schedule", "billing_run_approvals", ["billing_schedule_id"])
    op.create_index("idx_billing_run_approvals_run", "billing_run_approvals", ["billing_run_id"])


def downgrade() -> None:
    op.drop_index("idx_billing_run_approvals_run", table_name="billing_run_approvals")
    op.drop_index("idx_billing_run_approvals_schedule", table_name="billing_run_approvals")
    op.drop_table("billing_run_approvals")
    op.drop_table("billing_schedules")

    op.drop_column("billing_run_items", "sms_provider_ref")
    op.drop_column("billing_run_items", "email_provider_ref")
    op.drop_column("billing_run_items", "sms_failure_reason")
    op.drop_column("billing_run_items", "email_failure_reason")

    op.execute(sa.text("DROP TYPE IF EXISTS billing_approval_status"))
    op.execute(sa.text("DROP TYPE IF EXISTS billing_schedule_mode"))
