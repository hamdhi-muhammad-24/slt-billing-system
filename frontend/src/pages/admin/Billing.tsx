import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { generateOne, generateBatch, getBillingRun, ApiError } from '../../lib/api'
import type { Invoice, BillingRun } from '../../types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loading, ErrorState } from '../../components/states'
import { formatLKR } from '../../lib/money'

function errorDetail(err: unknown): string {
  return err instanceof ApiError ? err.detail : String(err)
}

// ── Section 1: Generate one invoice ──────────────────────────────────────────

function GenerateOneCard() {
  const qc = useQueryClient()
  const [accountId, setAccountId] = useState(1)
  const [period, setPeriod] = useState('2024-01')
  const [result, setResult] = useState<Invoice | null>(null)

  const mutation = useMutation({
    mutationFn: () => generateOne({ account_id: accountId, period }),
    onSuccess: (inv) => {
      setResult(inv)
      qc.invalidateQueries({ queryKey: ['invoices', accountId] })
    },
    onError: () => setResult(null),
  })

  return (
    <Card>
      <CardHeader><CardTitle>Generate One Invoice</CardTitle></CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="gen1-account">Account ID</Label>
            <Input
              id="gen1-account"
              type="number"
              min={1}
              value={accountId}
              onChange={(e) => { setAccountId(Number(e.target.value)); setResult(null); mutation.reset() }}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="gen1-period">Period (YYYY-MM)</Label>
            <Input
              id="gen1-period"
              value={period}
              onChange={(e) => { setPeriod(e.target.value); setResult(null); mutation.reset() }}
            />
          </div>
        </div>

        <Button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          className="w-fit"
        >
          {mutation.isPending ? 'Generating…' : 'Generate'}
        </Button>

        {mutation.isSuccess && result && (
          <p className="text-sm text-green-700 dark:text-green-400">
            Invoice created —{' '}
            <Link to={`/admin/invoices/${result.id}`} className="underline font-medium">
              View invoice {result.id} ({result.period}, {formatLKR(result.total_payable)})
            </Link>
          </p>
        )}

        {mutation.isError && (
          <div className="rounded-md bg-muted px-4 py-3 text-sm text-foreground">
            {mutation.error instanceof ApiError && mutation.error.status === 409
              ? <>Invoice for account {accountId} / {period} already exists.</>
              : mutation.error instanceof ApiError && mutation.error.status === 404
              ? <>Account {accountId} not found or has no billing data for {period}.</>
              : errorDetail(mutation.error)}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// ── Section 2: Generate batch ─────────────────────────────────────────────────

interface GenerateBatchCardProps {
  onRunStarted: (run: BillingRun) => void
}

function GenerateBatchCard({ onRunStarted }: GenerateBatchCardProps) {
  const [period, setPeriod] = useState('2024-01')

  const mutation = useMutation({
    mutationFn: () => generateBatch({ period }),
    onSuccess: (run) => onRunStarted(run),
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

        <Button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          className="w-fit"
        >
          {mutation.isPending ? 'Starting…' : 'Run batch'}
        </Button>

        {mutation.isError && (
          <div className="rounded-md bg-muted px-4 py-3 text-sm text-foreground">
            {errorDetail(mutation.error)}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// ── Section 3: Run status ─────────────────────────────────────────────────────

const ACTIVE_STATUSES = new Set(['pending', 'running'])

interface RunStatusCardProps {
  runId: number
}

function RunStatusCard({ runId }: RunStatusCardProps) {
  const { data, isPending, error } = useQuery({
    queryKey: ['billingRun', runId],
    queryFn: () => getBillingRun(runId),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status && ACTIVE_STATUSES.has(status) ? 1500 : false
    },
  })

  if (isPending) return <Loading />
  if (error) return <ErrorState detail={errorDetail(error)} />

  const run = data

  return (
    <Card>
      <CardHeader><CardTitle>Run Status — #{run.id}</CardTitle></CardHeader>
      <CardContent className="flex flex-col gap-4">
        <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
          <dt className="text-muted-foreground">Status</dt>
          <dd className="capitalize font-medium">{run.status}</dd>
          <dt className="text-muted-foreground">Period</dt><dd>{run.period}</dd>
          <dt className="text-muted-foreground">Total</dt><dd>{run.total}</dd>
          <dt className="text-muted-foreground">Succeeded</dt><dd>{run.succeeded}</dd>
          <dt className="text-muted-foreground">Failed</dt><dd>{run.failed}</dd>
          <dt className="text-muted-foreground">Started</dt><dd>{run.started_at ?? '—'}</dd>
          <dt className="text-muted-foreground">Finished</dt><dd>{run.finished_at ?? '—'}</dd>
        </dl>

        {run.failures.length > 0 && (
          <div className="flex flex-col gap-2">
            <p className="text-sm font-medium">
              Per-account outcomes ({run.failures.length} accounts not billed this run):
            </p>
            <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium">Account ID</th>
                    <th className="px-4 py-2 text-left font-medium">Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {run.failures.map((f) => (
                    <tr key={f.id} className="border-t border-foreground/5">
                      <td className="px-4 py-2">{f.account_id}</td>
                      <td className="px-4 py-2 text-muted-foreground">{f.error}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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
      <h1 className="text-2xl font-bold">Billing</h1>
      <GenerateOneCard />
      <GenerateBatchCard onRunStarted={(run) => setRunId(run.id)} />
      {runId !== null && <RunStatusCard runId={runId} />}
    </div>
  )
}
