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
    <div className="overflow-x-auto rounded-lg border border-border bg-card shadow-sm">
      <Table>
        <TableHeader>
          <TableRow className="border-border bg-muted/55 hover:bg-muted/55">
            {columns.map((col, i) => (
              <TableHead
                key={i}
                className={cn(
                  'h-10 whitespace-nowrap px-4 text-xs font-semibold uppercase tracking-wide text-muted-foreground',
                  col.numeric && 'text-right',
                )}
              >
                {col.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((row) => (
            <TableRow
              key={keyExtractor(row)}
              className={cn(
                'border-border/70 transition-colors hover:bg-accent/35',
                onRowClick && 'cursor-pointer',
              )}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
            >
              {columns.map((col, i) => (
                <TableCell
                  key={i}
                  className={cn(
                    'px-4 py-3 text-sm align-middle',
                    col.numeric && 'text-right font-medium tabular-nums',
                  )}
                >
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
