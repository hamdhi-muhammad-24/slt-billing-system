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
    <>
      <PageHeader title="Dashboard" />
      <TableSkeleton rows={1} cols={2} />
    </>
  )
  if (error) return <ErrorState detail={error instanceof ApiError ? error.detail : error.message} />

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Dashboard" description="SLT e-Bill system overview" />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          label="Customers"
          value={data.total}
          icon={Users}
          sublabel="Registered accounts"
        />
        <StatCard
          label="Customers"
          value="View →"
          icon={Users}
          sublabel="Browse all customers"
        />
        <StatCard
          label="Billing"
          value="Generate →"
          icon={Receipt}
          sublabel="Create or batch invoices"
        />
      </div>

      <div className="flex gap-3">
        <button
          onClick={() => navigate('/admin/customers')}
          className="text-sm text-primary underline underline-offset-2"
        >
          Go to Customers
        </button>
        <button
          onClick={() => navigate('/admin/billing')}
          className="text-sm text-primary underline underline-offset-2"
        >
          Go to Billing
        </button>
      </div>
    </div>
  )
}
