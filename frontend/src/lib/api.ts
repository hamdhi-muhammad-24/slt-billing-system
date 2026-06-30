import type {
  Account,
  AdminDashboardSummary,
  BillingRun,
  BillingRunFailure,
  Customer,
  DailyUsageRecord,
  Invoice,
  Paginated,
  Payment,
  ServiceAccount,
  UsageSummary,
} from '../types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL

const TOKEN_KEY = 'slt-token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

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
  const token = getToken()
  const authHeader: Record<string, string> = token
    ? { Authorization: `Bearer ${token}` }
    : {}

  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...authHeader,
      ...(init?.headers ?? {}),
    },
  })

  if (res.status === 401) {
    clearToken()
    localStorage.removeItem('slt-auth')
    window.location.href = '/login'
    throw new ApiError(401, 'Session expired - please log in again.')
  }

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

// --- Auth endpoints ---

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface MeResponse {
  id: number
  email: string
  role: 'ADMIN' | 'CUSTOMER'
  customer_id: number | null
}

export async function authLogin(email: string, password: string): Promise<LoginResponse> {
  const body = new URLSearchParams({ username: email, password })
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: body.toString(),
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const json = (await res.json()) as { detail: string }
      if (json.detail) detail = json.detail
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<LoginResponse>
}

export function authMe(): Promise<MeResponse> {
  return request('/auth/me')
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

export function getAdminDashboardSummary(): Promise<AdminDashboardSummary> {
  return request('/billing/admin-summary')
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

export function listUsage(accountId: number, period?: string): Promise<UsageSummary[]> {
  const q = period ? `?period=${encodeURIComponent(period)}` : ''
  return request(`/accounts/${accountId}/usage${q}`)
}

export function listUsageHistory(accountId: number, months = 6): Promise<UsageSummary[]> {
  return request(`/accounts/${accountId}/usage/history?months=${months}`)
}

export function listDailyUsage(serviceAccountId: number, period: string): Promise<DailyUsageRecord[]> {
  return request(`/service-accounts/${serviceAccountId}/daily-usage?period=${encodeURIComponent(period)}`)
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

interface PdfTokenResponse {
  token: string
  expires_in: number
}

export async function downloadInvoicePdf(invoiceId: number): Promise<void> {
  const { token } = await request<PdfTokenResponse>(`/invoices/${invoiceId}/pdf-token`)
  const url = `${BASE_URL}/invoices/${invoiceId}/pdf?token=${encodeURIComponent(token)}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error('PDF download failed')
  }

  const blob = await response.blob()
  const objectUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = objectUrl
  a.download = `invoice-${invoiceId}.pdf`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(objectUrl)
}
