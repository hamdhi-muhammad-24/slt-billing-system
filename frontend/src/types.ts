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
export type BillingScheduleMode = 'AUTOMATIC' | 'APPROVAL_REQUIRED'
export type BillingApprovalStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED'

export type PdfStatus = 'PENDING' | 'SUCCESS' | 'FAILED'
export type DeliveryStatus = 'NOT_ENABLED' | 'PENDING' | 'SUCCESS' | 'FAILED'
export type BillingRunItemOverallStatus = 'PENDING' | 'GENERATED' | 'FAILED' | 'READY_TO_SEND' | 'COMPLETED'

export interface BillingRunItem {
  id: number
  billing_run_id: number
  account_id: number | null
  customer_id: number | null
  invoice_id: number | null
  template_id: number | null
  account_number: string | null
  customer_name: string | null
  phone: string | null
  email: string | null
  pdf_status: PdfStatus
  email_status: DeliveryStatus
  sms_status: DeliveryStatus
  overall_status: BillingRunItemOverallStatus
  failure_reason: string | null
  email_failure_reason: string | null
  sms_failure_reason: string | null
  email_provider_ref: string | null
  sms_provider_ref: string | null
  retry_count: number
  pdf_path: string | null
  created_at: string
  updated_at: string
}

export interface BillingRun {
  id: number
  period: string
  status: BillingRunStatus
  template_id: number | null
  template_name: string | null
  total: number
  succeeded: number
  failed: number
  pdf_success_count: number
  pdf_failed_count: number
  email_status_summary: Record<string, number>
  sms_status_summary: Record<string, number>
  started_at: string | null
  finished_at: string | null
  failures?: BillingRunFailure[]
  items?: BillingRunItem[]
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

export type TemplateCategory = 'CLASSIC' | 'MODERN' | 'ENTERPRISE' | 'MINIMAL' | 'CUSTOM'

export interface InvoiceTemplate {
  id: number
  name: string
  description: string | null
  template_code: string
  is_active: boolean
  is_system_template: boolean
  base_template_id: number | null
  category: TemplateCategory
  layout_type: string
  cover_image_url: string | null
  template_layout: string | null
  header_message: string | null
  footer_message: string | null
  promotion_message: string | null
  theme_name: string | null
  theme_color: string | null
  created_at: string
  updated_at: string
}

export interface BillingSchedule {
  id: number
  name: string
  day_of_month: number
  run_time: string
  timezone: string
  schedule_mode: BillingScheduleMode
  is_active: boolean
  send_email: boolean
  send_sms: boolean
  approval_lead_days: number
  approval_email: string | null
  last_triggered_period: string | null
  created_at: string
  updated_at: string
}

export interface BillingRunApproval {
  id: number
  billing_schedule_id: number
  billing_run_id: number | null
  period: string
  status: BillingApprovalStatus
  requested_to: string | null
  requested_at: string
  expires_at: string | null
  approved_at: string | null
  rejected_at: string | null
  decided_by_user_id: number | null
  notes: string | null
}

export interface Paginated<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}
