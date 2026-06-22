import { useParams, Link } from 'react-router-dom'
import { useAccount } from '../../hooks/useAccount'
import { useServiceAccounts } from '../../hooks/useServiceAccounts'
import { useInvoices } from '../../hooks/useInvoices'
import { usePayments } from '../../hooks/usePayments'
import { Loading, ErrorState, Empty } from '../../components/states'
import { ApiError } from '../../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatLKR } from '../../lib/money'

export default function AccountDetail() {
  const { id } = useParams<{ id: string }>()
  const accountId = Number(id)

  const account = useAccount(accountId)
  const serviceAccounts = useServiceAccounts(accountId)
  const invoices = useInvoices(accountId)
  const payments = usePayments(accountId)

  if (account.isPending || serviceAccounts.isPending || invoices.isPending || payments.isPending)
    return <Loading />

  if (account.error) return <ErrorState detail={account.error instanceof ApiError ? account.error.detail : account.error.message} />
  if (serviceAccounts.error) return <ErrorState detail={serviceAccounts.error instanceof ApiError ? serviceAccounts.error.detail : serviceAccounts.error.message} />
  if (invoices.error) return <ErrorState detail={invoices.error instanceof ApiError ? invoices.error.detail : invoices.error.message} />
  if (payments.error) return <ErrorState detail={payments.error instanceof ApiError ? payments.error.detail : payments.error.message} />

  const a = account.data

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Account {a.account_no}</h1>

      <Card>
        <CardHeader><CardTitle>Account Details</CardTitle></CardHeader>
        <CardContent>
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
            <dt className="text-muted-foreground">ID</dt><dd>{a.id}</dd>
            <dt className="text-muted-foreground">Account No</dt><dd>{a.account_no}</dd>
            <dt className="text-muted-foreground">Status</dt><dd className="capitalize">{a.status}</dd>
            <dt className="text-muted-foreground">Billing Cycle</dt><dd>{a.billing_cycle}</dd>
          </dl>
        </CardContent>
      </Card>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Service Accounts</h2>
        {serviceAccounts.data.length === 0
          ? <Empty label="No service accounts." />
          : (
            <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium">Type</th>
                    <th className="px-4 py-2 text-left font-medium">Identifier</th>
                  </tr>
                </thead>
                <tbody>
                  {serviceAccounts.data.map((sa) => (
                    <tr key={sa.id} className="border-t border-foreground/5 hover:bg-muted/30">
                      <td className="px-4 py-2 capitalize">{sa.service_type}</td>
                      <td className="px-4 py-2">{sa.identifier}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Invoices</h2>
        {invoices.data.items.length === 0
          ? <Empty label="No invoices." />
          : (
            <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium">Period</th>
                    <th className="px-4 py-2 text-right font-medium">Total Payable</th>
                  </tr>
                </thead>
                <tbody>
                  {invoices.data.items.map((inv) => (
                    <tr key={inv.id} className="border-t border-foreground/5 hover:bg-muted/30">
                      <td className="px-4 py-2">
                        <Link to={`/admin/invoices/${inv.id}`} className="underline">
                          {inv.period}
                        </Link>
                      </td>
                      <td className="px-4 py-2 text-right">{formatLKR(inv.total_payable)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Payments</h2>
        {payments.data.length === 0
          ? <Empty label="No payments." />
          : (
            <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium">Date</th>
                    <th className="px-4 py-2 text-left font-medium">Method</th>
                    <th className="px-4 py-2 text-left font-medium">Reference</th>
                    <th className="px-4 py-2 text-right font-medium">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {payments.data.map((p) => (
                    <tr key={p.id} className="border-t border-foreground/5 hover:bg-muted/30">
                      <td className="px-4 py-2">{p.paid_at}</td>
                      <td className="px-4 py-2">{p.method}</td>
                      <td className="px-4 py-2">{p.reference}</td>
                      <td className="px-4 py-2 text-right">{formatLKR(p.amount)}</td>
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
