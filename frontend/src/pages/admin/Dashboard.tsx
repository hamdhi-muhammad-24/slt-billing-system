import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  AlertTriangle,
  ArrowRight,
  Bell,
  CheckCircle2,
  FileText,
  Gauge,
  Receipt,
  Search,
  ServerCog,
  ShieldAlert,
  Users,
  Wifi,
} from 'lucide-react'
import type { BillingRun, DashboardRecentInvoice } from '../../types'
import { useCustomers } from '../../hooks/useCustomers'
import { ErrorState } from '../../components/states'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { StatCard } from '../../components/ui-kit/StatCard'
import { DataTable, type ColumnDef } from '../../components/ui-kit/DataTable'
import { StatusBadge } from '../../components/ui-kit/StatusBadge'
import { ApiError, getAdminDashboardSummary } from '../../lib/api'
import { formatDate } from '../../lib/format'
import { formatLKR } from '../../lib/money'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

function DashboardSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Operations" description="SLT-MOBITEL billing operations overview" />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {[0, 1, 2, 3, 4].map((i) => <div key={i} className="h-28 animate-pulse rounded-lg bg-muted" />)}
      </div>
      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="h-72 animate-pulse rounded-lg bg-muted" />
        <div className="h-72 animate-pulse rounded-lg bg-muted" />
      </div>
    </div>
  )
}

function alertClasses(level: string) {
  if (level === 'critical') return 'border-red-200 bg-red-50 text-red-900'
  if (level === 'warning') return 'border-amber-200 bg-amber-50 text-amber-900'
  return 'border-emerald-200 bg-emerald-50 text-emerald-900'
}

const RUN_COLS: ColumnDef<BillingRun & { failures?: unknown[] }>[] = [
  { header: 'Run', cell: (run) => <span className="font-medium">#{run.id}</span> },
  { header: 'Period', cell: (run) => run.period },
  { header: 'Status', cell: (run) => <StatusBadge status={run.status} /> },
  { header: 'Succeeded', numeric: true, cell: (run) => run.succeeded },
  { header: 'Failed', numeric: true, cell: (run) => run.failed },
]

const INVOICE_COLS: ColumnDef<DashboardRecentInvoice>[] = [
  { header: 'Account', cell: (invoice) => <span className="font-medium">{invoice.account_no}</span> },
  { header: 'Customer', cell: (invoice) => invoice.customer_name },
  { header: 'Period', cell: (invoice) => invoice.period },
  { header: 'Issued', cell: (invoice) => formatDate(invoice.issue_date) },
  { header: 'Total', numeric: true, cell: (invoice) => formatLKR(invoice.total_payable) },
]

export default function Dashboard() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const summary = useQuery({
    queryKey: ['admin-dashboard-summary'],
    queryFn: getAdminDashboardSummary,
  })
  const customers = useCustomers(200, 0)

  const dashboardData = summary.data
  const customerMatches = useMemo(() => {
    const q = search.trim().toLowerCase()
    const customerItems = customers.data?.items ?? []
    if (!q) return []
    return customerItems
      .filter((customer) =>
        customer.name.toLowerCase().includes(q) ||
        (customer.nic ?? '').toLowerCase().includes(q) ||
        (customer.email ?? '').toLowerCase().includes(q),
      )
      .slice(0, 5)
  }, [customers.data, search])

  const invoiceMatches = useMemo(() => {
    const q = search.trim().toLowerCase()
    const recentInvoices = dashboardData?.recent_invoices ?? []
    if (!q) return []
    return recentInvoices
      .filter((invoice) =>
        invoice.account_no.toLowerCase().includes(q) ||
        invoice.customer_name.toLowerCase().includes(q),
      )
      .slice(0, 5)
  }, [dashboardData, search])

  const error = summary.error ?? customers.error
  if (summary.isPending || customers.isPending) return <DashboardSkeleton />
  if (error) return <ErrorState detail={error instanceof ApiError ? error.detail : error.message} />
  if (!dashboardData) return <ErrorState detail="Dashboard summary is unavailable." />

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Operations"
        description="Enterprise billing control center for customer records, invoice generation, notifications, and run health."
        actions={(
          <Button size="sm" onClick={() => navigate('/admin/billing')}>
            <Receipt size={14} />
            Open Billing
          </Button>
        )}
      />

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Total customers" value={dashboardData.total_customers} icon={Users} sublabel="Registered profiles" variant="blue" />
        <StatCard label="Active accounts" value={dashboardData.active_accounts} icon={Wifi} sublabel="Billable connections" variant="teal" />
        <StatCard label="Generated invoices" value={dashboardData.generated_invoices} icon={FileText} sublabel="Frozen bill snapshots" variant="green" />
        <StatCard label="Failed runs" value={dashboardData.failed_billing_runs} icon={ShieldAlert} sublabel="Failed or partial batches" variant={dashboardData.failed_billing_runs ? 'amber' : 'default'} />
        <StatCard label="Notifications" value={`${dashboardData.notifications_sent}/${dashboardData.notifications_failed}`} icon={Bell} sublabel="Sent / failed" variant={dashboardData.notifications_failed ? 'amber' : 'purple'} />
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="surface-section p-4">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold">Quick Search</h2>
              <p className="text-xs text-muted-foreground">Search recent accounts or customer records.</p>
            </div>
            <Gauge size={18} className="text-primary" />
          </div>
          <div className="relative">
            <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Account number, customer name, NIC, or email"
              className="h-9 pl-9 text-sm"
            />
          </div>
          <div className="mt-4 grid gap-2">
            {!search.trim() && (
              <div className="rounded-md border border-dashed border-border px-3 py-6 text-center text-sm text-muted-foreground">
                Type to search customer records and recent generated invoices.
              </div>
            )}
            {invoiceMatches.map((invoice) => (
              <button
                key={`invoice-${invoice.id}`}
                type="button"
                onClick={() => navigate(`/admin/invoices/${invoice.id}`)}
                className="flex items-center justify-between rounded-md border border-border bg-white px-3 py-2 text-left text-sm hover:border-primary/35 hover:bg-accent/30"
              >
                <span>
                  <span className="font-medium">{invoice.account_no}</span>
                  <span className="ml-2 text-muted-foreground">{invoice.customer_name}</span>
                </span>
                <ArrowRight size={13} className="text-muted-foreground" />
              </button>
            ))}
            {customerMatches.map((customer) => (
              <button
                key={`customer-${customer.id}`}
                type="button"
                onClick={() => navigate(`/admin/customers/${customer.id}`)}
                className="flex items-center justify-between rounded-md border border-border bg-white px-3 py-2 text-left text-sm hover:border-primary/35 hover:bg-accent/30"
              >
                <span>
                  <span className="font-medium">{customer.name}</span>
                  <span className="ml-2 text-muted-foreground">{customer.nic ?? customer.email}</span>
                </span>
                <ArrowRight size={13} className="text-muted-foreground" />
              </button>
            ))}
            {search.trim() && invoiceMatches.length === 0 && customerMatches.length === 0 && (
              <div className="rounded-md border border-border px-3 py-4 text-center text-sm text-muted-foreground">
                No dashboard matches found.
              </div>
            )}
          </div>
        </div>

        <div className="surface-section p-4">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold">Operational Alerts</h2>
              <p className="text-xs text-muted-foreground">Items that need staff attention.</p>
            </div>
            <ServerCog size={18} className="text-primary" />
          </div>
          <div className="grid gap-2">
            {dashboardData.alerts.map((alert, index) => (
              <div key={`${alert.title}-${index}`} className={cn('rounded-md border px-3 py-3', alertClasses(alert.level))}>
                <div className="flex items-start gap-2">
                  {alert.level === 'success'
                    ? <CheckCircle2 size={15} className="mt-0.5 shrink-0" />
                    : <AlertTriangle size={15} className="mt-0.5 shrink-0" />}
                  <div>
                    <p className="text-sm font-semibold">{alert.title}</p>
                    <p className="mt-1 text-xs leading-5 opacity-80">{alert.detail}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <div className="flex flex-col gap-3">
          <div className="flex items-end justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Billing Jobs</p>
              <h2 className="text-base font-semibold">Recent Billing Runs</h2>
            </div>
            <Button variant="outline" size="sm" onClick={() => navigate('/admin/billing')}>
              Billing workflow
              <ArrowRight size={13} />
            </Button>
          </div>
          <DataTable columns={RUN_COLS} data={dashboardData.recent_billing_runs} keyExtractor={(run) => run.id} emptyLabel="No billing runs." />
        </div>

        <div className="flex flex-col gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Invoices</p>
            <h2 className="text-base font-semibold">Recent Generated Invoices</h2>
          </div>
          <DataTable
            columns={INVOICE_COLS}
            data={dashboardData.recent_invoices}
            keyExtractor={(invoice) => invoice.id}
            emptyLabel="No recent invoices."
            onRowClick={(invoice) => navigate(`/admin/invoices/${invoice.id}`)}
          />
        </div>
      </section>
    </div>
  )
}
