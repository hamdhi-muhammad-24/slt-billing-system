import { useParams, useNavigate } from 'react-router-dom'
import { useMemo, useState } from 'react'
import { FileText, Router, Search, WalletCards } from 'lucide-react'
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
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

const SERVICE_TYPE_LABELS: Record<string, string> = {
  VOICE: 'Voice',
  BROADBAND: 'Broadband',
  PEOTV: 'PEO TV',
  BUNDLE: 'Bundle',
  OTHER: 'Other',
}

const SA_COLS: ColumnDef<ServiceAccount>[] = [
  { header: 'Service',    cell: (sa) => <Badge variant="outline">{SERVICE_TYPE_LABELS[sa.service_type] ?? sa.service_type}</Badge> },
  { header: 'Identifier', cell: (sa) => sa.identifier },
  { header: 'Package', cell: (sa) => sa.package_name ?? 'Not assigned' },
  { header: 'Connection', cell: (sa) => sa.connection_type ?? 'Other' },
  { header: 'Status', cell: (sa) => sa.status ? <StatusBadge status={sa.status} /> : 'Not recorded' },
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
  { header: 'Reference', cell: (p) => p.receipt_number ?? p.reference ?? 'Not recorded' },
  { header: 'Status', cell: (p) => p.status ?? 'POSTED' },
  { header: 'Amount',    numeric: true, cell: (p) => formatLKR(p.amount) },
]

type Tab = 'services' | 'invoices' | 'payments'

export default function AccountDetail() {
  const { id } = useParams<{ id: string }>()
  const accountId = Number(id)
  const navigate = useNavigate()
  const [tab, setTab] = useState<Tab>('invoices')
  const [filter, setFilter] = useState('')

  const account = useAccount(accountId)
  const serviceAccounts = useServiceAccounts(accountId)
  const invoices = useInvoices(accountId)
  const payments = usePayments(accountId)

  const invoiceRows = useMemo(() => {
    const q = filter.trim().toLowerCase()
    const rows = invoices.data?.items ?? []
    if (!q) return rows
    return rows.filter((invoice) => invoice.period.includes(q) || invoice.total_payable.includes(q))
  }, [filter, invoices.data])
  const paymentRows = useMemo(() => {
    const q = filter.trim().toLowerCase()
    const rows = payments.data ?? []
    if (!q) return rows
    return rows.filter((payment) =>
      payment.method.toLowerCase().includes(q) ||
      (payment.receipt_number ?? '').toLowerCase().includes(q) ||
      (payment.reference ?? '').toLowerCase().includes(q),
    )
  }, [filter, payments.data])
  const serviceRows = useMemo(() => {
    const q = filter.trim().toLowerCase()
    const rows = serviceAccounts.data ?? []
    if (!q) return rows
    return rows.filter((service) =>
      service.identifier.toLowerCase().includes(q) ||
      service.service_type.toLowerCase().includes(q) ||
      (service.package_name ?? '').toLowerCase().includes(q),
    )
  }, [filter, serviceAccounts.data])

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
  const latestInvoice = invoices.data.items[0]

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={`Account ${a.account_no}`}
        breadcrumbs={[{ label: 'Customers', to: '/admin/customers' }, { label: a.account_no }]}
      />

      <Card className="rounded-lg shadow-sm">
        <CardHeader><CardTitle className="text-base">Account Profile</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-4 lg:grid-cols-[1fr_auto]">
            <dl className="grid gap-x-8 gap-y-3 text-sm sm:grid-cols-[160px_1fr]">
              <dt className="text-muted-foreground">Account No</dt><dd className="font-medium">{a.account_no}</dd>
              <dt className="text-muted-foreground">Status</dt><dd><StatusBadge status={a.status} /></dd>
              <dt className="text-muted-foreground">Telephone</dt><dd>{a.telephone_number ?? 'Not recorded'}</dd>
              <dt className="text-muted-foreground">Service label</dt><dd>{a.service_label ?? 'Not recorded'}</dd>
              <dt className="text-muted-foreground">Billing cycle</dt><dd>{a.billing_cycle ?? 'Standard monthly'}</dd>
              <dt className="text-muted-foreground">Bill delivery</dt><dd>{a.bill_delivery_method ?? 'PORTAL'}</dd>
            </dl>
            <div className="grid min-w-[260px] gap-2 sm:grid-cols-2 lg:grid-cols-1">
              <div className="rounded-md border border-border bg-muted/25 p-3">
                <p className="text-xs text-muted-foreground">Latest payable</p>
                <p className="mt-1 text-xl font-semibold tabular-nums text-primary">
                  {latestInvoice ? formatLKR(latestInvoice.total_payable) : 'No invoice'}
                </p>
              </div>
              <div className="rounded-md border border-border bg-muted/25 p-3">
                <p className="text-xs text-muted-foreground">Linked services</p>
                <p className="mt-1 text-xl font-semibold tabular-nums">{serviceAccounts.data.length}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <section className="surface-section p-4">
        <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap gap-2">
            {[
              ['services', 'Services', Router],
              ['invoices', 'Invoices', FileText],
              ['payments', 'Payments', WalletCards],
            ].map(([key, label, Icon]) => (
              <Button
                key={key as string}
                type="button"
                size="sm"
                variant={tab === key ? 'default' : 'outline'}
                onClick={() => setTab(key as Tab)}
              >
                <Icon size={13} />
                {label as string}
              </Button>
            ))}
          </div>
          <div className="relative w-full lg:max-w-xs">
            <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
              placeholder="Filter current tab"
              className="h-9 pl-9 text-sm"
            />
          </div>
        </div>

        <div className={cn(tab !== 'services' && 'hidden')}>
          <DataTable columns={SA_COLS} data={serviceRows} keyExtractor={(sa) => sa.id} emptyLabel="No service accounts." />
        </div>
        <div className={cn(tab !== 'invoices' && 'hidden')}>
          <DataTable
            columns={INV_COLS}
            data={invoiceRows}
            keyExtractor={(inv) => inv.id}
            emptyLabel="No invoices."
            onRowClick={(inv) => navigate(`/admin/invoices/${inv.id}`)}
          />
        </div>
        <div className={cn(tab !== 'payments' && 'hidden')}>
          <DataTable columns={PAY_COLS} data={paymentRows} keyExtractor={(p) => p.id} emptyLabel="No payments." />
        </div>
      </section>
    </div>
  )
}
