import { useParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useInvoice } from '../../hooks/useInvoice'
import { Loading, ErrorState, Empty } from '../../components/states'
import { ApiError, downloadInvoicePdf } from '../../lib/api'
import { Card, CardAction, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { formatLKR } from '../../lib/money'

export default function InvoiceDetail() {
  const { id } = useParams<{ id: string }>()
  const invoiceId = Number(id)

  const { data: inv, isPending, error } = useInvoice(invoiceId)

  const download = useMutation({
    mutationFn: () => downloadInvoicePdf(invoiceId),
  })

  if (isPending) return <Loading />
  if (error) return <ErrorState detail={error instanceof ApiError ? error.detail : error.message} />

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Invoice — {inv.period}</h1>

      <Card>
        <CardHeader>
          <CardTitle>Snapshot</CardTitle>
          <CardAction>
            <Button
              size="sm"
              disabled={download.isPending}
              onClick={() => download.mutate()}
            >
              {download.isPending ? 'Downloading…' : 'Download PDF'}
            </Button>
          </CardAction>
        </CardHeader>
        <CardContent>
          {download.error && (
            <p className="text-destructive text-sm mb-4">
              {download.error instanceof ApiError ? download.error.detail : download.error.message}
            </p>
          )}
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
            <dt className="text-muted-foreground">Period</dt><dd>{inv.period}</dd>
            <dt className="text-muted-foreground">Issue Date</dt><dd>{inv.issue_date}</dd>
            <dt className="text-muted-foreground">Due Date</dt><dd>{inv.due_date}</dd>
            <dt className="text-muted-foreground border-t border-foreground/10 pt-2 col-span-2" />
            <dt className="text-muted-foreground">Balance B/F</dt><dd>{formatLKR(inv.balance_bf)}</dd>
            <dt className="text-muted-foreground">Payments Received</dt><dd>{formatLKR(inv.payments_received)}</dd>
            <dt className="text-muted-foreground">Arrears</dt><dd>{formatLKR(inv.arrears)}</dd>
            <dt className="text-muted-foreground">Charges for Period</dt><dd>{formatLKR(inv.charges_for_period)}</dd>
            <dt className="text-muted-foreground font-semibold">Total Payable</dt>
            <dd className="font-semibold">{formatLKR(inv.total_payable)}</dd>
          </dl>
        </CardContent>
      </Card>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Line Items</h2>
        {inv.line_items.length === 0
          ? <Empty label="No line items." />
          : (
            <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium">Description</th>
                    <th className="px-4 py-2 text-right font-medium">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {inv.line_items.map((li) => (
                    <tr key={li.id} className="border-t border-foreground/5 hover:bg-muted/30">
                      <td className="px-4 py-2 flex items-center gap-2">
                        {li.description}
                        {li.is_tax && (
                          <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium">
                            Tax
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-2 text-right">{formatLKR(li.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </section>
    </div>
  )
}
