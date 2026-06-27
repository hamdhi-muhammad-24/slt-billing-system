import { Link, useNavigate } from 'react-router-dom'
import { useMutation, useQueries } from '@tanstack/react-query'
import { toast } from 'sonner'
import type { LucideIcon } from 'lucide-react'
import {
  AlertCircle,
  ArrowRight,
  CalendarDays,
  CreditCard,
  Download,
  FileText,
  Inbox,
  Mail,
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

function AccountCard({ account }: { account: Account }) {
  return (
    <div className="flex flex-col gap-0 overflow-hidden rounded-lg border border-border bg-card shadow-sm transition-shadow hover:shadow-md">
      <div className="gradient-primary px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-white/20">
            <Wifi size={13} className="text-white" />
          </div>
          <span className="text-white font-semibold text-sm">{account.account_no}</span>
        </div>
        <StatusBadge status={account.status} />
      </div>

      <div className="px-4 py-3 flex flex-col gap-3">
        <p className="text-sm text-muted-foreground capitalize">
          {account.billing_cycle ?? 'Standard monthly'} billing
        </p>
        <Link to={`/app/accounts/${account.id}`} className="block">
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-between group hover:border-primary/40 hover:text-primary transition-colors"
          >
            View invoices
            <ArrowRight size={13} className="transition-transform group-hover:translate-x-0.5" />
          </Button>
        </Link>
      </div>
    </div>
  )
}

function BillingCard({
  icon: Icon,
  label,
  value,
  helper,
  tone = 'primary',
}: {
  icon: LucideIcon
  label: string
  value: string
  helper?: string
  tone?: 'primary' | 'success' | 'warning'
}) {
  const iconClass =
    tone === 'success'
      ? 'bg-success/10 text-success'
      : tone === 'warning'
        ? 'bg-warning/15 text-warning-foreground'
        : 'bg-primary/10 text-primary'

  return (
    <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</p>
          <p className="mt-2 text-xl font-bold tracking-tight tabular-nums">{value}</p>
          {helper && <p className="mt-1 text-xs text-muted-foreground">{helper}</p>}
        </div>
        <div className={`flex size-9 shrink-0 items-center justify-center rounded-md ${iconClass}`}>
          <Icon size={16} />
        </div>
      </div>
    </div>
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

  if (customer.isPending || accounts.isPending) return (
    <div className="flex flex-col gap-6">
      <div className="h-8 w-56 bg-muted animate-pulse rounded-md" />
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    </div>
  )

  if (customer.error) return <ErrorState detail={customer.error instanceof ApiError ? customer.error.detail : customer.error.message} />
  if (accounts.error) return <ErrorState detail={accounts.error instanceof ApiError ? accounts.error.detail : accounts.error.message} />

  const invoiceError = invoiceQueries.find((query) => query.error)?.error
  const paymentError = paymentQueries.find((query) => query.error)?.error
  if (invoiceError) return <ErrorState detail={invoiceError instanceof ApiError ? invoiceError.detail : invoiceError.message} />
  if (paymentError) return <ErrorState detail={paymentError instanceof ApiError ? paymentError.detail : paymentError.message} />

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
  const dueStatus = dueIn == null
    ? 'No bill yet'
    : dueIn < 0
      ? `${Math.abs(dueIn)} days overdue`
      : dueIn === 0
        ? 'Due today'
        : `${dueIn} days left`

  return (
    <div className="flex flex-col gap-8 pb-16 md:pb-0">
      <div>
        <p className="text-sm text-muted-foreground">Welcome back</p>
        <h1 className="text-2xl font-bold tracking-tight">Hello, {customer.data.name}</h1>
      </div>

      <section className="flex flex-col gap-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Billing Summary
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          <BillingCard
            icon={CreditCard}
            label="Current amount due"
            value={invoiceLoading ? 'Checking...' : formatLkrNumber(totalPayable)}
            helper="Across latest bills"
          />
          <BillingCard
            icon={CalendarDays}
            label="Due date"
            value={invoiceLoading ? 'Checking...' : latestInvoice ? formatDate(latestInvoice.due_date) : 'No bill'}
            helper={invoiceLoading ? undefined : dueStatus}
            tone={dueIn != null && dueIn <= 3 ? 'warning' : 'primary'}
          />
          <BillingCard
            icon={CreditCard}
            label="Last payment"
            value={paymentLoading ? 'Checking...' : latestPayment ? formatLKR(latestPayment.amount) : 'No payment'}
            helper={latestPayment ? formatDate(latestPayment.paid_at) : 'Payment history'}
            tone="success"
          />
          <BillingCard
            icon={ShieldCheck}
            label="Active connections"
            value={String(activeAccounts)}
            helper={`${accountList.length} linked account${accountList.length === 1 ? '' : 's'}`}
            tone="success"
          />
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-[1.15fr_0.85fr] gap-4">
        <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
          <div className="gradient-primary px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-white/20">
                <FileText size={13} className="text-white" />
              </div>
              <span className="text-white font-semibold text-sm">Latest bill preview</span>
            </div>
            {latestInvoice && <span className="text-xs font-medium text-white/80">{latestInvoice.period}</span>}
          </div>

          <div className="px-4 py-4">
            <p className="text-3xl font-bold tracking-tight text-primary tabular-nums">
              {invoiceLoading ? 'Checking...' : latestInvoice ? formatLKR(latestInvoice.total_payable) : 'No bill available'}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              {latestInvoice && latestAccount
                ? `${latestAccount.account_no} bill due ${formatDate(latestInvoice.due_date)}`
                : 'Your latest generated bill will appear here.'}
            </p>
            <div className="mt-4 flex flex-col gap-2 sm:flex-row">
              <Button
                size="sm"
                disabled={!latestInvoice}
                onClick={() => latestInvoice && navigate(`/app/invoices/${latestInvoice.id}`)}
              >
                <FileText size={13} />
                View Bill
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={!latestInvoice || downloadLatest.isPending}
                onClick={() => latestInvoice && downloadLatest.mutate(latestInvoice.id)}
              >
                <Download size={13} />
                {downloadLatest.isPending ? 'Downloading...' : 'Download PDF'}
              </Button>
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
          <div className="gradient-primary px-4 py-3 flex items-center gap-2">
            <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-white/20">
              <ReceiptText size={13} className="text-white" />
            </div>
            <span className="text-white font-semibold text-sm">Quick actions</span>
          </div>

          <div className="grid gap-2 px-4 py-3 sm:grid-cols-2 lg:grid-cols-1">
            <Button
              variant="outline"
              size="sm"
              className="justify-between"
              disabled={!latestInvoice || downloadLatest.isPending}
              onClick={() => latestInvoice && downloadLatest.mutate(latestInvoice.id)}
            >
              <span className="inline-flex items-center gap-2">
                <Download size={13} />
                Download bill
              </span>
              <ArrowRight size={13} />
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="justify-between"
              disabled={!latestAccount}
              onClick={() => latestAccount && navigate(`/app/accounts/${latestAccount.id}`)}
            >
              <span className="inline-flex items-center gap-2">
                <ReceiptText size={13} />
                View bill history
              </span>
              <ArrowRight size={13} />
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="justify-between"
              disabled={!latestInvoice}
              onClick={() => toast.info('Online bill payment will be connected in the payment phase.')}
            >
              <span className="inline-flex items-center gap-2">
                <CreditCard size={13} />
                Pay bill
              </span>
              <ArrowRight size={13} />
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="justify-between"
              onClick={() => toast.info('eBill request workflow will be added in a later phase.')}
            >
              <span className="inline-flex items-center gap-2">
                <Mail size={13} />
                Request eBill
              </span>
              <ArrowRight size={13} />
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="justify-between"
              onClick={() => toast.info('Billing issue reporting will be added in a support workflow phase.')}
            >
              <span className="inline-flex items-center gap-2">
                <AlertCircle size={13} />
                Report billing issue
              </span>
              <ArrowRight size={13} />
            </Button>
          </div>
        </div>
      </section>

      <section className="flex flex-col gap-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Your Accounts ({accountList.length})
        </h2>
        {accountList.length === 0
          ? (
            <EmptyState
              icon={Inbox}
              title="No accounts linked to your login yet"
              hint="Contact SLT support if you believe this is an error."
            />
          )
          : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {accountList.map((a) => <AccountCard key={a.id} account={a} />)}
            </div>
          )}
      </section>

      {latestInvoice && (
        <div className="fixed inset-x-0 bottom-0 z-30 border-t border-border bg-white/95 p-3 shadow-lg backdrop-blur md:hidden">
          <div className="grid grid-cols-2 gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={downloadLatest.isPending}
              onClick={() => downloadLatest.mutate(latestInvoice.id)}
            >
              <Download size={13} />
              Download
            </Button>
            <Button
              size="sm"
              onClick={() => toast.info('Online bill payment will be connected in the payment phase.')}
            >
              <CreditCard size={13} />
              Pay Bill
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
