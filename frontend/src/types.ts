export interface Customer {
  id: number
  name: string
  nic: string | null
  email: string | null
  phone: string | null
  address: string | null
}

export type AccountStatus = 'ACTIVE' | 'SUSPENDED' | 'CLOSED'

export interface Account {
  id: number
  customer_id: number
  account_no: string
  status: AccountStatus
  billing_cycle: string | null
}

export type ServiceType = 'VOICE' | 'BROADBAND' | 'PEOTV' | 'BUNDLE' | 'OTHER'

export interface ServiceAccount {
  id: number
  account_id: number
  service_type: ServiceType
  identifier: string
  package_id: number | null
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

export interface Paginated<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}
