import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'
import type { Customer } from '../../types'
import { useCustomers } from '../../hooks/useCustomers'
import { ErrorState } from '../../components/states'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { TableSkeleton } from '../../components/ui-kit/Skeletons'
import { ApiError } from '../../lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

const PAGE_SIZE = 50

function getInitials(name: string): string {
  return name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase()
}

const AVATAR_COLORS = [
  'bg-blue-500/12 text-blue-700',
  'bg-cyan-500/12 text-cyan-700',
  'bg-emerald-500/12 text-emerald-700',
  'bg-amber-500/12 text-amber-700',
  'bg-violet-500/12 text-violet-700',
  'bg-teal-500/12 text-teal-700',
]

function avatarColor(id: number): string {
  return AVATAR_COLORS[id % AVATAR_COLORS.length]
}

function CustomerRow({ customer, onClick }: { customer: Customer; onClick: () => void }) {
  const email = customer.email ?? 'Email not recorded'
  const address = customer.address ?? 'Address not recorded'

  return (
    <tr onClick={onClick} className="group cursor-pointer transition-colors hover:bg-accent/35">
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <div className={cn('flex size-9 shrink-0 items-center justify-center rounded-md text-xs font-semibold', avatarColor(customer.id))}>
            {getInitials(customer.name)}
          </div>
          <div className="flex min-w-0 flex-col">
            <span className="truncate text-sm font-medium">{customer.name}</span>
            <span className="truncate text-xs text-muted-foreground">{email}</span>
          </div>
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-muted-foreground">{address}</td>
      <td className="px-4 py-3">
        <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
          #{customer.id}
        </span>
      </td>
    </tr>
  )
}

export default function Customers() {
  const [offset, setOffset] = useState(0)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('ALL')
  const { data, isPending, error } = useCustomers(PAGE_SIZE, offset)
  const navigate = useNavigate()

  const customerTypes = useMemo(() => {
    const types = new Set((data?.items ?? []).map((customer) => customer.customer_type).filter(Boolean))
    return ['ALL', ...Array.from(types)] as string[]
  }, [data])

  const filtered = useMemo(() => {
    if (!data) return []
    const q = search.trim().toLowerCase()
    return data.items.filter((c) => {
      const matchesSearch = !q ||
        c.name.toLowerCase().includes(q) ||
        (c.email ?? '').toLowerCase().includes(q) ||
        (c.nic ?? '').toLowerCase().includes(q) ||
        (c.address ?? '').toLowerCase().includes(q)
      const matchesType = typeFilter === 'ALL' || c.customer_type === typeFilter
      return matchesSearch && matchesType
    })
  }, [data, search, typeFilter])

  if (isPending) return (
    <>
      <PageHeader title="Customers" />
      <TableSkeleton rows={6} cols={3} />
    </>
  )
  if (error) return <ErrorState detail={error instanceof ApiError ? error.detail : error.message} />

  const totalPages = Math.ceil(data.total / PAGE_SIZE)
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Customers"
        description={`${data.total} registered customer${data.total !== 1 ? 's' : ''} available to billing administrators.`}
      />

      <div className="surface-section p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative w-full lg:max-w-md">
            <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search by name, email, NIC, or address..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-9 bg-white pl-9 text-sm"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            {customerTypes.map((type) => (
              <Button
                key={type}
                type="button"
                variant={typeFilter === type ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTypeFilter(type)}
              >
                {type === 'ALL' ? 'All types' : type}
              </Button>
            ))}
          </div>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/55">
              <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Customer</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Address</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">ID</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-sm text-muted-foreground">
                  {search || typeFilter !== 'ALL' ? 'No customers match the current filters.' : 'No customers found.'}
                </td>
              </tr>
            ) : (
              filtered.map((customer) => (
                <CustomerRow
                  key={customer.id}
                  customer={customer}
                  onClick={() => navigate(`/admin/customers/${customer.id}`)}
                />
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center gap-4 text-sm">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            disabled={offset === 0}
          >
            Previous
          </Button>
          <span className="text-muted-foreground">Page {currentPage} of {totalPages}</span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setOffset(offset + PAGE_SIZE)}
            disabled={currentPage >= totalPages}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  )
}
