import type {
  Account,
  BillingRun,
  BillingRunFailure,
  Customer,
  Invoice,
  Paginated,
  Payment,
  ServiceAccount,
} from '../types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL

export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = (await res.json()) as { detail: string }
      if (body.detail) detail = body.detail
    } catch {
      // ignore JSON parse failure; use statusText
    }
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<T>
}

function paginationQuery(params?: { limit?: number; offset?: number }): string {
  const q = new URLSearchParams()
  if (params?.limit !== undefined) q.set('limit', String(params.limit))
  if (params?.offset !== undefined) q.set('offset', String(params.offset))
  const s = q.toString()
  return s ? `?${s}` : ''
}

export interface HealthResponse {
  status: string
  db: string
}

export function getHealth(): Promise<HealthResponse> {
  return request('/health')
}

export function listCustomers(
  params?: { limit?: number; offset?: number },
): Promise<Paginated<Customer>> {
  return request(`/customers${paginationQuery(params)}`)
}

export function getCustomer(customerId: number): Promise<Customer> {
  return request(`/customers/${customerId}`)
}

export function listCustomerAccounts(customerId: number): Promise<Account[]> {
  return request(`/customers/${customerId}/accounts`)
}

export function getAccount(accountId: number): Promise<Account> {
  return request(`/accounts/${accountId}`)
}

export function listServiceAccounts(accountId: number): Promise<ServiceAccount[]> {
  return request(`/accounts/${accountId}/service-accounts`)
}

export function listInvoices(
  accountId: number,
  params?: { limit?: number; offset?: number },
): Promise<Paginated<Invoice>> {
  return request(`/accounts/${accountId}/invoices${paginationQuery(params)}`)
}

export function listPayments(accountId: number): Promise<Payment[]> {
  return request(`/accounts/${accountId}/payments`)
}

export function getInvoice(invoiceId: number): Promise<Invoice> {
  return request(`/invoices/${invoiceId}`)
}

export interface GenerateOneRequest {
  account_id: number
  period: string
}

export function generateOne(body: GenerateOneRequest): Promise<Invoice> {
  return request('/billing/generate-one', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export interface GenerateBatchRequest {
  period: string
  account_ids?: number[]
}

export function generateBatch(body: GenerateBatchRequest): Promise<BillingRun> {
  return request('/billing/generate-batch', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export interface BillingRunWithFailures extends BillingRun {
  failures: BillingRunFailure[]
}

export function getBillingRun(runId: number): Promise<BillingRunWithFailures> {
  return request(`/billing/runs/${runId}`)
}

export async function downloadInvoicePdf(invoiceId: number): Promise<void> {
  const res = await fetch(`${BASE_URL}/invoices/${invoiceId}/pdf`)
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = (await res.json()) as { detail: string }
      if (body.detail) detail = body.detail
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail)
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `invoice-${invoiceId}.pdf`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
