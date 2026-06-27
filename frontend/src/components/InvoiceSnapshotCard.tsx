import type { Invoice, InvoiceLineItem } from '../types'
import type { ColumnDef } from './ui-kit/DataTable'
import { CalendarDays, CreditCard, FileText, ReceiptText } from 'lucide-react'
import { formatLKR } from '../lib/money'
import { formatDate } from '../lib/format'
import { DataTable } from './ui-kit/DataTable'
import { StatusBadge } from './ui-kit/StatusBadge'
import { Separator } from '@/components/ui/separator'
import Brand from './Brand'

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

type InvoiceStatus = 'Paid' | 'Due' | 'Overdue' | 'Generated'

function asNumber(value: string): number {
  const n = Number(value)
  return Number.isFinite(n) ? n : 0
}

function invoiceStatus(invoice: Invoice): InvoiceStatus {
  if (asNumber(invoice.total_payable) <= 0) return 'Paid'
  if (!invoice.due_date) return 'Generated'

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const due = new Date(invoice.due_date)
  due.setHours(0, 0, 0, 0)

  return due < today ? 'Overdue' : 'Due'
}

function DetailTile({
  label,
  value,
  icon: Icon,
}: {
  label: string
  value: string
  icon: typeof FileText
}) {
  return (
    <div className="rounded-md border border-border bg-muted/30 p-4">
      <div className="mb-3 flex size-9 items-center justify-center rounded-md bg-primary/10 text-primary">
        <Icon size={16} />
      </div>
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-semibold tabular-nums">{value}</p>
    </div>
  )
}

export default function InvoiceSnapshotCard({ invoice: inv }: Props) {
  const status = invoiceStatus(inv)

  return (
    <>
      <section className="surface-section overflow-hidden">
        <div className="gradient-primary relative p-5 text-white sm:p-6">
          <div className="network-grid absolute inset-0 opacity-30" />
          <div className="relative flex flex-col gap-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <Brand tone="dark" size="lg" />
              <StatusBadge status={status} />
            </div>
            <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-sm font-medium text-white/72">Total payable</p>
                <p className="mt-2 text-4xl font-semibold tabular-nums sm:text-5xl">
                  {formatLKR(inv.total_payable)}
                </p>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                <div className="rounded-lg border border-white/20 bg-white/10 px-4 py-3 text-sm backdrop-blur">
                  <p className="text-white/65">Billing period</p>
                  <p className="mt-1 font-semibold text-white">{inv.period}</p>
                </div>
                <div className="rounded-lg border border-white/20 bg-white/10 px-4 py-3 text-sm backdrop-blur">
                  <p className="text-white/65">Payment due</p>
                  <p className="mt-1 font-semibold text-white">{formatDate(inv.due_date)}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-4 p-5 lg:grid-cols-[0.95fr_1.05fr]">
          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            <DetailTile label="Issued" value={formatDate(inv.issue_date)} icon={FileText} />
            <DetailTile label="Payment due" value={formatDate(inv.due_date)} icon={CalendarDays} />
            <DetailTile label="Account" value={`#${inv.account_id}`} icon={ReceiptText} />
          </div>

          <div className="rounded-lg border border-border bg-card p-4">
            <div className="mb-4 flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-md bg-success/10 text-success">
                <CreditCard size={18} />
              </div>
              <div>
                <p className="text-sm font-semibold">Invoice breakdown</p>
                <p className="text-xs text-muted-foreground">Charges, payments, and balances</p>
              </div>
            </div>

            <dl className="grid grid-cols-[auto_1fr] gap-x-8 gap-y-3 text-sm">
              <dt className="text-muted-foreground">Balance B/F</dt>
              <dd className="text-right tabular-nums">{formatLKR(inv.balance_bf)}</dd>

              <dt className="text-muted-foreground">Payments received</dt>
              <dd className="text-right tabular-nums">{formatLKR(inv.payments_received)}</dd>

              <dt className="text-muted-foreground">Arrears</dt>
              <dd className="text-right tabular-nums">{formatLKR(inv.arrears)}</dd>

              <dt className="text-muted-foreground">Charges for period</dt>
              <dd className="text-right tabular-nums">{formatLKR(inv.charges_for_period)}</dd>

              <Separator className="col-span-2 my-1" />

              <dt className="font-semibold">Total payable</dt>
              <dd className="text-right font-semibold tabular-nums text-primary">{formatLKR(inv.total_payable)}</dd>
            </dl>
          </div>
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-base font-semibold">Line items</h2>
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
