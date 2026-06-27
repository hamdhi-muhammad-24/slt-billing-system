import { useParams, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Download, FileText, CreditCard, ChevronRight } from 'lucide-react'
import type { Invoice, Payment } from '../../types'
import { useAuth } from '../../auth/AuthProvider'
import { useAccount } from '../../hooks/useAccount'
import { useCustomerAccounts } from '../../hooks/useCustomerAccounts'
import { useInvoices } from '../../hooks/useInvoices'
import { usePayments } from '../../hooks/usePayments'
import { ErrorState } from '../../components/states'
import { CardSkeleton } from '../../components/ui-kit/Skeletons'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { StatusBadge } from '../../components/ui-kit/StatusBadge'
import { ApiError, downloadInvoicePdf } from '../../lib/api'
import { formatLKR } from '../../lib/money'
import { formatDate } from '../../lib/format'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

function LatestBillCard({ invoice }: { invoice: Invoice }) {
  const navigate = useNavigate()

  const download = useMutation({
    mutationFn: () => downloadInvoicePdf(invoice.id),
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.detail : 'PDF download failed.')
    },
  })

  return (
    <div className="surface-section flex flex-col gap-5 p-5">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Amount Due</p>
        <p className="mt-1 text-5xl font-semibold tabular-nums text-primary">{formatLKR(invoice.total_payable)}</p>
      </div>
      <div className="flex gap-6 text-sm">
        <div>
          <p className="text-xs text-muted-foreground">Period</p>
          <p className="font-semibold mt-0.5">{invoice.period}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Due Date</p>
          <p className="font-semibold mt-0.5">{formatDate(invoice.due_date)}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Issued</p>
          <p className="font-semibold mt-0.5">{formatDate(invoice.issue_date)}</p>
        </div>
      </div>
      <div className="flex gap-2 flex-wrap">
        <Button
          size="sm"
          className="gap-1.5 font-semibold"
          onClick={() => navigate(`/app/invoices/${invoice.id}`)}
        >
          <FileText size={13} />
          View Bill
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="gap-1.5"
          disabled={download.isPending}
          onClick={() => download.mutate()}
        >
          <Download size={13} />
          {download.isPending ? 'Downloading...' : 'Download PDF'}
        </Button>
      </div>
    </div>
  )
}

function InvoiceRow({ invoice, onClick }: { invoice: Invoice; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group flex w-full items-center justify-between rounded-md px-4 py-3 text-left transition-colors hover:bg-accent/35"
    >
      <div className="flex items-center gap-3">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
          <FileText size={14} />
        </div>
        <div>
          <p className="text-sm font-medium">{invoice.period}</p>
          <p className="text-xs text-muted-foreground">Due {formatDate(invoice.due_date)}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <p className="text-sm font-semibold tabular-nums">{formatLKR(invoice.total_payable)}</p>
        <ChevronRight size={14} className="text-muted-foreground/50 group-hover:text-muted-foreground transition-colors" />
      </div>
    </button>
  )
}

function PaymentTimelineItem({ payment, isLast }: { payment: Payment; isLast: boolean }) {
  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-success/15 text-success">
          <CreditCard size={13} />
        </div>
        {!isLast && <div className="w-px flex-1 bg-border mt-1" />}
      </div>
      <div className={cn('flex flex-col gap-0.5', isLast ? 'pb-0' : 'pb-4')}>
        <p className="text-sm font-medium">{formatLKR(payment.amount)}</p>
        <p className="text-xs text-muted-foreground">{payment.method} - {formatDate(payment.paid_at)}</p>
      </div>
    </div>
  )
}

export default function CustomerAccountDetail() {
  const { id } = useParams<{ id: string }>()
  const accountId = Number(id)
  const navigate = useNavigate()

  const { session } = useAuth()
  const customerId = session?.customerId ?? 0

  const ownedAccounts = useCustomerAccounts(customerId)
  const account = useAccount(accountId)
  const invoices = useInvoices(accountId)
  const payments = usePayments(accountId)
  const stickyDownload = useMutation({
    mutationFn: (invoiceId: number) => downloadInvoicePdf(invoiceId),
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.detail : 'PDF download failed.')
    },
  })

  if (ownedAccounts.isPending || account.isPending || invoices.isPending || payments.isPending)
    return (
      <div className="flex flex-col gap-6">
        <PageHeader title="Account" breadcrumbs={[{ label: 'My Accounts', to: '/app' }]} />
        <CardSkeleton />
        <CardSkeleton />
      </div>
    )

  if (ownedAccounts.error) return <ErrorState detail={ownedAccounts.error instanceof ApiError ? ownedAccounts.error.detail : ownedAccounts.error.message} />
  if (account.error) return <ErrorState detail={account.error instanceof ApiError ? account.error.detail : account.error.message} />
  if (invoices.error) return <ErrorState detail={invoices.error instanceof ApiError ? invoices.error.detail : invoices.error.message} />
  if (payments.error) return <ErrorState detail={payments.error instanceof ApiError ? payments.error.detail : payments.error.message} />

  const owned = ownedAccounts.data.some((a) => a.id === accountId)
  if (!owned) return <ErrorState detail="This account isn't available on your login." />

  const a = account.data
  const sortedInvoices = [...invoices.data.items].sort((x, y) => y.period.localeCompare(x.period))
  const latestInvoice = sortedInvoices[0] ?? null

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title={a.account_no}
        breadcrumbs={[{ label: 'My Accounts', to: '/app' }, { label: a.account_no }]}
        actions={<StatusBadge status={a.status} />}
      />

      {latestInvoice && (
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Latest Bill</h2>
          <LatestBillCard invoice={latestInvoice} />
        </section>
      )}

      <section className="flex flex-col gap-2">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Bill History</h2>
        <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
          {sortedInvoices.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-muted-foreground">No bills yet.</p>
          ) : (
            <div className="divide-y divide-border p-1">
              {sortedInvoices.map((inv) => (
                <InvoiceRow
                  key={inv.id}
                  invoice={inv}
                  onClick={() => navigate(`/app/invoices/${inv.id}`)}
                />
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Payment History</h2>
        {payments.data.length === 0 ? (
          <p className="text-sm text-muted-foreground">No payments recorded.</p>
        ) : (
          <div className="pt-1">
            {[...payments.data]
              .sort((a, b) => b.paid_at.localeCompare(a.paid_at))
              .map((p, i, arr) => (
                <PaymentTimelineItem key={p.id} payment={p} isLast={i === arr.length - 1} />
              ))}
          </div>
        )}
      </section>

      {latestInvoice && (
        <div className="fixed inset-x-0 bottom-0 z-30 border-t border-border bg-white/95 p-3 shadow-lg backdrop-blur md:hidden">
          <div className="grid grid-cols-2 gap-2">
            <Button
              size="sm"
              variant="outline"
              className="gap-1.5"
              disabled={stickyDownload.isPending}
              onClick={() => stickyDownload.mutate(latestInvoice.id)}
            >
              <Download size={13} />
              Download
            </Button>
            <Button
              size="sm"
              className="gap-1.5"
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
