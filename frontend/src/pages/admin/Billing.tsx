import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { CheckCircle2, Circle, Loader2, AlertTriangle, XCircle } from 'lucide-react'
import { generateOne, generateBatch, getBillingRun, ApiError } from '../../lib/api'
import type { BillingRun, BillingRunFailure } from '../../types'
import type { ColumnDef } from '../../components/ui-kit/DataTable'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { DataTable } from '../../components/ui-kit/DataTable'
import { StatusBadge } from '../../components/ui-kit/StatusBadge'
import { ErrorState } from '../../components/states'
import { CardSkeleton } from '../../components/ui-kit/Skeletons'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

function errDetail(err: unknown): string {
  return err instanceof ApiError ? err.detail : String(err)
}

// ── Step header ───────────────────────────────────────────────────────────────

function StepHeader({ step, title, subtitle }: { step: number; title: string; subtitle: string }) {
  return (
    <div className="flex items-start gap-4">
      <div className="flex size-8 shrink-0 items-center justify-center rounded-full gradient-primary text-white text-sm font-bold shadow-sm">
        {step}
      </div>
      <div>
        <p className="text-base font-semibold">{title}</p>
        <p className="text-sm text-muted-foreground">{subtitle}</p>
      </div>
    </div>
  )
}

// ── Section 1: Generate one ───────────────────────────────────────────────────

function GenerateOneSection() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [accountId, setAccountId] = useState(1)
  const [period, setPeriod] = useState('2024-01')

  const mutation = useMutation({
    mutationFn: () => generateOne({ account_id: accountId, period }),
    onSuccess: (inv) => {
      qc.invalidateQueries({ queryKey: ['invoices', accountId] })
      toast.success(`Invoice ${inv.id} created — ${inv.period}`, {
        action: { label: 'View', onClick: () => navigate(`/admin/invoices/${inv.id}`) },
      })
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 409) {
        toast.info(`Invoice for account ${accountId} / ${period} already exists.`)
      } else if (err instanceof ApiError && err.status === 404) {
        toast.info(`Account ${accountId} not found or has no billing data for ${period}.`)
      } else {
        toast.error(errDetail(err))
      }
    },
  })

  return (
    <div className="flex flex-col gap-5 rounded-xl border border-border bg-card p-5 shadow-sm">
      <StepHeader step={1} title="Generate One Invoice" subtitle="Create a single invoice for a specific account and period." />
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-sm pl-12">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="gen1-account">Account ID</Label>
          <Input
            id="gen1-account"
            type="number"
            min={1}
            value={accountId}
            onChange={(e) => { setAccountId(Number(e.target.value)); mutation.reset() }}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="gen1-period">Period (YYYY-MM)</Label>
          <Input
            id="gen1-period"
            value={period}
            onChange={(e) => { setPeriod(e.target.value); mutation.reset() }}
          />
        </div>
      </div>
      <div className="pl-12">
        <Button onClick={() => mutation.mutate()} disabled={mutation.isPending} className="w-fit">
          {mutation.isPending ? (
            <span className="flex items-center gap-2">
              <Loader2 size={14} className="animate-spin" /> Generating…
            </span>
          ) : 'Generate Invoice'}
        </Button>
      </div>
    </div>
  )
}

// ── Section 2: Generate batch ─────────────────────────────────────────────────

interface BatchSectionProps {
  onRunStarted: (run: BillingRun) => void
}

function GenerateBatchSection({ onRunStarted }: BatchSectionProps) {
  const [period, setPeriod] = useState('2024-01')

  const mutation = useMutation({
    mutationFn: () => generateBatch({ period }),
    onSuccess: (run) => {
      onRunStarted(run)
      toast.success(`Batch run #${run.id} started for ${period}.`)
    },
    onError: (err) => toast.error(errDetail(err)),
  })

  return (
    <div className="flex flex-col gap-5 rounded-xl border border-border bg-card p-5 shadow-sm">
      <StepHeader step={2} title="Run Batch Billing" subtitle="Generate invoices for all active accounts in a period." />
      <div className="flex flex-col gap-1.5 max-w-xs pl-12">
        <Label htmlFor="batch-period">Period (YYYY-MM)</Label>
        <Input
          id="batch-period"
          value={period}
          onChange={(e) => { setPeriod(e.target.value); mutation.reset() }}
        />
      </div>
      <div className="pl-12">
        <Button onClick={() => mutation.mutate()} disabled={mutation.isPending} className="w-fit">
          {mutation.isPending ? (
            <span className="flex items-center gap-2">
              <Loader2 size={14} className="animate-spin" /> Starting…
            </span>
          ) : 'Run Batch'}
        </Button>
      </div>
    </div>
  )
}

// ── Section 3: Run status ─────────────────────────────────────────────────────

const ACTIVE_STATUSES = new Set(['pending', 'running'])

const FAILURE_COLS: ColumnDef<BillingRunFailure>[] = [
  { header: 'Account ID', cell: (f) => f.account_id },
  { header: 'Reason',     cell: (f) => <span className="text-muted-foreground">{f.error}</span> },
]

function runGradient(status: string) {
  if (status === 'completed') return 'gradient-success'
  if (status === 'failed') return 'from-red-600 to-red-500 bg-gradient-to-br'
  if (status === 'running' || status === 'pending') return 'gradient-primary'
  return 'from-amber-500 to-amber-400 bg-gradient-to-br'
}

function RunStatusIcon({ status }: { status: string }) {
  if (status === 'completed') return <CheckCircle2 size={20} className="text-white" />
  if (status === 'failed') return <XCircle size={20} className="text-white" />
  if (status === 'running') return <Loader2 size={20} className="text-white animate-spin" />
  if (status === 'pending') return <Circle size={20} className="text-white/80" />
  return <AlertTriangle size={20} className="text-white" />
}

function RunStatusSection({ runId }: { runId: number }) {
  const { data, isPending, error } = useQuery({
    queryKey: ['billingRun', runId],
    queryFn: () => getBillingRun(runId),
    refetchInterval: (q) => {
      const s = q.state.data?.status
      return s && ACTIVE_STATUSES.has(s) ? 1500 : false
    },
  })

  if (isPending) return <CardSkeleton />
  if (error) return <ErrorState detail={errDetail(error)} />

  const run = data
  const isActive = ACTIVE_STATUSES.has(run.status)

  return (
    <div className="flex flex-col gap-5 rounded-xl border border-border bg-card p-5 shadow-sm">
      <StepHeader step={3} title="Run Status" subtitle="Live results for the most recent batch run." />

      <div className={cn('rounded-xl p-5 shadow-md', runGradient(run.status))}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-white/20">
              <RunStatusIcon status={run.status} />
            </div>
            <div>
              <p className="text-white font-bold text-lg leading-none">Run #{run.id}</p>
              <p className="text-white/70 text-sm mt-0.5">{run.period}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isActive && (
              <span className="size-2 rounded-full bg-white animate-pulse" />
            )}
            <StatusBadge status={run.status} />
          </div>
        </div>

        <div className="mt-5 grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-white/70 text-xs">Total</p>
            <p className="text-white font-bold text-2xl tabular-nums">{run.total}</p>
          </div>
          <div>
            <p className="text-white/70 text-xs">Succeeded</p>
            <p className="text-white font-bold text-2xl tabular-nums">{run.succeeded}</p>
          </div>
          <div>
            <p className="text-white/70 text-xs">Failed</p>
            <p className={cn('font-bold text-2xl tabular-nums', run.failed > 0 ? 'text-white' : 'text-white/50')}>
              {run.failed}
            </p>
          </div>
        </div>
      </div>

      {run.failures.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium text-muted-foreground">
            {run.failures.length} account{run.failures.length !== 1 ? 's' : ''} not billed
            (invoice may already exist for this period):
          </p>
          <DataTable
            columns={FAILURE_COLS}
            data={run.failures}
            keyExtractor={(f) => f.id}
            emptyLabel="No failures."
          />
        </div>
      )}

      <dl className="grid grid-cols-[auto_1fr] gap-x-8 gap-y-1.5 text-sm text-muted-foreground pl-1">
        <dt>Started</dt><dd className="text-foreground">{run.started_at ?? '—'}</dd>
        <dt>Finished</dt><dd className="text-foreground">{run.finished_at ?? '—'}</dd>
      </dl>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function Billing() {
  const [runId, setRunId] = useState<number | null>(null)

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Billing" description="Generate invoices for one account or all active accounts." />
      <GenerateOneSection />
      <GenerateBatchSection onRunStarted={(run) => setRunId(run.id)} />
      {runId !== null && <RunStatusSection runId={runId} />}
    </div>
  )
}
