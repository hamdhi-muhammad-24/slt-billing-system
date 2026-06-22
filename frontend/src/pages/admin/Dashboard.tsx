import { useNavigate } from 'react-router-dom'
import { Users, Receipt } from 'lucide-react'
import { useCustomers } from '../../hooks/useCustomers'
import { ErrorState } from '../../components/states'
import { TableSkeleton } from '../../components/ui-kit/Skeletons'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { StatCard } from '../../components/ui-kit/StatCard'
import { ApiError } from '../../lib/api'

export default function Dashboard() {
  const { data, isPending, error } = useCustomers(1, 0)
  const navigate = useNavigate()

  if (isPending) return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Dashboard" />
      <TableSkeleton rows={1} cols={3} />
    </div>
  )
  if (error) return <ErrorState detail={error instanceof ApiError ? error.detail : error.message} />

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Dashboard" description="SLT e-Bill system overview" />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          label="Total Customers"
          value={data.total}
          icon={Users}
          sublabel="Registered in the system"
        />
        <div
          role="button"
          tabIndex={0}
          className="cursor-pointer rounded-xl focus-visible:outline-2 focus-visible:outline-ring focus-visible:outline-offset-2 hover:opacity-90 transition-opacity"
          onClick={() => navigate('/admin/customers')}
          onKeyDown={(e) => e.key === 'Enter' && navigate('/admin/customers')}
        >
          <StatCard
            label="Customers"
            value="Browse →"
            icon={Users}
            sublabel="View all customer accounts"
          />
        </div>
        <div
          role="button"
          tabIndex={0}
          className="cursor-pointer rounded-xl focus-visible:outline-2 focus-visible:outline-ring focus-visible:outline-offset-2 hover:opacity-90 transition-opacity"
          onClick={() => navigate('/admin/billing')}
          onKeyDown={(e) => e.key === 'Enter' && navigate('/admin/billing')}
        >
          <StatCard
            label="Billing"
            value="Generate →"
            icon={Receipt}
            sublabel="Create or batch invoices"
          />
        </div>
      </div>
    </div>
  )
}
