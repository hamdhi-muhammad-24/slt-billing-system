import type { ReactNode } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { cn } from '@/lib/utils'
import { EmptyState } from './EmptyState'

export interface ColumnDef<T> {
  header: string
  cell: (row: T) => ReactNode
  numeric?: boolean
}

interface Props<T extends object> {
  columns: ColumnDef<T>[]
  data: T[]
  keyExtractor: (row: T) => string | number
  emptyLabel?: string
  onRowClick?: (row: T) => void
}

export function DataTable<T extends object>({
  columns,
  data,
  keyExtractor,
  emptyLabel = 'No data.',
  onRowClick,
}: Props<T>) {
  if (data.length === 0) return <EmptyState title={emptyLabel} />

  return (
    <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((col, i) => (
              <TableHead key={i} className={col.numeric ? 'text-right' : ''}>
                {col.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((row) => (
            <TableRow
              key={keyExtractor(row)}
              className={cn(onRowClick && 'cursor-pointer')}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
            >
              {columns.map((col, i) => (
                <TableCell key={i} className={col.numeric ? 'text-right' : ''}>
                  {col.cell(row)}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
