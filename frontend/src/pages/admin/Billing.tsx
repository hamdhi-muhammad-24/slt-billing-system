import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  AlertTriangle,
  CheckCircle2,
  Circle,
  FileCheck2,
  Loader2,
  RefreshCw,
  Search,
  Send,
} from 'lucide-react'
import type { Account, BillingRun, BillingRunFailure } from '../../types'
import type { ColumnDef } from '../../components/ui-kit/DataTable'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { DataTable } from '../../components/ui-kit/DataTable'
import { StatusBadge } from '../../components/ui-kit/StatusBadge'
import { ErrorState } from '../../components/states'
import { CardSkeleton } from '../../components/ui-kit/Skeletons'
import { useCustomers } from '../../hooks/useCustomers'
import { ApiError, generateBatch, generateOne, getBillingRun, listCustomerAccounts } from '../../lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

type ScopeMode = 'all' | 'single'

function errDetail(err: unknown): string {
  return err instanceof ApiError ? err.detail : String(err)
}

function currentPeriod(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

function StepRail({ active }: { active: number }) {
  const steps = ['Month', 'Scope', 'Validate', 'Generate', 'Summary']
  return (
    <div className="grid gap-2 md:grid-cols-5">
      {steps.map((label, index) => {
        const step = index + 1
        const done = step < active
        const isActive = step === active
        return (
          <div
            key={label}
            className={cn(
              'flex items-center gap-2 rounded-lg border px-3 py-2 text-sm',
              isActive && 'border-primary bg-primary/5 text-primary',
              done && 'border-success/25 bg-success/5 text-success',
              !done && !isActive && 'border-border bg-white text-muted-foreground',
            )}
          >
            <span className={cn('flex size-6 items-center justify-center rounded-md text-xs font-semibold', done ? 'bg-success text-white' : isActive ? 'bg-primary text-white' : 'bg-muted')}>
              {done ? <CheckCircle2 size={13} /> : step}
            </span>
            {label}
          </div>
        )
      })}
    </div>
  )
}

function FailureTable({ failures }: { failures: BillingRunFailure[] }) {
  const cols: ColumnDef<BillingRunFailure>[] = [
    { header: 'Account ID', cell: (failure) => failure.account_id ?? 'Unknown' },
    { header: 'Reason', cell: (failure) => <span className="text-muted-foreground">{failure.error}</span> },
  ]
  return <DataTable columns={cols} data={failures} keyExtractor={(failure) => failure.id} emptyLabel="No failed accounts." />
}

export default function Billing() {
  const [period, setPeriod] = useState(currentPeriod())
  const [scope, setScope] = useState<ScopeMode>('all')
  const [accountSearch, setAccountSearch] = useState('')
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null)
  const [runId, setRunId] = useState<number | null>(null)
  const navigate = useNavigate()
  const qc = useQueryClient()

  const customers = useCustomers(200, 0)
  const accountQueries = useQueries({
    queries: (customers.data?.items ?? []).map((customer) => ({
      queryKey: ['customerAccounts', customer.id, 'billing-picker'],
      queryFn: () => listCustomerAccounts(customer.id),
      enabled: Boolean(customers.data),
    })),
  })

  const run = useQuery({
    queryKey: ['billingRun', runId],
    queryFn: () => getBillingRun(runId!),
    enabled: runId !== null,
    refetchInterval: (q) => {
      const status = q.state.data?.status
      return status === 'pending' || status === 'running' ? 1500 : false
    },
  })

  const allAccounts = useMemo(
    () => accountQueries.flatMap((query) => query.data ?? []),
    [accountQueries],
  )
  const selectedAccount = allAccounts.find((account) => account.id === selectedAccountId) ?? null
  const activeAccounts = allAccounts.filter((account) => account.status === 'ACTIVE')
  const filteredAccounts = allAccounts
    .filter((account) => {
      const q = accountSearch.trim().toLowerCase()
      if (!q) return true
      return account.account_no.toLowerCase().includes(q) || String(account.id).includes(q)
    })
    .slice(0, 8)

  const generateOneMutation = useMutation({
    mutationFn: () => generateOne({ account_id: selectedAccountId!, period }),
    onSuccess: (invoice) => {
      qc.invalidateQueries({ queryKey: ['invoices', selectedAccountId] })
      toast.success(`Invoice ${invoice.id} is ready.`)
      navigate(`/admin/invoices/${invoice.id}`)
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 409) toast.info('Invoice already exists for that account and period.')
      else toast.error(errDetail(err))
    },
  })

  const generateBatchMutation = useMutation({
    mutationFn: () => generateBatch({ period }),
    onSuccess: (billingRun: BillingRun) => {
      setRunId(billingRun.id)
      qc.invalidateQueries({ queryKey: ['admin-dashboard-summary'] })
      toast.success(`Billing run #${billingRun.id} completed.`)
    },
    onError: (err) => toast.error(errDetail(err)),
  })

  if (customers.isPending || accountQueries.some((query) => query.isPending)) {
    return (
      <div className="flex flex-col gap-6">
        <PageHeader title="Billing Workflow" />
        <CardSkeleton />
        <CardSkeleton />
      </div>
    )
  }
  const loadError = customers.error ?? accountQueries.find((query) => query.error)?.error
  if (loadError) return <ErrorState detail={loadError instanceof ApiError ? loadError.detail : loadError.message} />

  const canValidate = scope === 'all' || selectedAccountId !== null
  const validationRows = [
    { label: 'Billing month', value: period, ok: /^\d{4}-(0[1-9]|1[0-2])$/.test(period) },
    { label: 'Billing scope', value: scope === 'all' ? `${activeAccounts.length} active accounts` : selectedAccount ? selectedAccount.account_no : 'No account selected', ok: canValidate },
    { label: 'Data readiness', value: allAccounts.length > 0 ? 'Accounts loaded' : 'No accounts found', ok: allAccounts.length > 0 },
  ]
  const validationOk = validationRows.every((row) => row.ok)
  const activeStep = run.data ? 5 : generateBatchMutation.isPending || generateOneMutation.isPending ? 4 : validationOk ? 3 : scope === 'single' ? 2 : 1

  function generate() {
    if (!validationOk) {
      toast.error('Fix validation issues before generation.')
      return
    }
    if (scope === 'single') generateOneMutation.mutate()
    else generateBatchMutation.mutate()
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Billing Workflow"
        description="Generate invoices through a controlled staff workflow: select period, choose scope, validate data, generate, and review results."
      />

      <StepRail active={activeStep} />

      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="surface-section p-5">
          <div className="mb-4 flex items-center gap-2">
            <Circle size={14} className="text-primary" />
            <h2 className="text-base font-semibold">1. Select Billing Month</h2>
          </div>
          <Label htmlFor="billing-period">Billing month</Label>
          <Input
            id="billing-period"
            value={period}
            onChange={(event) => setPeriod(event.target.value)}
            className="mt-2 max-w-xs"
            placeholder="YYYY-MM"
          />
          <p className="mt-2 text-xs text-muted-foreground">Use the invoice billing month, for example 2026-06.</p>
        </div>

        <div className="surface-section p-5">
          <div className="mb-4 flex items-center gap-2">
            <Circle size={14} className="text-primary" />
            <h2 className="text-base font-semibold">2. Choose Billing Scope</h2>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => setScope('all')}
              className={cn('rounded-lg border p-4 text-left', scope === 'all' ? 'border-primary bg-primary/5' : 'border-border bg-white')}
            >
              <p className="text-sm font-semibold">All active accounts</p>
              <p className="mt-1 text-xs text-muted-foreground">{activeAccounts.length} accounts ready for batch processing.</p>
            </button>
            <button
              type="button"
              onClick={() => setScope('single')}
              className={cn('rounded-lg border p-4 text-left', scope === 'single' ? 'border-primary bg-primary/5' : 'border-border bg-white')}
            >
              <p className="text-sm font-semibold">Single account</p>
              <p className="mt-1 text-xs text-muted-foreground">Generate or validate one specific account.</p>
            </button>
          </div>
          {scope === 'single' && (
            <div className="mt-4">
              <div className="relative">
                <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={accountSearch}
                  onChange={(event) => setAccountSearch(event.target.value)}
                  className="h-9 pl-9"
                  placeholder="Search account number or ID"
                />
              </div>
              <div className="mt-2 grid max-h-64 gap-2 overflow-auto">
                {filteredAccounts.map((account: Account) => (
                  <button
                    key={account.id}
                    type="button"
                    onClick={() => setSelectedAccountId(account.id)}
                    className={cn('flex items-center justify-between rounded-md border px-3 py-2 text-left text-sm', selectedAccountId === account.id ? 'border-primary bg-primary/5' : 'border-border bg-white hover:bg-accent/30')}
                  >
                    <span>
                      <span className="font-medium">{account.account_no}</span>
                      <span className="ml-2 text-xs text-muted-foreground">ID {account.id}</span>
                    </span>
                    <StatusBadge status={account.status} />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      <section className="surface-section p-5">
        <div className="mb-4 flex items-center gap-2">
          <FileCheck2 size={16} className="text-primary" />
          <h2 className="text-base font-semibold">3. Validate Billing Data</h2>
        </div>
        <div className="grid gap-2 md:grid-cols-3">
          {validationRows.map((row) => (
            <div key={row.label} className={cn('rounded-md border px-3 py-3', row.ok ? 'border-emerald-200 bg-emerald-50' : 'border-amber-200 bg-amber-50')}>
              <div className="flex items-start gap-2">
                {row.ok ? <CheckCircle2 size={15} className="mt-0.5 text-success" /> : <AlertTriangle size={15} className="mt-0.5 text-amber-700" />}
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{row.label}</p>
                  <p className="mt-1 text-sm font-medium">{row.value}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="surface-section p-5">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-base font-semibold">4. Generate Invoices</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {scope === 'all' ? 'Run batch generation for all active accounts.' : 'Generate the selected account invoice.'}
            </p>
          </div>
          <Button disabled={!validationOk || generateBatchMutation.isPending || generateOneMutation.isPending} onClick={generate}>
            {generateBatchMutation.isPending || generateOneMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            {scope === 'all' ? 'Generate Batch' : 'Generate Invoice'}
          </Button>
        </div>
      </section>

      <section className="surface-section p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold">5. Result Summary</h2>
            <p className="mt-1 text-sm text-muted-foreground">Batch success, failure, and partial status appear here.</p>
          </div>
          <Button variant="outline" size="sm" disabled>
            <RefreshCw size={13} />
            Retry failed accounts
          </Button>
        </div>

        {scope === 'single' && !run.data ? (
          <div className="rounded-md border border-dashed border-border px-3 py-8 text-center text-sm text-muted-foreground">
            Single-account generation opens the invoice after success.
          </div>
        ) : run.isPending && runId ? (
          <CardSkeleton />
        ) : run.error ? (
          <ErrorState detail={errDetail(run.error)} />
        ) : run.data ? (
          <div className="grid gap-4">
            <div className="grid gap-3 md:grid-cols-4">
              <div className="rounded-md border border-border bg-white p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Status</p>
                <div className="mt-2"><StatusBadge status={run.data.status} /></div>
              </div>
              <div className="rounded-md border border-border bg-white p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Total</p>
                <p className="mt-2 text-2xl font-semibold tabular-nums">{run.data.total}</p>
              </div>
              <div className="rounded-md border border-border bg-white p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Success</p>
                <p className="mt-2 text-2xl font-semibold tabular-nums text-success">{run.data.succeeded}</p>
              </div>
              <div className="rounded-md border border-border bg-white p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Failed</p>
                <p className="mt-2 text-2xl font-semibold tabular-nums text-amber-700">{run.data.failed}</p>
              </div>
            </div>
            <FailureTable failures={run.data.failures} />
          </div>
        ) : (
          <div className="rounded-md border border-dashed border-border px-3 py-8 text-center text-sm text-muted-foreground">
            No generation run selected yet.
          </div>
        )}
      </section>
    </div>
  )
}
