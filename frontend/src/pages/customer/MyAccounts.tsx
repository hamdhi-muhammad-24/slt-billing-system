import { Link, useNavigate } from 'react-router-dom'
import { useMutation, useQueries } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  ArrowRight,
  Building2,
  CalendarDays,
  CreditCard,
  Download,
  FileText,
  Inbox,
  ReceiptText,
  ShieldCheck,
  Wifi,
} from 'lucide-react'
import type { Account, Invoice, Payment } from '../../types'
import { useAuth } from '../../auth/AuthProvider'
import { useCustomer } from '../../hooks/useCustomer'
import { useCustomerAccounts } from '../../hooks/useCustomerAccounts'
import { ErrorState } from '../../components/states'
import { CardSkeleton } from '../../components/ui-kit/Skeletons'
import { EmptyState } from '../../components/ui-kit/EmptyState'
import { StatusBadge } from '../../components/ui-kit/StatusBadge'
import { ApiError, downloadInvoicePdf, listInvoices, listPayments } from '../../lib/api'
import { formatDate } from '../../lib/format'
import { formatLKR } from '../../lib/money'
import { Button } from '@/components/ui/button'

function sortInvoices(invoices: Invoice[]): Invoice[] {
  return [...invoices].sort((a, b) => {
    const issueDate = b.issue_date.localeCompare(a.issue_date)
    return issueDate !== 0 ? issueDate : b.period.localeCompare(a.period)
  })
}

function sortPayments(payments: Payment[]): Payment[] {
  return [...payments].sort((a, b) => b.paid_at.localeCompare(a.paid_at))
}

function daysUntil(dueDate: string): number {
  const now = new Date()
  now.setHours(0, 0, 0, 0)
  const due = new Date(dueDate)
  due.setHours(0, 0, 0, 0)
  return Math.ceil((due.getTime() - now.getTime()) / 86_400_000)
}

function formatLkrNumber(value: number): string {
  return formatLKR(value.toFixed(2))
}

function MetricTile({
  icon: Icon,
  label,
  value,
  tone = 'primary',
}: {
  icon: typeof FileText
  label: string
  value: string
  tone?: 'primary' | 'success' | 'warning'
}) {
  const toneClass =
    tone === 'success'
      ? 'bg-success/10 text-success'
      : tone === 'warning'
        ? 'bg-warning/10 text-warning-foreground'
        : 'bg-primary/10 text-primary'

  return (
    <div className="surface-card flex items-center gap-3 p-4">
      <div className={`flex size-10 shrink-0 items-center justify-center rounded-md ${toneClass}`}>
        <Icon size={18} />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        <p className="mt-0.5 truncate text-lg font-semibold tabular-nums">{value}</p>
      </div>
    </div>
  )
}

function AccountCard({
  account,
  latestInvoice,
}: {
  account: Account
  latestInvoice?: Invoice
}) {
  return (
    <article className="surface-card overflow-hidden">
      <div className="flex items-start justify-between gap-3 border-b border-border bg-muted/35 px-4 py-3">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
            <Wifi size={16} />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold">{account.account_no}</p>
            <p className="text-xs text-muted-foreground">{account.billing_cycle ?? 'Monthly billing'}</p>
          </div>
        </div>
        <StatusBadge status={account.status} />
      </div>

      <div className="grid gap-4 p-4">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-xs text-muted-foreground">Latest bill</p>
            <p className="mt-1 font-semibold tabular-nums">
              {latestInvoice ? formatLKR(latestInvoice.total_payable) : 'No bill'}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Due date</p>
            <p className="mt-1 font-semibold">
              {latestInvoice ? formatDate(latestInvoice.due_date) : 'Pending'}
            </p>
          </div>
        </div>

        <Button
          asChild
          variant="outline"
          size="sm"
          className="w-full justify-between hover:border-primary/40 hover:text-primary"
        >
          <Link to={`/app/accounts/${account.id}`}>
            View account
            <ArrowRight size={14} />
          </Link>
        </Button>
      </div>
    </article>
  )
}

export default function MyAccounts() {
  const navigate = useNavigate()
  const { session } = useAuth()
  const customerId = session?.customerId ?? 0

  const customer = useCustomer(customerId)
  const accounts = useCustomerAccounts(customerId)
  const accountList = accounts.data ?? []

  const invoiceQueries = useQueries({
    queries: accountList.map((account) => ({
      queryKey: ['invoices', account.id, 'customer-dashboard'],
      queryFn: () => listInvoices(account.id, { limit: 6 }),
    })),
  })

  const paymentQueries = useQueries({
    queries: accountList.map((account) => ({
      queryKey: ['payments', account.id, 'customer-dashboard'],
      queryFn: () => listPayments(account.id),
    })),
  })

  const downloadLatest = useMutation({
    mutationFn: (invoiceId: number) => downloadInvoicePdf(invoiceId),
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.detail : 'PDF download failed.')
    },
  })

  if (customer.isPending || accounts.isPending) {
    return (
      <div className="flex flex-col gap-6">
        <div className="h-28 rounded-lg bg-muted animate-pulse" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    )
  }

  if (customer.error) {
    return <ErrorState detail={customer.error instanceof ApiError ? customer.error.detail : customer.error.message} />
  }
  if (accounts.error) {
    return <ErrorState detail={accounts.error instanceof ApiError ? accounts.error.detail : accounts.error.message} />
  }

  const invoiceError = invoiceQueries.find((query) => query.error)?.error
  const paymentError = paymentQueries.find((query) => query.error)?.error
  if (invoiceError) {
    return <ErrorState detail={invoiceError instanceof ApiError ? invoiceError.detail : invoiceError.message} />
  }
  if (paymentError) {
    return <ErrorState detail={paymentError instanceof ApiError ? paymentError.detail : paymentError.message} />
  }

  const invoices = invoiceQueries.flatMap((query) => query.data?.items ?? [])
  const payments = paymentQueries.flatMap((query) => query.data ?? [])
  const sortedInvoices = sortInvoices(invoices)
  const latestInvoice = sortedInvoices[0] ?? null
  const latestAccount = latestInvoice
    ? accountList.find((account) => account.id === latestInvoice.account_id)
    : null
  const latestPayment = sortPayments(payments)[0] ?? null
  const invoiceLoading = accountList.length > 0 && invoiceQueries.some((query) => query.isPending)
  const paymentLoading = accountList.length > 0 && paymentQueries.some((query) => query.isPending)

  const latestByAccount = new Map<number, Invoice>()
  for (const invoice of sortedInvoices) {
    if (!latestByAccount.has(invoice.account_id)) latestByAccount.set(invoice.account_id, invoice)
  }

  const totalPayable = [...latestByAccount.values()].reduce(
    (sum, invoice) => sum + Number(invoice.total_payable),
    0,
  )
  const activeAccounts = accountList.filter((account) => account.status === 'ACTIVE').length
  const dueIn = latestInvoice ? daysUntil(latestInvoice.due_date) : null
  const dueLabel = dueIn == null
    ? 'No bill yet'
    : dueIn < 0
      ? `${Math.abs(dueIn)} days overdue`
      : dueIn === 0
        ? 'Due today'
        : `${dueIn} days left`

  return (
    <div className="flex flex-col gap-8">
      <section className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
        <div className="gradient-primary relative p-5 text-white sm:p-6">
          <div className="network-grid absolute inset-0 opacity-35" />
          <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl">
              <p className="text-sm font-medium text-white/72">Customer self-care dashboard</p>
              <h1 className="mt-2 text-3xl font-semibold sm:text-4xl">
                Hello, {customer.data.name}
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-white/75">
                Review linked SLT-MOBITEL accounts, check your latest bill, and download statements
                from a single secure workspace.
              </p>
            </div>
            <div className="grid min-w-[260px] gap-2 rounded-lg border border-white/20 bg-white/10 p-4 backdrop-blur">
              <p className="text-xs font-medium text-white/70">Total payable across latest bills</p>
              <p className="text-3xl font-semibold tabular-nums">
                {invoiceLoading ? 'Checking...' : formatLkrNumber(totalPayable)}
              </p>
              <p className="text-xs text-white/60">
                {accountList.length} account{accountList.length === 1 ? '' : 's'} linked to this login
              </p>
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricTile icon={Building2} label="Linked accounts" value={String(accountList.length)} />
        <MetricTile icon={ShieldCheck} label="Active services" value={String(activeAccounts)} tone="success" />
        <MetricTile
          icon={CalendarDays}
          label="Next due status"
          value={invoiceLoading ? 'Checking...' : dueLabel}
          tone={dueIn != null && dueIn <= 3 ? 'warning' : 'primary'}
        />
        <MetricTile
          icon={CreditCard}
          label="Last payment"
          value={paymentLoading ? 'Checking...' : latestPayment ? formatLKR(latestPayment.amount) : 'No payment'}
          tone="success"
        />
      </div>

      <section className="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
        <article className="surface-section p-5">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Latest bill</p>
              <h2 className="mt-1 text-3xl font-semibold tabular-nums">
                {invoiceLoading ? 'Checking...' : latestInvoice ? formatLKR(latestInvoice.total_payable) : 'No bill available'}
              </h2>
              <p className="mt-2 text-sm text-muted-foreground">
                {latestInvoice && latestAccount
                  ? `${latestAccount.account_no} for ${latestInvoice.period}, due ${formatDate(latestInvoice.due_date)}`
                  : 'Bills generated by SLT-MOBITEL will appear here.'}
              </p>
            </div>
            {latestInvoice && (
              <div className="rounded-md border border-border bg-muted/40 px-3 py-2 text-sm">
                <p className="text-xs text-muted-foreground">Due status</p>
                <p className="font-semibold">{dueLabel}</p>
              </div>
            )}
          </div>

          <div className="mt-6 flex flex-col gap-2 sm:flex-row">
            <Button
              disabled={!latestInvoice}
              onClick={() => latestInvoice && navigate(`/app/invoices/${latestInvoice.id}`)}
            >
              <FileText size={15} />
              View latest bill
            </Button>
            <Button
              variant="outline"
              disabled={!latestInvoice || downloadLatest.isPending}
              onClick={() => latestInvoice && downloadLatest.mutate(latestInvoice.id)}
            >
              <Download size={15} />
              {downloadLatest.isPending ? 'Downloading...' : 'Download PDF'}
            </Button>
          </div>
        </article>

        <article className="surface-section p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Quick actions</p>
              <h2 className="mt-1 text-xl font-semibold">Billing shortcuts</h2>
            </div>
            <div className="flex size-11 items-center justify-center rounded-md bg-primary/10 text-primary">
              <ReceiptText size={20} />
            </div>
          </div>

          <div className="mt-5 grid gap-2">
            <Button
              variant="outline"
              className="justify-between"
              disabled={!latestAccount}
              onClick={() => latestAccount && navigate(`/app/accounts/${latestAccount.id}`)}
            >
              Open account history
              <ArrowRight size={14} />
            </Button>
            <Button
              variant="outline"
              className="justify-between"
              disabled={!latestInvoice}
              onClick={() => latestInvoice && navigate(`/app/invoices/${latestInvoice.id}`)}
            >
              Review bill breakdown
              <ArrowRight size={14} />
            </Button>
            <Button
              variant="outline"
              className="justify-between"
              disabled={!latestInvoice || downloadLatest.isPending}
              onClick={() => latestInvoice && downloadLatest.mutate(latestInvoice.id)}
            >
              Download statement
              <ArrowRight size={14} />
            </Button>
          </div>
        </article>
      </section>

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Your accounts</p>
            <h2 className="text-xl font-semibold">{accountList.length} linked account{accountList.length === 1 ? '' : 's'}</h2>
          </div>
          <p className="text-sm text-muted-foreground">Broadband, voice, PeoTV, and bundled service accounts</p>
        </div>

        {accountList.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title="No accounts linked to your login yet"
            hint="Contact SLT support if you believe this is an error."
          />
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {accountList.map((account) => (
              <AccountCard
                key={account.id}
                account={account}
                latestInvoice={latestByAccount.get(account.id)}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
