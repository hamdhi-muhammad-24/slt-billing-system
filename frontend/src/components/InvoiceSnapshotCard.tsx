import type { Invoice, InvoiceLineItem } from '../types'
import type { ColumnDef } from './ui-kit/DataTable'
import { formatLKR } from '../lib/money'
import { formatDate } from '../lib/format'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from './ui-kit/DataTable'
import { StatusBadge } from './ui-kit/StatusBadge'
import { Separator } from '@/components/ui/separator'

const LINE_ITEM_COLS: ColumnDef<InvoiceLineItem>[] = [
  {
    header: 'Description',
    cell: (li) => (
      <span className="inline-flex items-center gap-2">
        {li.description}
        {li.is_tax && <StatusBadge status="tax" />}
      </span>
    ),
  },
  {
    header: 'Amount',
    numeric: true,
    cell: (li) => (
      <span className={li.amount.startsWith('-') ? 'text-success font-medium' : ''}>
        {formatLKR(li.amount)}
      </span>
    ),
  },
]

interface Props {
  invoice: Invoice
}

export default function InvoiceSnapshotCard({ invoice: inv }: Props) {
  return (
    <>
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-4">
            <div>
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Payable</CardTitle>
              <p className="text-4xl font-bold text-primary mt-1">{formatLKR(inv.total_payable)}</p>
            </div>
            <div className="text-right text-sm text-muted-foreground">
              <p>Period: <span className="text-foreground font-medium">{inv.period}</span></p>
              <p>Due: <span className="text-foreground font-medium">{formatDate(inv.due_date)}</span></p>
              <p>Issued: <span className="text-foreground">{formatDate(inv.issue_date)}</span></p>
            </div>
          </div>
        </CardHeader>

        <Separator />

        <CardContent className="pt-4">
          <CardDescription className="mb-3 text-xs uppercase tracking-wide">Breakdown</CardDescription>
          <dl className="grid grid-cols-[auto_1fr] gap-x-8 gap-y-2 text-sm">
            <dt className="text-muted-foreground">Balance B/F</dt>
            <dd className="text-right tabular-nums">{formatLKR(inv.balance_bf)}</dd>

            <dt className="text-muted-foreground">Payments Received</dt>
            <dd className="text-right tabular-nums">{formatLKR(inv.payments_received)}</dd>

            <dt className="text-muted-foreground">Arrears</dt>
            <dd className="text-right tabular-nums">{formatLKR(inv.arrears)}</dd>

            <dt className="text-muted-foreground">Charges for Period</dt>
            <dd className="text-right tabular-nums">{formatLKR(inv.charges_for_period)}</dd>

            <Separator className="col-span-2 my-1" />

            <dt className="font-semibold">Total Payable</dt>
            <dd className="text-right tabular-nums font-semibold">{formatLKR(inv.total_payable)}</dd>
          </dl>
        </CardContent>
      </Card>

      <section className="flex flex-col gap-3">
        <h2 className="text-base font-semibold">Line Items</h2>
        <DataTable
          columns={LINE_ITEM_COLS}
          data={inv.line_items}
          keyExtractor={(li) => li.id}
          emptyLabel="No line items."
        />
      </section>
    </>
  )
}
