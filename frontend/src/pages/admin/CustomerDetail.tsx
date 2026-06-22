import { useParams, useNavigate } from 'react-router-dom'
import type { Account } from '../../types'
import type { ColumnDef } from '../../components/ui-kit/DataTable'
import { useCustomer } from '../../hooks/useCustomer'
import { useCustomerAccounts } from '../../hooks/useCustomerAccounts'
import { ErrorState } from '../../components/states'
import { CardSkeleton } from '../../components/ui-kit/Skeletons'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { DataTable } from '../../components/ui-kit/DataTable'
import { StatusBadge } from '../../components/ui-kit/StatusBadge'
import { ApiError } from '../../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const ACCOUNT_COLS: ColumnDef<Account>[] = [
  { header: 'Account No',    cell: (a) => <span className="font-medium">{a.account_no}</span> },
  { header: 'Status',        cell: (a) => <StatusBadge status={a.status} /> },
  { header: 'Billing Cycle', cell: (a) => a.billing_cycle },
]

export default function CustomerDetail() {
  const { id } = useParams<{ id: string }>()
  const customerId = Number(id)
  const navigate = useNavigate()

  const customer = useCustomer(customerId)
  const accounts = useCustomerAccounts(customerId)

  if (customer.isPending || accounts.isPending) return (
    <>
      <PageHeader title="Customer" breadcrumbs={[{ label: 'Customers', to: '/admin/customers' }]} />
      <CardSkeleton />
    </>
  )
  if (customer.error) return <ErrorState detail={customer.error instanceof ApiError ? customer.error.detail : customer.error.message} />
  if (accounts.error) return <ErrorState detail={accounts.error instanceof ApiError ? accounts.error.detail : accounts.error.message} />

  const c = customer.data

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={c.name}
        breadcrumbs={[{ label: 'Customers', to: '/admin/customers' }, { label: c.name }]}
      />

      <Card>
        <CardHeader><CardTitle>Details</CardTitle></CardHeader>
        <CardContent>
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
            <dt className="text-muted-foreground">ID</dt><dd>{c.id}</dd>
            <dt className="text-muted-foreground">NIC</dt><dd>{c.nic}</dd>
            <dt className="text-muted-foreground">Email</dt><dd>{c.email}</dd>
            <dt className="text-muted-foreground">Phone</dt><dd>{c.phone}</dd>
            <dt className="text-muted-foreground">Address</dt><dd>{c.address}</dd>
          </dl>
        </CardContent>
      </Card>

      <section className="flex flex-col gap-3">
        <h2 className="text-base font-semibold">Accounts</h2>
        <DataTable
          columns={ACCOUNT_COLS}
          data={accounts.data}
          keyExtractor={(a) => a.id}
          emptyLabel="No accounts."
          onRowClick={(a) => navigate(`/admin/accounts/${a.id}`)}
        />
      </section>
    </div>
  )
}
