import { useParams, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import type { Invoice, Payment } from '../../types'
import type { ColumnDef } from '../../components/ui-kit/DataTable'
import { useAuth } from '../../auth/AuthProvider'
import { useAccount } from '../../hooks/useAccount'
import { useCustomerAccounts } from '../../hooks/useCustomerAccounts'
import { useInvoices } from '../../hooks/useInvoices'
import { usePayments } from '../../hooks/usePayments'
import { ErrorState } from '../../components/states'
import { CardSkeleton } from '../../components/ui-kit/Skeletons'
import { DataTable } from '../../components/ui-kit/DataTable'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { ApiError, downloadInvoicePdf } from '../../lib/api'
import { formatLKR } from '../../lib/money'
import { formatDate } from '../../lib/format'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

const INV_COLS: ColumnDef<Invoice>[] = [
  { header: 'Period',   cell: (inv) => <span className="font-medium">{inv.period}</span> },
  { header: 'Due Date', cell: (inv) => formatDate(inv.due_date) },
  { header: 'Amount',   numeric: true, cell: (inv) => formatLKR(inv.total_payable) },
]

const PAY_COLS: ColumnDef<Payment>[] = [
  { header: 'Date',   cell: (p) => formatDate(p.paid_at) },
  { header: 'Method', cell: (p) => p.method },
  { header: 'Amount', numeric: true, cell: (p) => formatLKR(p.amount) },
]

function LatestBillCard({ invoice }: { invoice: Invoice }) {
  const navigate = useNavigate()

  const download = useMutation({
    mutationFn: () => downloadInvoicePdf(invoice.id),
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.detail : 'PDF download failed.')
    },
  })

  return (
    <Card className="border-primary/20 bg-primary/5">
      <CardContent className="pt-5 pb-5 flex flex-col gap-4">
        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Amount Due</p>
          <p className="text-4xl font-bold text-primary mt-1 tabular-nums">
            {formatLKR(invoice.total_payable)}
          </p>
        </div>
        <div className="flex gap-6 text-sm text-muted-foreground">
          <span>Period: <span className="text-foreground font-medium">{invoice.period}</span></span>
          <span>Due: <span className="text-foreground font-medium">{formatDate(invoice.due_date)}</span></span>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button size="sm" onClick={() => navigate(`/app/invoices/${invoice.id}`)}>
            View bill
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled={download.isPending}
            onClick={() => download.mutate()}
          >
            {download.isPending ? 'Downloading…' : 'Download PDF'}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default function CustomerAccountDetail() {
  const { id } = useParams<{ id: string }>()
  const accountId = Number(id)

  const { session } = useAuth()
  const customerId = session?.customerId ?? 0

  // Client-side ownership guard — real enforcement is server-side in the auth phase
  const ownedAccounts = useCustomerAccounts(customerId)
  const account = useAccount(accountId)
  const invoices = useInvoices(accountId)
  const payments = usePayments(accountId)

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
  const navigate = useNavigate()

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title={a.account_no}
        breadcrumbs={[{ label: 'My Accounts', to: '/app' }, { label: a.account_no }]}
      />

      {latestInvoice && (
        <section className="flex flex-col gap-3">
          <h2 className="text-base font-semibold">Latest Bill</h2>
          <LatestBillCard invoice={latestInvoice} />
        </section>
      )}

      <section className="flex flex-col gap-3">
        <h2 className="text-base font-semibold">Bill History</h2>
        <DataTable
          columns={INV_COLS}
          data={sortedInvoices}
          keyExtractor={(inv) => inv.id}
          emptyLabel="No bills yet."
          onRowClick={(inv) => navigate(`/app/invoices/${inv.id}`)}
        />
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-base font-semibold">Payments</h2>
        <DataTable
          columns={PAY_COLS}
          data={payments.data}
          keyExtractor={(p) => p.id}
          emptyLabel="No payments recorded."
        />
      </section>
    </div>
  )
}
