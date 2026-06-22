import { useParams, Link } from 'react-router-dom'
import { useCustomer } from '../../hooks/useCustomer'
import { useCustomerAccounts } from '../../hooks/useCustomerAccounts'
import { Loading, ErrorState, Empty } from '../../components/states'
import { ApiError } from '../../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function CustomerDetail() {
  const { id } = useParams<{ id: string }>()
  const customerId = Number(id)

  const customer = useCustomer(customerId)
  const accounts = useCustomerAccounts(customerId)

  if (customer.isPending || accounts.isPending) return <Loading />
  if (customer.error) return <ErrorState detail={customer.error instanceof ApiError ? customer.error.detail : customer.error.message} />
  if (accounts.error) return <ErrorState detail={accounts.error instanceof ApiError ? accounts.error.detail : accounts.error.message} />

  const c = customer.data

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">{c.name}</h1>

      <Card>
        <CardHeader>
          <CardTitle>Customer Details</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
            <dt className="text-muted-foreground">ID</dt><dd>{c.id}</dd>
            <dt className="text-muted-foreground">NIC</dt><dd>{c.nic}</dd>
            <dt className="text-muted-foreground">Email</dt><dd>{c.email}</dd>
            <dt className="text-muted-foreground">Phone</dt><dd>{c.phone}</dd>
            <dt className="text-muted-foreground">Address</dt><dd>{c.address}</dd>
          </dl>
        </CardContent>
      </Card>

      <div className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Accounts</h2>
        {accounts.data.length === 0
          ? <Empty label="No accounts." />
          : (
            <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium">Account No</th>
                    <th className="px-4 py-2 text-left font-medium">Status</th>
                    <th className="px-4 py-2 text-left font-medium">Billing Cycle</th>
                  </tr>
                </thead>
                <tbody>
                  {accounts.data.map((a) => (
                    <tr key={a.id} className="border-t border-foreground/5 hover:bg-muted/30">
                      <td className="px-4 py-2">
                        <Link to={`/admin/accounts/${a.id}`} className="underline">
                          {a.account_no}
                        </Link>
                      </td>
                      <td className="px-4 py-2 capitalize">{a.status}</td>
                      <td className="px-4 py-2">{a.billing_cycle}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </div>
    </div>
  )
}
