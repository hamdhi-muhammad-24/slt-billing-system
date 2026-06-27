import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  ArrowLeft,
  CalendarDays,
  CreditCard,
  Download,
  FileText,
  ReceiptText,
  WalletCards,
} from 'lucide-react'
import type { Invoice, Payment } from '../../types'
import { useInvoice } from '../../hooks/useInvoice'
import { ErrorState } from '../../components/states'
import { CardSkeleton } from '../../components/ui-kit/Skeletons'
import { StatusBadge } from '../../components/ui-kit/StatusBadge'
import { ApiError, downloadInvoicePdf, listInvoices, listPayments } from '../../lib/api'
import { formatDate } from '../../lib/format'
import { formatLKR } from '../../lib/money'
import Brand from '../../components/Brand'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'

type InvoiceStatus = 'Paid' | 'Due' | 'Overdue' | 'Generated'

function asNumber(value: string): number {
  const n = Number(value)
  return Number.isFinite(n) ? n : 0
}

function invoiceStatus(invoice: Invoice): InvoiceStatus {
  const total = asNumber(invoice.total_payable)
  if (total <= 0) return 'Paid'

  if (!invoice.due_date) return 'Generated'

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const due = new Date(invoice.due_date)
  due.setHours(0, 0, 0, 0)

  return due < today ? 'Overdue' : 'Due'
}

function sortInvoices(invoices: Invoice[]): Invoice[] {
  return [...invoices].sort((a, b) => {
    const issueDate = b.issue_date.localeCompare(a.issue_date)
    return issueDate !== 0 ? issueDate : b.period.localeCompare(a.period)
  })
}

function sortPayments(payments: Payment[]): Payment[] {
  return [...payments].sort((a, b) => b.paid_at.localeCompare(a.paid_at))
}

function DetailCard({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof FileText
  label: string
  value: string
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
      <div className="mb-3 flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
        <Icon size={16} />
      </div>
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-semibold tabular-nums">{value}</p>
    </div>
  )
}

export default function CustomerInvoiceDetail() {
  const { id } = useParams<{ id: string }>()
  const invoiceId = Number(id)
  const navigate = useNavigate()

  const { data: inv, isPending, error } = useInvoice(invoiceId)

  const invoiceHistory = useQuery({
    queryKey: ['invoices', inv?.account_id, 'period-selector'],
    queryFn: () => listInvoices(inv!.account_id, { limit: 24 }),
    enabled: Boolean(inv?.account_id),
  })

  const payments = useQuery({
    queryKey: ['payments', inv?.account_id, 'invoice-detail'],
    queryFn: () => listPayments(inv!.account_id),
    enabled: Boolean(inv?.account_id),
  })

  const download = useMutation({
    mutationFn: () => downloadInvoicePdf(invoiceId),
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.detail : 'PDF download failed.')
    },
  })

  if (isPending) return (
    <div className="flex flex-col gap-6 pb-16 md:pb-0">
      <CardSkeleton />
      <CardSkeleton />
    </div>
  )
  if (error) return <ErrorState detail={error instanceof ApiError ? error.detail : error.message} />

  const history = sortInvoices(invoiceHistory.data?.items ?? [inv])
  const recentPayments = sortPayments(payments.data ?? []).slice(0, 3)
  const status = invoiceStatus(inv)
  const charges = inv.line_items.filter((item) => !item.is_tax)
  const taxes = inv.line_items.filter((item) => item.is_tax)
  const paymentCount = payments.data?.length ?? 0

  return (
    <div className="flex flex-col gap-6">
      <Button
        variant="ghost"
        size="sm"
        className="w-fit gap-1.5 px-0 text-muted-foreground hover:bg-transparent hover:text-foreground"
        onClick={() => navigate(`/app/accounts/${inv.account_id}`)}
      >
        <ArrowLeft size={14} />
        Back to account
      </Button>

      <section className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
        <div className="gradient-primary px-5 py-5 text-white sm:px-6">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div className="flex flex-col gap-5">
              <Brand tone="dark" size="lg" />
              <div>
                <p className="text-sm font-medium text-white/75">SLT-MOBITEL eBill viewer</p>
                <h1 className="mt-2 text-2xl font-bold tracking-tight sm:text-3xl">
                  Invoice {inv.period}
                </h1>
                <p className="mt-2 text-sm text-white/72">Account #{inv.account_id}</p>
              </div>
            </div>

            <div className="flex flex-col gap-3 sm:min-w-[300px]">
              <div className="rounded-lg border border-white/20 bg-white/10 p-4 backdrop-blur">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-white/65">
                      Total payable
                    </p>
                    <p className="mt-2 text-4xl font-bold tracking-tight tabular-nums">
                      {formatLKR(inv.total_payable)}
                    </p>
                  </div>
                  <StatusBadge status={status} />
                </div>
                <div className="mt-4 flex items-center gap-2 text-sm text-white/78">
                  <CalendarDays size={15} />
                  Due {formatDate(inv.due_date)}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <Button
                  size="sm"
                  className="bg-white text-primary hover:bg-white/90"
                  disabled={download.isPending}
                  onClick={() => download.mutate()}
                >
                  <Download size={14} />
                  {download.isPending ? 'Downloading...' : 'Download PDF'}
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  className="border-white/20 bg-white/10 text-white hover:bg-white/15 hover:text-white"
                  onClick={() => toast.info('Online bill payment will be connected in the payment phase.')}
                >
                  <CreditCard size={14} />
                  Pay Now
                </Button>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-4">
          <DetailCard icon={FileText} label="Issued" value={formatDate(inv.issue_date)} />
          <DetailCard icon={CalendarDays} label="Due date" value={formatDate(inv.due_date)} />
          <DetailCard icon={ReceiptText} label="Billing period" value={inv.period} />
          <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
            <label htmlFor="billing-period" className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Select period
            </label>
            <select
              id="billing-period"
              value={String(inv.id)}
              className="mt-3 h-9 w-full rounded-md border border-input bg-background px-3 text-sm font-medium shadow-sm outline-none transition-colors focus:border-ring focus:ring-[3px] focus:ring-ring/20"
              onChange={(event) => navigate(`/app/invoices/${event.target.value}`)}
            >
              {history.map((invoice) => (
                <option key={invoice.id} value={invoice.id}>
                  {invoice.period}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-lg border border-border bg-card shadow-sm">
          <div className="flex items-center gap-3 border-b border-border bg-muted/35 px-4 py-3">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
              <WalletCards size={14} />
            </div>
            <div>
              <h2 className="text-sm font-semibold">Charges breakdown</h2>
              <p className="text-xs text-muted-foreground">Charges, payments, arrears, and taxes</p>
            </div>
          </div>

          <div className="p-4">
            <dl className="grid grid-cols-[auto_1fr] gap-x-8 gap-y-3 text-sm">
              <dt className="text-muted-foreground">Balance B/F</dt>
              <dd className="text-right tabular-nums">{formatLKR(inv.balance_bf)}</dd>

              <dt className="text-muted-foreground">Payments received</dt>
              <dd className="text-right tabular-nums text-success">{formatLKR(inv.payments_received)}</dd>

              <dt className="text-muted-foreground">Arrears</dt>
              <dd className="text-right tabular-nums">{formatLKR(inv.arrears)}</dd>

              <dt className="text-muted-foreground">Charges for period</dt>
              <dd className="text-right tabular-nums">{formatLKR(inv.charges_for_period)}</dd>

              <Separator className="col-span-2 my-1" />

              <dt className="font-semibold">Total payable</dt>
              <dd className="text-right font-semibold tabular-nums text-primary">{formatLKR(inv.total_payable)}</dd>
            </dl>

            <div className="mt-5 overflow-hidden rounded-lg border border-border">
              <div className="grid grid-cols-[1fr_auto] bg-muted/35 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <span>Description</span>
                <span>Amount</span>
              </div>
              {(charges.length ? charges : inv.line_items).map((item) => (
                <div key={item.id} className="grid grid-cols-[1fr_auto] gap-4 border-t border-border px-4 py-3 text-sm">
                  <span>{item.description}</span>
                  <span className="font-medium tabular-nums">{formatLKR(item.amount)}</span>
                </div>
              ))}
              {taxes.map((item) => (
                <div key={item.id} className="grid grid-cols-[1fr_auto] gap-4 border-t border-border px-4 py-3 text-sm">
                  <span className="inline-flex items-center gap-2">
                    {item.description}
                    <StatusBadge status="tax" />
                  </span>
                  <span className="font-medium tabular-nums">{formatLKR(item.amount)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card shadow-sm">
          <div className="flex items-center gap-3 border-b border-border bg-muted/35 px-4 py-3">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-success/10 text-success">
              <CreditCard size={14} />
            </div>
            <div>
              <h2 className="text-sm font-semibold">Payment history summary</h2>
              <p className="text-xs text-muted-foreground">{paymentCount} payment record{paymentCount === 1 ? '' : 's'}</p>
            </div>
          </div>

          <div className="p-4">
            <div className="rounded-lg border border-border bg-muted/25 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Received for this bill</p>
              <p className="mt-2 text-2xl font-bold tracking-tight tabular-nums text-success">
                {formatLKR(inv.payments_received)}
              </p>
            </div>

            <div className="mt-4 grid gap-3">
              {payments.isPending ? (
                <p className="text-sm text-muted-foreground">Checking payment history...</p>
              ) : recentPayments.length === 0 ? (
                <p className="text-sm text-muted-foreground">No payments recorded for this account yet.</p>
              ) : (
                recentPayments.map((payment) => (
                  <div key={payment.id} className="flex items-center justify-between gap-4 rounded-lg border border-border px-3 py-2">
                    <div>
                      <p className="text-sm font-medium">{payment.method}</p>
                      <p className="text-xs text-muted-foreground">{formatDate(payment.paid_at)}</p>
                    </div>
                    <p className="text-sm font-semibold tabular-nums">{formatLKR(payment.amount)}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </section>

      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-border bg-white/95 p-3 shadow-lg backdrop-blur md:hidden">
        <div className="grid grid-cols-2 gap-2">
          <Button
            size="sm"
            variant="outline"
            disabled={download.isPending}
            onClick={() => download.mutate()}
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
    </div>
  )
}
