import { useNavigate } from 'react-router-dom'
import { ArrowRight, FileText, Receipt, ShieldCheck, Users } from 'lucide-react'
import { useCustomers } from '../../hooks/useCustomers'
import { ErrorState } from '../../components/states'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { StatCard } from '../../components/ui-kit/StatCard'
import { ApiError } from '../../lib/api'
import { Button } from '@/components/ui/button'

function DashboardSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Dashboard" description="SLT-MOBITEL billing operations overview" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-32 animate-pulse rounded-lg bg-muted" />
        ))}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { data, isPending, error } = useCustomers(1, 0)
  const navigate = useNavigate()

  if (isPending) return <DashboardSkeleton />
  if (error) return <ErrorState detail={error instanceof ApiError ? error.detail : error.message} />

  return (
    <div className="flex flex-col gap-7">
      <PageHeader
        title="Dashboard"
        description="Monitor customer records, invoice generation, and monthly billing operations."
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Customers"
          value={data.total}
          icon={Users}
          sublabel="Registered billing customers"
          variant="blue"
        />
        <StatCard
          label="Invoices"
          value="PDF"
          icon={FileText}
          sublabel="SLT-style bill rendering enabled"
          variant="teal"
        />
        <StatCard
          label="Billing Runs"
          value="Batch"
          icon={Receipt}
          sublabel="Single and monthly runs available"
          variant="green"
        />
        <StatCard
          label="Access"
          value="JWT"
          icon={ShieldCheck}
          sublabel="Admin and customer roles active"
          variant="amber"
        />
      </div>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="surface-section p-5">
          <div className="mb-5 flex items-start justify-between gap-4">
            <div>
              <h2 className="text-base font-semibold">Billing Operations</h2>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">
                Generate invoices for individual accounts or run a full billing batch for a month.
              </p>
            </div>
            <Button size="sm" onClick={() => navigate('/admin/billing')} className="gap-1.5">
              Open Billing
              <ArrowRight size={14} />
            </Button>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-md border border-border bg-muted/25 p-4">
              <p className="text-sm font-medium">Single invoice</p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                Validate account-period data and return a frozen invoice snapshot.
              </p>
            </div>
            <div className="rounded-md border border-border bg-muted/25 p-4">
              <p className="text-sm font-medium">Monthly batch</p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                Process active-account invoices with per-account failure tracking.
              </p>
            </div>
          </div>
        </div>

        <div className="surface-section p-5">
          <h2 className="text-base font-semibold">Customer Administration</h2>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            Review registered customers and drill into billing accounts, invoices, and payments.
          </p>
          <Button
            variant="outline"
            className="mt-5 w-full justify-between"
            onClick={() => navigate('/admin/customers')}
          >
            Browse customer records
            <ArrowRight size={14} />
          </Button>
        </div>
      </section>
    </div>
  )
}
