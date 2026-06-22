import { Link } from 'react-router-dom'
import type { Account } from '../../types'
import { useAuth } from '../../auth/AuthProvider'
import { useCustomer } from '../../hooks/useCustomer'
import { useCustomerAccounts } from '../../hooks/useCustomerAccounts'
import { ErrorState } from '../../components/states'
import { CardSkeleton } from '../../components/ui-kit/Skeletons'
import { EmptyState } from '../../components/ui-kit/EmptyState'
import { StatusBadge } from '../../components/ui-kit/StatusBadge'
import { ApiError } from '../../lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Inbox } from 'lucide-react'

function AccountCard({ account }: { account: Account }) {
  return (
    <Card>
      <CardContent className="pt-5 pb-5 flex flex-col gap-3">
        <div className="flex items-start justify-between gap-3">
          <p className="text-lg font-semibold tracking-tight">{account.account_no}</p>
          <StatusBadge status={account.status} />
        </div>
        <p className="text-sm text-muted-foreground capitalize">{account.billing_cycle} billing</p>
        <Link to={`/app/accounts/${account.id}`}>
          <Button variant="outline" size="sm" className="w-full sm:w-auto">
            View bills →
          </Button>
        </Link>
      </CardContent>
    </Card>
  )
}

export default function MyAccounts() {
  const { session } = useAuth()
  const customerId = session?.customerId ?? 0

  const customer = useCustomer(customerId)
  const accounts = useCustomerAccounts(customerId)

  if (customer.isPending || accounts.isPending) return (
    <div className="flex flex-col gap-6">
      <div className="h-8 w-56 bg-muted animate-pulse rounded-md" />
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    </div>
  )

  if (customer.error) return <ErrorState detail={customer.error instanceof ApiError ? customer.error.detail : customer.error.message} />
  if (accounts.error) return <ErrorState detail={accounts.error instanceof ApiError ? accounts.error.detail : accounts.error.message} />

  return (
    <div className="flex flex-col gap-8">
      <div>
        <p className="text-sm text-muted-foreground">Welcome back</p>
        <h1 className="text-2xl font-bold tracking-tight">Hello, {customer.data.name}</h1>
      </div>

      <section className="flex flex-col gap-4">
        <h2 className="text-base font-semibold">Your Accounts</h2>
        {accounts.data.length === 0
          ? (
            <EmptyState
              icon={Inbox}
              title="No accounts linked to your login yet"
              hint="Contact SLT support if you believe this is an error."
            />
          )
          : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {accounts.data.map((a) => <AccountCard key={a.id} account={a} />)}
            </div>
          )}
      </section>
    </div>
  )
}
