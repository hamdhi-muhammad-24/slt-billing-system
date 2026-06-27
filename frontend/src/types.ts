export interface Customer {
  id: number
  name: string
  nic: string | null
  email: string | null
  phone: string | null
  alternate_phone: string | null
  title: string | null
  first_name: string | null
  last_name: string | null
  preferred_language: string | null
  customer_type: string | null
  address: string | null
}

export type AccountStatus = 'ACTIVE' | 'SUSPENDED' | 'CLOSED'

export interface Account {
  id: number
  customer_id: number
  account_no: string
  status: AccountStatus
  billing_cycle: string | null
  service_label: string | null
  telephone_number: string | null
  bill_delivery_method: string | null
  credit_limit: string | null
  deposit_amount: string | null
  notify_email: boolean
  notify_sms: boolean
}

export type ServiceType = 'VOICE' | 'BROADBAND' | 'PEOTV' | 'BUNDLE' | 'OTHER'

export interface ServiceAccount {
  id: number
  account_id: number
  service_type: ServiceType
  identifier: string
  package_id: number | null
  package_name: string | null
  connection_type: string | null
  label: string | null
  status: AccountStatus | null
}

export interface Package {
  id: number
  name: string
  service_type: ServiceType
  monthly_rental: string
}

export interface InvoiceLineItem {
  id: number
  service_account_id: number | null
  description: string
  amount: string
  is_tax: boolean
  sort_order: number
}

export interface ServiceAccountSummary {
  id: number
  service_type: ServiceType
  identifier: string
}

export interface Invoice {
  id: number
  account_id: number
  period: string
  issue_date: string
  due_date: string
  balance_bf: string
  payments_received: string
  arrears: string
  charges_for_period: string
  total_payable: string
  service_accounts: ServiceAccountSummary[]
  line_items: InvoiceLineItem[]
}

export interface Payment {
  id: number
  account_id: number
  amount: string
  paid_at: string
  method: string
  reference: string | null
  status: string | null
  receipt_number: string | null
  provider: string | null
}

export interface UsageSummary {
  id: number
  service_account_id: number
  period: string
  metric: string
  included_quantity: string
  used_quantity: string
  remaining_quantity: string
  overage_quantity: string
  charge: string
}

export interface DailyUsageRecord {
  id: number
  service_account_id: number
  usage_date: string
  bucket: string
  protocol: string | null
  app_category: string | null
  download_gb: string
  upload_gb: string
  total_gb: string
  charge: string
}

export type BillingRunStatus = 'pending' | 'running' | 'done' | 'partial' | 'failed'

export interface BillingRun {
  id: number
  period: string
  status: BillingRunStatus
  total: number
  succeeded: number
  failed: number
  started_at: string | null
  finished_at: string | null
}

export interface BillingRunFailure {
  id: number
  run_id: number
  account_id: number | null
  error: string
}

export interface DashboardRecentInvoice {
  id: number
  account_id: number
  account_no: string
  customer_name: string
  period: string
  issue_date: string
  total_payable: string
  status: string
}

export interface DashboardAlert {
  level: 'success' | 'warning' | 'critical'
  title: string
  detail: string
}

export interface AdminDashboardSummary {
  total_customers: number
  active_accounts: number
  generated_invoices: number
  failed_billing_runs: number
  notifications_sent: number
  notifications_failed: number
  recent_billing_runs: (BillingRun & { failures: BillingRunFailure[] })[]
  recent_invoices: DashboardRecentInvoice[]
  alerts: DashboardAlert[]
}

export interface Paginated<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}
