"""add_notification_outbox

Revision ID: c1d2e3f4a5b6
Revises: a3f8d012e4c1
Create Date: 2026-06-23 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from alembic import op

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "a3f8d012e4c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_notification_channel = PgEnum("EMAIL", "SMS",                  name="notification_channel", create_type=False)
_notification_status  = PgEnum("QUEUED", "SENT", "FAILED",      name="notification_status",  create_type=False)


def _create_enum(name: str, *values: str) -> None:
    labels = ", ".join(f"'{v}'" for v in values)
    op.execute(sa.text(
        f"DO $$ BEGIN "
        f"  CREATE TYPE {name} AS ENUM ({labels}); "
        f"EXCEPTION WHEN duplicate_object THEN NULL; "
        f"END $$"
    ))


def upgrade() -> None:
    _create_enum("notification_channel", "EMAIL", "SMS")
    _create_enum("notification_status",  "QUEUED", "SENT", "FAILED")

    op.create_table(
        "notification_outbox",
        sa.Column("id",           sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("invoice_id",   sa.BigInteger(), nullable=False),
        sa.Column("channel",      _notification_channel, nullable=False),
        sa.Column("status",       _notification_status,  nullable=False, server_default=sa.text("'QUEUED'")),
        sa.Column("recipient",    sa.Text(), nullable=False),
        sa.Column("attempts",     sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_error",   sa.Text(), nullable=True),
        sa.Column("provider_ref", sa.Text(), nullable=True),
        sa.Column("created_at",   sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("sent_at",      sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_id", "channel", name="uq_outbox_invoice_channel"),
    )


def downgrade() -> None:
    op.drop_table("notification_outbox")
    op.execute(sa.text("DROP TYPE IF EXISTS notification_status"))
    op.execute(sa.text("DROP TYPE IF EXISTS notification_channel"))
