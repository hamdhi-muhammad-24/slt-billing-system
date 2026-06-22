import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Customer } from '../../types'
import type { ColumnDef } from '../../components/ui-kit/DataTable'
import { useCustomers } from '../../hooks/useCustomers'
import { ErrorState } from '../../components/states'
import { TableSkeleton } from '../../components/ui-kit/Skeletons'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { DataTable } from '../../components/ui-kit/DataTable'
import { ApiError } from '../../lib/api'
import { Button } from '@/components/ui/button'

const PAGE_SIZE = 50

const COLS: ColumnDef<Customer>[] = [
  { header: 'ID',    cell: (c) => c.id },
  { header: 'Name',  cell: (c) => <span className="font-medium">{c.name}</span> },
  { header: 'NIC',   cell: (c) => c.nic },
  { header: 'Email', cell: (c) => c.email },
]

export default function Customers() {
  const [offset, setOffset] = useState(0)
  const { data, isPending, error } = useCustomers(PAGE_SIZE, offset)
  const navigate = useNavigate()

  if (isPending) return (
    <>
      <PageHeader title="Customers" />
      <TableSkeleton rows={6} cols={4} />
    </>
  )
  if (error) return <ErrorState detail={error instanceof ApiError ? error.detail : error.message} />

  const totalPages = Math.ceil(data.total / PAGE_SIZE)
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Customers" description={`${data.total} registered customer${data.total !== 1 ? 's' : ''}`} />

      <DataTable
        columns={COLS}
        data={data.items}
        keyExtractor={(c) => c.id}
        emptyLabel="No customers found."
        onRowClick={(c) => navigate(`/admin/customers/${c.id}`)}
      />

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
