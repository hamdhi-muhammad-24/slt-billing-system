import { useParams, useNavigate } from 'react-router-dom'
import { Hash, IdCard, Mail, MapPin, Phone, UserRound, Wifi } from 'lucide-react'
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

const ACCOUNT_COLS: ColumnDef<Account>[] = [
  { header: 'Account No',    cell: (a) => <span className="font-medium">{a.account_no}</span> },
  { header: 'Status',        cell: (a) => <StatusBadge status={a.status} /> },
  { header: 'Billing Cycle', cell: (a) => a.billing_cycle ?? 'Standard monthly' },
]

const empty = (value: string | null) => value || 'Not recorded'

function initials(name: string): string {
  return name
    .split(' ')
    .slice(0, 2)
    .map((word) => word[0])
    .join('')
    .toUpperCase()
}

function ProfileItem({
  label,
  value,
  icon: Icon,
}: {
  label: string
  value: string
  icon: typeof UserRound
}) {
  return (
    <div className="flex items-start gap-3 rounded-md border border-border bg-muted/25 p-3">
      <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
        <Icon size={16} />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        <p className="mt-1 break-words text-sm font-medium">{value}</p>
      </div>
    </div>
  )
}

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
        description="Customer profile, contact details, and linked billing accounts."
      />

      <section className="surface-section overflow-hidden">
        <div className="flex flex-col gap-5 border-b border-border bg-muted/25 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex min-w-0 items-center gap-4">
            <div className="flex size-14 shrink-0 items-center justify-center rounded-lg bg-primary text-lg font-semibold text-primary-foreground">
              {initials(c.name)}
            </div>
            <div className="min-w-0">
              <p className="truncate text-lg font-semibold">{c.name}</p>
              <p className="mt-1 text-sm text-muted-foreground">Customer #{c.id}</p>
            </div>
          </div>
          <div className="rounded-md border border-border bg-card px-3 py-2 text-sm">
            <p className="text-xs text-muted-foreground">Linked accounts</p>
            <p className="font-semibold tabular-nums">{accounts.data.length}</p>
          </div>
        </div>

        <div className="grid gap-3 p-5 sm:grid-cols-2 xl:grid-cols-3">
          <ProfileItem label="Customer ID" value={`#${c.id}`} icon={Hash} />
          <ProfileItem label="NIC" value={empty(c.nic)} icon={IdCard} />
          <ProfileItem label="Email" value={empty(c.email)} icon={Mail} />
          <ProfileItem label="Phone" value={empty(c.phone)} icon={Phone} />
          <ProfileItem label="Billing address" value={empty(c.address)} icon={MapPin} />
          <ProfileItem label="Service status" value={`${accounts.data.length} account${accounts.data.length === 1 ? '' : 's'} linked`} icon={Wifi} />
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <div className="flex items-end justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Billing accounts</p>
            <h2 className="text-base font-semibold">Linked services</h2>
          </div>
        </div>
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
