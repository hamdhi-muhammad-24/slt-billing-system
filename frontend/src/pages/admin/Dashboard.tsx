import { Link } from 'react-router-dom'
import { useCustomers } from '../../hooks/useCustomers'
import { Loading, ErrorState } from '../../components/states'
import { ApiError } from '../../lib/api'

export default function Dashboard() {
  const { data, isPending, error } = useCustomers(1, 0)

  if (isPending) return <Loading />
  if (error) return <ErrorState detail={error instanceof ApiError ? error.detail : error.message} />

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <p className="text-muted-foreground">
        Customers: <span className="text-foreground font-semibold">{data.total}</span>
      </p>
      <div className="flex gap-4">
        <Link to="/admin/customers" className="underline text-sm">Customers</Link>
        <Link to="/admin/billing" className="underline text-sm">Billing</Link>
      </div>
    </div>
  )
}
