import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { generateOne, generateBatch, getBillingRun, ApiError } from '../../lib/api'
import type { BillingRun, BillingRunFailure } from '../../types'
import type { ColumnDef } from '../../components/ui-kit/DataTable'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { DataTable } from '../../components/ui-kit/DataTable'
import { StatusBadge } from '../../components/ui-kit/StatusBadge'
import { ErrorState } from '../../components/states'
import { CardSkeleton } from '../../components/ui-kit/Skeletons'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

function errDetail(err: unknown): string {
  return err instanceof ApiError ? err.detail : String(err)
}

// ── Section 1: Generate one ───────────────────────────────────────────────────

function GenerateOneCard() {
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
    <Card>
      <CardHeader><CardTitle>Generate One Invoice</CardTitle></CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-sm">
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
        <Button onClick={() => mutation.mutate()} disabled={mutation.isPending} className="w-fit">
          {mutation.isPending ? 'Generating…' : 'Generate'}
        </Button>
      </CardContent>
    </Card>
  )
}

// ── Section 2: Generate batch ─────────────────────────────────────────────────

interface BatchCardProps {
  onRunStarted: (run: BillingRun) => void
}

function GenerateBatchCard({ onRunStarted }: BatchCardProps) {
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
    <Card>
      <CardHeader><CardTitle>Generate Batch</CardTitle></CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5 max-w-xs">
          <Label htmlFor="batch-period">Period (YYYY-MM)</Label>
          <Input
            id="batch-period"
            value={period}
            onChange={(e) => { setPeriod(e.target.value); mutation.reset() }}
          />
        </div>
        <Button onClick={() => mutation.mutate()} disabled={mutation.isPending} className="w-fit">
          {mutation.isPending ? 'Starting…' : 'Run batch'}
        </Button>
      </CardContent>
    </Card>
  )
}

// ── Section 3: Run status ─────────────────────────────────────────────────────

const ACTIVE_STATUSES = new Set(['pending', 'running'])

const FAILURE_COLS: ColumnDef<BillingRunFailure>[] = [
  { header: 'Account ID', cell: (f) => f.account_id },
  { header: 'Reason',     cell: (f) => <span className="text-muted-foreground">{f.error}</span> },
]

function RunStatusCard({ runId }: { runId: number }) {
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

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-3">
          Run #{run.id}
          <StatusBadge status={run.status} />
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <dl className="grid grid-cols-[auto_1fr] gap-x-8 gap-y-2 text-sm">
          <dt className="text-muted-foreground">Period</dt><dd>{run.period}</dd>
          <dt className="text-muted-foreground">Total</dt><dd>{run.total}</dd>
          <dt className="text-muted-foreground">Succeeded</dt>
          <dd className="text-success font-medium">{run.succeeded}</dd>
          <dt className="text-muted-foreground">Failed</dt>
          <dd className={run.failed > 0 ? 'text-muted-foreground' : ''}>{run.failed}</dd>
          <dt className="text-muted-foreground">Started</dt><dd>{run.started_at ?? '—'}</dd>
          <dt className="text-muted-foreground">Finished</dt><dd>{run.finished_at ?? '—'}</dd>
        </dl>

        {run.failures.length > 0 && (
          <div className="flex flex-col gap-2">
            <p className="text-sm font-medium text-muted-foreground">
              {run.failures.length} account{run.failures.length !== 1 ? 's' : ''} not billed this run
              (e.g. invoice already exists for this period):
            </p>
            <DataTable
              columns={FAILURE_COLS}
              data={run.failures}
              keyExtractor={(f) => f.id}
              emptyLabel="No failures."
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function Billing() {
  const [runId, setRunId] = useState<number | null>(null)

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Billing" description="Generate invoices for one account or all active accounts." />
      <GenerateOneCard />
      <GenerateBatchCard onRunStarted={(run) => setRunId(run.id)} />
      {runId !== null && <RunStatusCard runId={runId} />}
    </div>
  )
}
