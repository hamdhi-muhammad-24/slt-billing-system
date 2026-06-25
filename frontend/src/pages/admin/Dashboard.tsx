import { useNavigate } from 'react-router-dom'
import { Users, Receipt, ArrowRight, TrendingUp } from 'lucide-react'
import { useCustomers } from '../../hooks/useCustomers'
import { ErrorState } from '../../components/states'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { StatCard } from '../../components/ui-kit/StatCard'
import { ApiError } from '../../lib/api'
import { cn } from '@/lib/utils'

function QuickActionCard({
  title,
  subtitle,
  gradient,
  onClick,
}: {
  title: string
  subtitle: string
  gradient: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'group w-full text-left rounded-xl p-5 shadow-lg border-0 transition-all duration-200',
        'hover:scale-[1.02] hover:shadow-xl focus-visible:outline-2 focus-visible:outline-ring focus-visible:outline-offset-2',
        gradient,
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <p className="text-white/75 text-sm font-medium">{title}</p>
          <p className="text-white text-xl font-bold">{subtitle}</p>
        </div>
        <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-white/20 text-white transition-transform group-hover:translate-x-1">
          <ArrowRight size={16} />
        </div>
      </div>
    </button>
  )
}

function DashboardSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Dashboard" description="SLT e-Bill system overview" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {[0, 1, 2].map((i) => (
          <div key={i} className="rounded-xl p-5 bg-muted animate-pulse h-28" />
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
    <div className="flex flex-col gap-8">
      <PageHeader title="Dashboard" description="SLT e-Bill system overview" />

      {/* Stat row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          label="Total Customers"
          value={data.total}
          icon={Users}
          sublabel="Registered in the system"
          variant="blue"
        />
        <StatCard
          label="Active Accounts"
          value="—"
          icon={TrendingUp}
          sublabel="Across all customers"
          variant="teal"
        />
        <StatCard
          label="Billing Runs"
          value="—"
          icon={Receipt}
          sublabel="Generated this month"
          variant="green"
        />
      </div>

      {/* Quick actions */}
      <div className="flex flex-col gap-3">
        <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Quick Actions</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <QuickActionCard
            title="Customers"
            subtitle="Browse all accounts →"
            gradient="gradient-primary"
            onClick={() => navigate('/admin/customers')}
          />
          <QuickActionCard
            title="Billing"
            subtitle="Generate invoices →"
            gradient="gradient-success"
            onClick={() => navigate('/admin/billing')}
          />
        </div>
      </div>
    </div>
  )
}
