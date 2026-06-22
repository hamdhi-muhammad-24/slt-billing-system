import { useParams, useNavigate } from 'react-router-dom'
import type { Invoice, Payment, ServiceAccount } from '../../types'
import type { ColumnDef } from '../../components/ui-kit/DataTable'
import { useAccount } from '../../hooks/useAccount'
import { useServiceAccounts } from '../../hooks/useServiceAccounts'
import { useInvoices } from '../../hooks/useInvoices'
import { usePayments } from '../../hooks/usePayments'
import { ErrorState } from '../../components/states'
import { CardSkeleton } from '../../components/ui-kit/Skeletons'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { DataTable } from '../../components/ui-kit/DataTable'
import { StatusBadge } from '../../components/ui-kit/StatusBadge'
import { ApiError } from '../../lib/api'
import { formatLKR } from '../../lib/money'
import { formatDate } from '../../lib/format'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const SERVICE_TYPE_LABELS: Record<string, string> = {
  voice: 'Voice', broadband: 'Broadband', peotv: 'PEO TV',
}

const SA_COLS: ColumnDef<ServiceAccount>[] = [
  { header: 'Service',    cell: (sa) => <Badge variant="outline">{SERVICE_TYPE_LABELS[sa.service_type] ?? sa.service_type}</Badge> },
  { header: 'Identifier', cell: (sa) => sa.identifier },
]

const INV_COLS: ColumnDef<Invoice>[] = [
  { header: 'Period',      cell: (inv) => <span className="font-medium">{inv.period}</span> },
  { header: 'Issue Date',  cell: (inv) => formatDate(inv.issue_date) },
  { header: 'Due Date',    cell: (inv) => formatDate(inv.due_date) },
  { header: 'Total Payable', numeric: true, cell: (inv) => formatLKR(inv.total_payable) },
]

const PAY_COLS: ColumnDef<Payment>[] = [
  { header: 'Date',      cell: (p) => formatDate(p.paid_at) },
  { header: 'Method',    cell: (p) => p.method },
  { header: 'Reference', cell: (p) => p.reference },
  { header: 'Amount',    numeric: true, cell: (p) => formatLKR(p.amount) },
]

export default function AccountDetail() {
  const { id } = useParams<{ id: string }>()
  const accountId = Number(id)
  const navigate = useNavigate()

  const account = useAccount(accountId)
  const serviceAccounts = useServiceAccounts(accountId)
  const invoices = useInvoices(accountId)
  const payments = usePayments(accountId)

  if (account.isPending || serviceAccounts.isPending || invoices.isPending || payments.isPending)
    return (
      <>
        <PageHeader title="Account" />
        <CardSkeleton />
      </>
    )

  if (account.error) return <ErrorState detail={account.error instanceof ApiError ? account.error.detail : account.error.message} />
  if (serviceAccounts.error) return <ErrorState detail={serviceAccounts.error instanceof ApiError ? serviceAccounts.error.detail : serviceAccounts.error.message} />
  if (invoices.error) return <ErrorState detail={invoices.error instanceof ApiError ? invoices.error.detail : invoices.error.message} />
  if (payments.error) return <ErrorState detail={payments.error instanceof ApiError ? payments.error.detail : payments.error.message} />

  const a = account.data

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={`Account ${a.account_no}`}
        breadcrumbs={[{ label: 'Customers', to: '/admin/customers' }, { label: a.account_no }]}
      />

      <Card>
        <CardHeader><CardTitle>Summary</CardTitle></CardHeader>
        <CardContent>
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
            <dt className="text-muted-foreground">Account No</dt><dd className="font-medium">{a.account_no}</dd>
            <dt className="text-muted-foreground">Status</dt><dd><StatusBadge status={a.status} /></dd>
            <dt className="text-muted-foreground">Billing Cycle</dt><dd>{a.billing_cycle}</dd>
          </dl>
        </CardContent>
      </Card>

      <section className="flex flex-col gap-3">
        <h2 className="text-base font-semibold">Service Accounts</h2>
        <DataTable
          columns={SA_COLS}
          data={serviceAccounts.data}
          keyExtractor={(sa) => sa.id}
          emptyLabel="No service accounts."
        />
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-base font-semibold">Invoices</h2>
        <DataTable
          columns={INV_COLS}
          data={invoices.data.items}
          keyExtractor={(inv) => inv.id}
          emptyLabel="No invoices."
          onRowClick={(inv) => navigate(`/admin/invoices/${inv.id}`)}
        />
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-base font-semibold">Payments</h2>
        <DataTable
          columns={PAY_COLS}
          data={payments.data}
          keyExtractor={(p) => p.id}
          emptyLabel="No payments."
        />
      </section>
    </div>
  )
}
