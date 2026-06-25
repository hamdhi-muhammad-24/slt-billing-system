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
import { Button } from '@/components/ui/button'
import { Inbox, Wifi, ArrowRight } from 'lucide-react'

function AccountCard({ account }: { account: Account }) {
  return (
    <div className="rounded-xl border border-border bg-card shadow-sm hover:shadow-md transition-shadow flex flex-col gap-0 overflow-hidden">
      {/* Card top bar */}
      <div className="gradient-primary px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-white/20">
            <Wifi size={13} className="text-white" />
          </div>
          <span className="text-white font-semibold text-sm">{account.account_no}</span>
        </div>
        <StatusBadge status={account.status} />
      </div>

      {/* Card body */}
      <div className="px-4 py-3 flex flex-col gap-3">
        <p className="text-sm text-muted-foreground capitalize">{account.billing_cycle} billing</p>
        <Link to={`/app/accounts/${account.id}`} className="block">
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-between group hover:border-primary/40 hover:text-primary transition-colors"
          >
            View invoices
            <ArrowRight size={13} className="transition-transform group-hover:translate-x-0.5" />
          </Button>
        </Link>
      </div>
    </div>
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
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Your Accounts ({accounts.data.length})
        </h2>
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
