"""remove old models

Revision ID: f83db6b9b904
Revises: de4394329a97
Create Date: 2026-07-07 14:26:34.771370

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f83db6b9b904'
down_revision: Union[str, Sequence[str], None] = 'de4394329a97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DROP TABLE IF EXISTS service_requests CASCADE")
    op.execute("DROP TABLE IF EXISTS payments CASCADE")
    op.execute("DROP TABLE IF EXISTS accounts CASCADE")
    op.execute("DROP TABLE IF EXISTS usage_records CASCADE")
    op.execute("DROP TABLE IF EXISTS packages CASCADE")
    op.execute("DROP TABLE IF EXISTS customers CASCADE")
    op.execute("DROP TABLE IF EXISTS customer_addresses CASCADE")
    op.execute("DROP TABLE IF EXISTS usage_summaries CASCADE")
    op.execute("DROP TABLE IF EXISTS billing_periods CASCADE")
    op.execute("DROP TABLE IF EXISTS service_accounts CASCADE")
    op.execute("DROP TABLE IF EXISTS daily_usage_records CASCADE")
    op.execute("DROP TABLE IF EXISTS invoice_line_items CASCADE")
    op.execute("DROP TABLE IF EXISTS service_addons CASCADE")
    op.execute("DROP TABLE IF EXISTS fault_tickets CASCADE")

    op.add_column('billing_run_approvals', sa.Column('batch_name', sa.Text(), nullable=False, server_default='batch'))
    op.drop_index(op.f('idx_billing_run_approvals_run'), table_name='billing_run_approvals')
    op.drop_index(op.f('idx_billing_run_approvals_schedule'), table_name='billing_run_approvals')
    op.drop_constraint(op.f('uq_billing_run_approvals_schedule_period'), 'billing_run_approvals', type_='unique')
    op.add_column('billing_run_failures', sa.Column('account_number', sa.Text(), nullable=True))
    op.drop_column('billing_run_failures', 'account_id')
    op.add_column('billing_run_items', sa.Column('account_number', sa.Text(), nullable=True))
    op.drop_index(op.f('idx_billing_run_items_account'), table_name='billing_run_items')
    op.drop_index(op.f('idx_billing_run_items_customer'), table_name='billing_run_items')
    op.drop_index(op.f('idx_billing_run_items_invoice'), table_name='billing_run_items')
    op.drop_index(op.f('idx_billing_run_items_run'), table_name='billing_run_items')
    op.drop_constraint(op.f('uq_billing_run_items_run_account'), 'billing_run_items', type_='unique')
    op.drop_column('billing_run_items', 'sms_provider_ref')
    op.drop_column('billing_run_items', 'sms_status')
    op.drop_column('billing_run_items', 'email_provider_ref')
    op.drop_column('billing_run_items', 'account_id')
    op.drop_column('billing_run_items', 'email_status')
    op.drop_column('billing_run_items', 'sms_failure_reason')
    op.drop_column('billing_run_items', 'customer_id')
    op.drop_column('billing_run_items', 'email_failure_reason')
    op.add_column('billing_runs', sa.Column('batch_name', sa.Text(), nullable=False, server_default='batch'))
    op.add_column('billing_runs', sa.Column('zip_path', sa.Text(), nullable=True))
    op.drop_constraint('fk_billing_runs_template_id', 'billing_runs', type_='foreignkey')
    op.drop_column('billing_runs', 'template_id')
    op.drop_column('billing_schedules', 'send_sms')
    op.drop_column('billing_schedules', 'send_email')
    op.add_column('invoices', sa.Column('account_number', sa.Text(), nullable=False, server_default='000'))
    op.add_column('invoices', sa.Column('zip_path', sa.Text(), nullable=True))
    op.add_column('invoices', sa.Column('batch_name', sa.Text(), nullable=True))
    op.alter_column('invoices', 'status',
               existing_type=postgresql.ENUM('DRAFT', 'GENERATED', 'SENT', 'PAID', 'OVERDUE', 'CANCELLED', name='invoice_status'),
               type_=sa.Text(),
               existing_nullable=False,
               existing_server_default=sa.text("'GENERATED'::invoice_status"))
    op.drop_index(op.f('idx_invoices_account'), table_name='invoices')
    op.drop_index(op.f('idx_invoices_period'), table_name='invoices')
    op.drop_index(op.f('idx_invoices_template'), table_name='invoices')
    op.drop_constraint('invoices_account_id_period_start_period_end_key', 'invoices', type_='unique')
    op.drop_column('invoices', 'balance_bf')
    op.drop_column('invoices', 'payments_received')
    op.drop_column('invoices', 'charges_total')
    op.drop_column('invoices', 'snapshot_package_name')
    op.drop_column('invoices', 'due_date')
    op.drop_column('invoices', 'account_id')
    op.drop_column('invoices', 'snapshot_account_number')
    op.drop_column('invoices', 'snapshot_bill_address')
    op.drop_column('invoices', 'charges_for_period')
    op.drop_column('invoices', 'snapshot_service_label')
    op.drop_column('invoices', 'snapshot_telephone_number')
    op.drop_column('invoices', 'snapshot_customer_name')
    op.drop_column('invoices', 'total_payable')
    op.drop_column('invoices', 'snapshot_customer_nic')
    op.drop_column('invoices', 'taxes_total')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('invoices', sa.Column('taxes_total', sa.NUMERIC(precision=12, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=False))
    op.add_column('invoices', sa.Column('snapshot_customer_nic', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('invoices', sa.Column('total_payable', sa.NUMERIC(precision=12, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=False))
    op.add_column('invoices', sa.Column('snapshot_customer_name', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('invoices', sa.Column('snapshot_telephone_number', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('invoices', sa.Column('snapshot_service_label', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('invoices', sa.Column('charges_for_period', sa.NUMERIC(precision=12, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=False))
    op.add_column('invoices', sa.Column('snapshot_bill_address', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('invoices', sa.Column('snapshot_account_number', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('invoices', sa.Column('account_id', sa.BIGINT(), autoincrement=False, nullable=False))
    op.add_column('invoices', sa.Column('due_date', sa.DATE(), autoincrement=False, nullable=False))
    op.add_column('invoices', sa.Column('snapshot_package_name', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('invoices', sa.Column('charges_total', sa.NUMERIC(precision=12, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=False))
    op.add_column('invoices', sa.Column('payments_received', sa.NUMERIC(precision=12, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=False))
    op.add_column('invoices', sa.Column('balance_bf', sa.NUMERIC(precision=12, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=False))
    op.create_foreign_key(op.f('invoices_account_id_fkey'), 'invoices', 'accounts', ['account_id'], ['id'], ondelete='RESTRICT')
    op.create_unique_constraint(op.f('invoices_account_id_period_start_period_end_key'), 'invoices', ['account_id', 'period_start', 'period_end'], postgresql_nulls_not_distinct=False)
    op.create_index(op.f('idx_invoices_template'), 'invoices', ['template_id'], unique=False)
    op.create_index(op.f('idx_invoices_period'), 'invoices', ['period_start', 'period_end'], unique=False)
    op.create_index(op.f('idx_invoices_account'), 'invoices', ['account_id'], unique=False)
    op.alter_column('invoices', 'status',
               existing_type=sa.Text(),
               type_=postgresql.ENUM('DRAFT', 'GENERATED', 'SENT', 'PAID', 'OVERDUE', 'CANCELLED', name='invoice_status'),
               existing_nullable=False,
               existing_server_default=sa.text("'GENERATED'::invoice_status"))
    op.drop_column('invoices', 'batch_name')
    op.drop_column('invoices', 'zip_path')
    op.drop_column('invoices', 'account_number')
    op.add_column('billing_schedules', sa.Column('send_email', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False))
    op.add_column('billing_schedules', sa.Column('send_sms', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False))
    op.add_column('billing_runs', sa.Column('template_id', sa.BIGINT(), autoincrement=False, nullable=True))
    op.create_foreign_key(op.f('fk_billing_runs_template_id'), 'billing_runs', 'invoice_templates', ['template_id'], ['id'], ondelete='SET NULL')
    op.drop_column('billing_runs', 'zip_path')
    op.drop_column('billing_runs', 'batch_name')
    op.add_column('billing_run_items', sa.Column('email_failure_reason', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('billing_run_items', sa.Column('customer_id', sa.BIGINT(), autoincrement=False, nullable=True))
    op.add_column('billing_run_items', sa.Column('sms_failure_reason', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('billing_run_items', sa.Column('email_status', postgresql.ENUM('NOT_ENABLED', 'PENDING', 'SUCCESS', 'FAILED', name='delivery_status'), server_default=sa.text("'NOT_ENABLED'::delivery_status"), autoincrement=False, nullable=False))
    op.add_column('billing_run_items', sa.Column('account_id', sa.BIGINT(), autoincrement=False, nullable=True))
    op.add_column('billing_run_items', sa.Column('email_provider_ref', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('billing_run_items', sa.Column('sms_status', postgresql.ENUM('NOT_ENABLED', 'PENDING', 'SUCCESS', 'FAILED', name='delivery_status'), server_default=sa.text("'NOT_ENABLED'::delivery_status"), autoincrement=False, nullable=False))
    op.add_column('billing_run_items', sa.Column('sms_provider_ref', sa.TEXT(), autoincrement=False, nullable=True))
    op.create_foreign_key(op.f('billing_run_items_account_id_fkey'), 'billing_run_items', 'accounts', ['account_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(op.f('billing_run_items_customer_id_fkey'), 'billing_run_items', 'customers', ['customer_id'], ['id'], ondelete='SET NULL')
    op.create_unique_constraint(op.f('uq_billing_run_items_run_account'), 'billing_run_items', ['billing_run_id', 'account_id'], postgresql_nulls_not_distinct=False)
    op.create_index(op.f('idx_billing_run_items_run'), 'billing_run_items', ['billing_run_id'], unique=False)
    op.create_index(op.f('idx_billing_run_items_invoice'), 'billing_run_items', ['invoice_id'], unique=False)
    op.create_index(op.f('idx_billing_run_items_customer'), 'billing_run_items', ['customer_id'], unique=False)
    op.create_index(op.f('idx_billing_run_items_account'), 'billing_run_items', ['account_id'], unique=False)
    op.drop_column('billing_run_items', 'account_number')
    op.add_column('billing_run_failures', sa.Column('account_id', sa.BIGINT(), autoincrement=False, nullable=True))
    op.create_foreign_key(op.f('billing_run_failures_account_id_fkey'), 'billing_run_failures', 'accounts', ['account_id'], ['id'], ondelete='SET NULL')
    op.drop_column('billing_run_failures', 'account_number')
    op.create_unique_constraint(op.f('uq_billing_run_approvals_schedule_period'), 'billing_run_approvals', ['billing_schedule_id', 'period'], postgresql_nulls_not_distinct=False)
    op.create_index(op.f('idx_billing_run_approvals_schedule'), 'billing_run_approvals', ['billing_schedule_id'], unique=False)
    op.create_index(op.f('idx_billing_run_approvals_run'), 'billing_run_approvals', ['billing_run_id'], unique=False)
    op.drop_column('billing_run_approvals', 'batch_name')
    op.create_table('fault_tickets',
    sa.Column('id', sa.BIGINT(), sa.Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), autoincrement=True, nullable=False),
    sa.Column('customer_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('account_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('service_account_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('ticket_number', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('status', postgresql.ENUM('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', name='fault_status'), server_default=sa.text("'OPEN'::fault_status"), autoincrement=False, nullable=False),
    sa.Column('category', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('opened_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('resolved_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fault_tickets_account_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], name=op.f('fault_tickets_customer_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['service_account_id'], ['service_accounts.id'], name=op.f('fault_tickets_service_account_id_fkey'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('fault_tickets_pkey')),
    sa.UniqueConstraint('ticket_number', name=op.f('fault_tickets_ticket_number_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('idx_fault_tickets_customer'), 'fault_tickets', ['customer_id'], unique=False)
    op.create_index(op.f('idx_fault_tickets_account'), 'fault_tickets', ['account_id'], unique=False)
    op.create_table('service_addons',
    sa.Column('id', sa.BIGINT(), sa.Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), autoincrement=True, nullable=False),
    sa.Column('service_account_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('billing_period_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('addon_name', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('addon_type', sa.TEXT(), server_default=sa.text("'EXTRA_GB'::text"), autoincrement=False, nullable=False),
    sa.Column('purchased_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('valid_from', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('valid_to', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('quantity_gb', sa.NUMERIC(precision=10, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('remaining_gb', sa.NUMERIC(precision=10, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('charge', sa.NUMERIC(precision=12, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['billing_period_id'], ['billing_periods.id'], name=op.f('service_addons_billing_period_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['service_account_id'], ['service_accounts.id'], name=op.f('service_addons_service_account_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('service_addons_pkey'))
    )
    op.create_index(op.f('idx_service_addons_service'), 'service_addons', ['service_account_id'], unique=False)
    op.create_index(op.f('idx_service_addons_period'), 'service_addons', ['billing_period_id'], unique=False)
    op.create_table('invoice_line_items',
    sa.Column('id', sa.BIGINT(), sa.Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), autoincrement=True, nullable=False),
    sa.Column('invoice_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('service_account_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('line_type', postgresql.ENUM('RENTAL', 'USAGE', 'DISCOUNT', 'TAX', 'FEE', 'ADJUSTMENT', name='line_type'), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('period_start', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('period_end', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('amount', sa.NUMERIC(precision=12, scale=2), autoincrement=False, nullable=False),
    sa.Column('sort_order', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], name=op.f('invoice_line_items_invoice_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['service_account_id'], ['service_accounts.id'], name=op.f('invoice_line_items_service_account_id_fkey'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('invoice_line_items_pkey'))
    )
    op.create_index(op.f('idx_line_items_invoice'), 'invoice_line_items', ['invoice_id'], unique=False)
    op.create_table('daily_usage_records',
    sa.Column('id', sa.BIGINT(), sa.Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), autoincrement=True, nullable=False),
    sa.Column('service_account_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('billing_period_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('usage_date', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('bucket', sa.TEXT(), server_default=sa.text("'ANYTIME'::text"), autoincrement=False, nullable=False),
    sa.Column('protocol', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('app_category', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('download_gb', sa.NUMERIC(precision=12, scale=3), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('upload_gb', sa.NUMERIC(precision=12, scale=3), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('total_gb', sa.NUMERIC(precision=12, scale=3), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('charge', sa.NUMERIC(precision=12, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['billing_period_id'], ['billing_periods.id'], name=op.f('daily_usage_records_billing_period_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['service_account_id'], ['service_accounts.id'], name=op.f('daily_usage_records_service_account_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('daily_usage_records_pkey'))
    )
    op.create_index(op.f('idx_daily_usage_service_date'), 'daily_usage_records', ['service_account_id', 'usage_date'], unique=False)
    op.create_index(op.f('idx_daily_usage_period'), 'daily_usage_records', ['billing_period_id'], unique=False)
    op.create_table('service_accounts',
    sa.Column('id', sa.BIGINT(), sa.Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), autoincrement=True, nullable=False),
    sa.Column('account_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('service_number', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('service_type', postgresql.ENUM('VOICE', 'BROADBAND', 'PEOTV', 'BUNDLE', 'OTHER', name='service_type'), autoincrement=False, nullable=False),
    sa.Column('label', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('package_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('installation_address_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('connection_type', postgresql.ENUM('FTTH', 'ADSL', 'LTE', 'VOICE', 'PEOTV', 'OTHER', name='connection_type'), server_default=sa.text("'OTHER'::connection_type"), autoincrement=False, nullable=False),
    sa.Column('activated_on', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('contract_number', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('router_serial', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('ont_serial', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('service_username', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('status', postgresql.ENUM('ACTIVE', 'SUSPENDED', 'CLOSED', name='account_status'), server_default=sa.text("'ACTIVE'::account_status"), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('service_accounts_account_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['installation_address_id'], ['customer_addresses.id'], name=op.f('fk_service_accounts_installation_address_id'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['package_id'], ['packages.id'], name=op.f('fk_service_accounts_package_id'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('service_accounts_pkey'))
    )
    op.create_index(op.f('idx_service_accounts_account'), 'service_accounts', ['account_id'], unique=False)
    op.create_table('billing_periods',
    sa.Column('id', sa.BIGINT(), sa.Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), autoincrement=True, nullable=False),
    sa.Column('code', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('period_start', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('period_end', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('billing_date', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('due_date', sa.DATE(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('billing_periods_pkey')),
    sa.UniqueConstraint('code', name=op.f('billing_periods_code_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_table('usage_summaries',
    sa.Column('id', sa.BIGINT(), sa.Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), autoincrement=True, nullable=False),
    sa.Column('service_account_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('billing_period_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('period_start', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('period_end', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('metric', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('included_quantity', sa.NUMERIC(precision=12, scale=3), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('used_quantity', sa.NUMERIC(precision=12, scale=3), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('remaining_quantity', sa.NUMERIC(precision=12, scale=3), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('overage_quantity', sa.NUMERIC(precision=12, scale=3), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('charge', sa.NUMERIC(precision=12, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['billing_period_id'], ['billing_periods.id'], name=op.f('usage_summaries_billing_period_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['service_account_id'], ['service_accounts.id'], name=op.f('usage_summaries_service_account_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('usage_summaries_pkey')),
    sa.UniqueConstraint('service_account_id', 'billing_period_id', 'metric', name=op.f('uq_usage_summary_service_period_metric'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('idx_usage_summaries_service'), 'usage_summaries', ['service_account_id'], unique=False)
    op.create_index(op.f('idx_usage_summaries_period'), 'usage_summaries', ['billing_period_id'], unique=False)
    op.create_table('customer_addresses',
    sa.Column('id', sa.BIGINT(), sa.Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), autoincrement=True, nullable=False),
    sa.Column('customer_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('address_type', postgresql.ENUM('BILLING', 'SERVICE', 'POSTAL', name='address_type'), autoincrement=False, nullable=False),
    sa.Column('line1', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('line2', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('city', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('district', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('province', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('postal_code', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('country', sa.TEXT(), server_default=sa.text("'Sri Lanka'::text"), autoincrement=False, nullable=False),
    sa.Column('is_primary', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], name=op.f('customer_addresses_customer_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('customer_addresses_pkey'))
    )
    op.create_index(op.f('idx_customer_addresses_customer'), 'customer_addresses', ['customer_id'], unique=False)
    op.create_table('customers',
    sa.Column('id', sa.BIGINT(), sa.Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('full_name', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('address_line1', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('address_line2', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('city', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('postal_code', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('status', postgresql.ENUM('ACTIVE', 'SUSPENDED', 'CLOSED', name='account_status'), server_default=sa.text("'ACTIVE'::account_status"), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('nic', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('title', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('first_name', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('last_name', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('email', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('mobile_number', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('alternate_phone', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('preferred_language', sa.TEXT(), server_default=sa.text("'en'::text"), autoincrement=False, nullable=False),
    sa.Column('date_of_birth', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('customer_type', postgresql.ENUM('RESIDENTIAL', 'BUSINESS', name='customer_type'), server_default=sa.text("'RESIDENTIAL'::customer_type"), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('customers_user_id_fkey'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('customers_pkey')),
    sa.UniqueConstraint('nic', name=op.f('uq_customers_nic'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_table('packages',
    sa.Column('id', sa.BIGINT(), sa.Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), autoincrement=True, nullable=False),
    sa.Column('name', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('service_type', postgresql.ENUM('VOICE', 'BROADBAND', 'PEOTV', 'BUNDLE', 'OTHER', name='service_type'), autoincrement=False, nullable=False),
    sa.Column('monthly_fee', sa.NUMERIC(precision=12, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('data_limit_gb', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=True),
    sa.Column('extra_charge_per_gb', sa.NUMERIC(precision=12, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False),
    sa.Column('package_code', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('speed_tier', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('anytime_gb', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=True),
    sa.Column('peak_gb', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=True),
    sa.Column('offpeak_gb', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=True),
    sa.Column('included_voice_minutes', sa.NUMERIC(precision=12, scale=3), autoincrement=False, nullable=True),
    sa.Column('active_from', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('active_to', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('tax_applicable', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('packages_pkey')),
    sa.UniqueConstraint('package_code', name=op.f('uq_packages_package_code'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_table('usage_records',
    sa.Column('id', sa.BIGINT(), sa.Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), autoincrement=True, nullable=False),
    sa.Column('service_account_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('period_start', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('period_end', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('metric', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('quantity', sa.NUMERIC(precision=12, scale=3), autoincrement=False, nullable=True),
    sa.Column('charge', sa.NUMERIC(precision=12, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=True),
    sa.Column('event_time', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['service_account_id'], ['service_accounts.id'], name=op.f('usage_records_service_account_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('usage_records_pkey'))
    )
    op.create_index(op.f('idx_usage_service'), 'usage_records', ['service_account_id'], unique=False)
    op.create_table('accounts',
    sa.Column('id', sa.BIGINT(), sa.Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), autoincrement=True, nullable=False),
    sa.Column('customer_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('account_number', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('telephone_number', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('service_label', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('status', postgresql.ENUM('ACTIVE', 'SUSPENDED', 'CLOSED', name='account_status'), server_default=sa.text("'ACTIVE'::account_status"), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('billing_cycle', sa.TEXT(), server_default=sa.text("'MONTHLY_25'::text"), autoincrement=False, nullable=False),
    sa.Column('bill_delivery_method', postgresql.ENUM('EMAIL', 'SMS', 'POSTAL', 'PORTAL', name='bill_delivery_method'), server_default=sa.text("'PORTAL'::bill_delivery_method"), autoincrement=False, nullable=False),
    sa.Column('credit_limit', sa.NUMERIC(precision=12, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('deposit_amount', sa.NUMERIC(precision=12, scale=2), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('opened_on', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('closed_on', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('last_billed_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('notify_email', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False),
    sa.Column('notify_sms', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], name=op.f('accounts_customer_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('accounts_pkey')),
    sa.UniqueConstraint('account_number', name=op.f('accounts_account_number_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('idx_accounts_customer'), 'accounts', ['customer_id'], unique=False)
    op.create_table('payments',
    sa.Column('id', sa.BIGINT(), sa.Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), autoincrement=True, nullable=False),
    sa.Column('account_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('payment_date', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('method', postgresql.ENUM('PHYSICAL', 'ONLINE', 'CARD', 'CHEQUE', 'BANK_TRANSFER', name='payment_method'), server_default=sa.text("'PHYSICAL'::payment_method"), autoincrement=False, nullable=False),
    sa.Column('amount', sa.NUMERIC(precision=12, scale=2), autoincrement=False, nullable=False),
    sa.Column('reference', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('invoice_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('status', postgresql.ENUM('PENDING', 'POSTED', 'FAILED', 'REVERSED', name='payment_status'), server_default=sa.text("'POSTED'::payment_status"), autoincrement=False, nullable=False),
    sa.Column('receipt_number', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('provider', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('provider_reference', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('posted_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('payments_account_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], name=op.f('fk_payments_invoice_id'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('payments_pkey'))
    )
    op.create_index(op.f('idx_payments_account'), 'payments', ['account_id'], unique=False)
    op.create_table('service_requests',
    sa.Column('id', sa.BIGINT(), sa.Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), autoincrement=True, nullable=False),
    sa.Column('customer_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('account_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('service_account_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('request_type', postgresql.ENUM('NEW_SERVICE', 'PACKAGE_UPGRADE', 'PACKAGE_DOWNGRADE', 'RELOCATION', 'DISCONNECTION', name='request_type'), autoincrement=False, nullable=False),
    sa.Column('status', postgresql.ENUM('OPEN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='request_status'), server_default=sa.text("'OPEN'::request_status"), autoincrement=False, nullable=False),
    sa.Column('requested_package_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('notes', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('resolved_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('service_requests_account_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], name=op.f('service_requests_customer_id_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['requested_package_id'], ['packages.id'], name=op.f('service_requests_requested_package_id_fkey'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['service_account_id'], ['service_accounts.id'], name=op.f('service_requests_service_account_id_fkey'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('service_requests_pkey'))
    )
    op.create_index(op.f('idx_service_requests_customer'), 'service_requests', ['customer_id'], unique=False)
    op.create_index(op.f('idx_service_requests_account'), 'service_requests', ['account_id'], unique=False)
    # ### end Alembic commands ###
