import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Customer } from '../../types'
import { useCustomers } from '../../hooks/useCustomers'
import { ErrorState } from '../../components/states'
import { TableSkeleton } from '../../components/ui-kit/Skeletons'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { ApiError } from '../../lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Search } from 'lucide-react'
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
  'bg-blue-500/20 text-blue-300',
  'bg-violet-500/20 text-violet-300',
  'bg-emerald-500/20 text-emerald-300',
  'bg-amber-500/20 text-amber-300',
  'bg-rose-500/20 text-rose-300',
  'bg-teal-500/20 text-teal-300',
]

function avatarColor(id: number): string {
  return AVATAR_COLORS[id % AVATAR_COLORS.length]
}

function CustomerRow({ customer, onClick }: { customer: Customer; onClick: () => void }) {
  return (
    <tr
      onClick={onClick}
      className="group cursor-pointer hover:bg-accent/40 transition-colors"
    >
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              'flex size-8 shrink-0 items-center justify-center rounded-full text-xs font-bold',
              avatarColor(customer.id),
            )}
          >
            {getInitials(customer.name)}
          </div>
          <div className="flex flex-col min-w-0">
            <span className="font-medium text-sm truncate">{customer.name}</span>
            <span className="text-xs text-muted-foreground truncate">{customer.email}</span>
          </div>
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-muted-foreground">{customer.nic}</td>
      <td className="px-4 py-3">
        <span className="inline-flex items-center rounded-full bg-primary/10 text-primary px-2 py-0.5 text-xs font-medium">
          #{customer.id}
        </span>
      </td>
    </tr>
  )
}

export default function Customers() {
  const [offset, setOffset] = useState(0)
  const [search, setSearch] = useState('')
  const { data, isPending, error } = useCustomers(PAGE_SIZE, offset)
  const navigate = useNavigate()

  const filtered = useMemo(() => {
    if (!data) return []
    const q = search.trim().toLowerCase()
    if (!q) return data.items
    return data.items.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.email.toLowerCase().includes(q) ||
        c.nic.toLowerCase().includes(q),
    )
  }, [data, search])

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
        description={`${data.total} registered customer${data.total !== 1 ? 's' : ''}`}
      />

      {/* Search bar */}
      <div className="relative max-w-sm">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
        <Input
          placeholder="Search by name, email, or NIC…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9 h-9 text-sm"
        />
      </div>

      {/* Table */}
      <div className="rounded-xl border border-border overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/40">
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Customer</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">NIC</th>
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">ID</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-sm text-muted-foreground">
                  {search ? `No customers matching "${search}".` : 'No customers found.'}
                </td>
              </tr>
            ) : (
              filtered.map((c) => (
                <CustomerRow
                  key={c.id}
                  customer={c}
                  onClick={() => navigate(`/admin/customers/${c.id}`)}
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
