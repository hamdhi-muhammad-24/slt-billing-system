import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  Circle,
  FileCheck2,
  Loader2,
  RefreshCw,
  Search,
  Send,
} from 'lucide-react'
import type { Account, BillingRun, BillingRunApproval, BillingRunFailure, BillingRunItem, BillingScheduleMode } from '../../types'
import type { ColumnDef } from '../../components/ui-kit/DataTable'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { DataTable } from '../../components/ui-kit/DataTable'
import { StatusBadge } from '../../components/ui-kit/StatusBadge'
import { ErrorState } from '../../components/states'
import { CardSkeleton } from '../../components/ui-kit/Skeletons'
import { useCustomers } from '../../hooks/useCustomers'
import {
  ApiError,
  approveBillingRun,
  generateBatch,
  generateOne,
  getBillingRun,
  getBillingSchedule,
  listBillingApprovals,
  listBillingRuns,
  listCustomerAccounts,
  listInvoiceTemplates,
  rejectBillingRun,
  retryBillingRunItem,
  sendBillingRun,
  updateBillingSchedule,
} from '../../lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

type ScopeMode = 'all' | 'single'
type ScheduleForm = {
  name: string
  day_of_month: number
  run_time: string
  timezone: string
  schedule_mode: BillingScheduleMode
  is_active: boolean
  send_email: boolean
  send_sms: boolean
  approval_lead_days: number
  approval_email: string
}

function errDetail(err: unknown): string {
  return err instanceof ApiError ? err.detail : String(err)
}

function currentPeriod(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

function statusSummaryText(summary?: Record<string, number>): string {
  const entries = Object.entries(summary ?? {})
  return entries.length ? entries.map(([key, value]) => `${key}: ${value}`).join(' | ') : 'No status rows'
}

function runItemReasons(item: BillingRunItem): string {
  return [
    item.failure_reason,
    item.email_failure_reason ? `Email: ${item.email_failure_reason}` : null,
    item.sms_failure_reason ? `SMS: ${item.sms_failure_reason}` : null,
  ].filter(Boolean).join(' | ') || '-'
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

function RunItemTable({
  items,
  onOpenInvoice,
  onRetryItem,
  retryingItemId,
}: {
  items: BillingRunItem[]
  onOpenInvoice: (invoiceId: number) => void
  onRetryItem: (itemId: number) => void
  retryingItemId: number | null
}) {
  const cols: ColumnDef<BillingRunItem>[] = [
    { header: 'Account', cell: (item) => <span className="font-medium">{item.account_number ?? `#${item.account_id ?? '-'}`}</span> },
    { header: 'Customer', cell: (item) => item.customer_name ?? 'Unknown' },
    { header: 'Phone', cell: (item) => item.phone ?? '-' },
    { header: 'Contact email', cell: (item) => item.email ?? '-' },
    { header: 'PDF', cell: (item) => <StatusBadge status={item.pdf_status} /> },
    { header: 'Email status', cell: (item) => <StatusBadge status={item.email_status} /> },
    { header: 'SMS', cell: (item) => <StatusBadge status={item.sms_status} /> },
    { header: 'Overall', cell: (item) => <StatusBadge status={item.overall_status} /> },
    {
      header: 'Invoice',
      cell: (item) => item.invoice_id ? (
        <Button variant="outline" size="sm" onClick={(event) => { event.stopPropagation(); onOpenInvoice(item.invoice_id!) }}>
          Open
        </Button>
      ) : '-',
    },
    { header: 'Failure reason', cell: (item) => <span className="text-muted-foreground">{runItemReasons(item)}</span> },
    {
      header: 'Retry',
      cell: (item) => (
        <Button
          variant="outline"
          size="sm"
          disabled={retryingItemId === item.id}
          onClick={(event) => {
            event.stopPropagation()
            onRetryItem(item.id)
          }}
        >
          {retryingItemId === item.id ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
          Retry
        </Button>
      ),
    },
  ]
  return <DataTable columns={cols} data={items} keyExtractor={(item) => item.id} emptyLabel="No processed accounts for this run." />
}

export default function Billing() {
  const [period, setPeriod] = useState(currentPeriod())
  const [scope, setScope] = useState<ScopeMode>('all')
  const [accountSearch, setAccountSearch] = useState('')
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null)
  const [runId, setRunId] = useState<number | null>(null)
  const [retryingItemId, setRetryingItemId] = useState<number | null>(null)
  const [scheduleForm, setScheduleForm] = useState<ScheduleForm>({
    name: 'Monthly SLT billing',
    day_of_month: 1,
    run_time: '02:00',
    timezone: 'Asia/Colombo',
    schedule_mode: 'AUTOMATIC',
    is_active: true,
    send_email: true,
    send_sms: true,
    approval_lead_days: 1,
    approval_email: '',
  })
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

  const schedule = useQuery({
    queryKey: ['billingSchedule'],
    queryFn: getBillingSchedule,
  })
  const approvals = useQuery({
    queryKey: ['billingApprovals'],
    queryFn: listBillingApprovals,
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
  const templates = useQuery({
    queryKey: ['invoice-templates', 'billing'],
    queryFn: listInvoiceTemplates,
  })
  const recentRuns = useQuery({
    queryKey: ['billingRuns', 'recent'],
    queryFn: () => listBillingRuns({ limit: 8, offset: 0 }),
  })

  useEffect(() => {
    if (!schedule.data) return
    setScheduleForm({
      name: schedule.data.name,
      day_of_month: schedule.data.day_of_month,
      run_time: schedule.data.run_time,
      timezone: schedule.data.timezone,
      schedule_mode: schedule.data.schedule_mode,
      is_active: schedule.data.is_active,
      send_email: schedule.data.send_email,
      send_sms: schedule.data.send_sms,
      approval_lead_days: schedule.data.approval_lead_days,
      approval_email: schedule.data.approval_email ?? '',
    })
  }, [schedule.data])

  const allAccounts = useMemo(
    () => accountQueries.flatMap((query) => query.data ?? []),
    [accountQueries],
  )
  const selectedAccount = allAccounts.find((account) => account.id === selectedAccountId) ?? null
  const activeAccounts = allAccounts.filter((account) => account.status === 'ACTIVE')
  const activeTemplate = templates.data?.find((template) => template.is_active) ?? null
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
      qc.invalidateQueries({ queryKey: ['billingRuns'] })
      toast.success(`Billing run #${billingRun.id} completed.`)
    },
    onError: (err) => toast.error(errDetail(err)),
  })

  const updateScheduleMutation = useMutation({
    mutationFn: () => updateBillingSchedule({
      ...scheduleForm,
      approval_email: scheduleForm.approval_email.trim() || null,
    }),
    onSuccess: (updated) => {
      qc.setQueryData(['billingSchedule'], updated)
      toast.success('Billing schedule saved.')
    },
    onError: (err) => toast.error(errDetail(err)),
  })

  const approveMutation = useMutation({
    mutationFn: (approvalId: number) => approveBillingRun(approvalId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['billingApprovals'] })
      toast.success('Billing run approved.')
    },
    onError: (err) => toast.error(errDetail(err)),
  })

  const rejectMutation = useMutation({
    mutationFn: (approvalId: number) => rejectBillingRun(approvalId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['billingApprovals'] })
      toast.success('Billing run rejected.')
    },
    onError: (err) => toast.error(errDetail(err)),
  })

  const sendRunMutation = useMutation({
    mutationFn: () => sendBillingRun(runId!, {
      send_email: scheduleForm.send_email,
      send_sms: scheduleForm.send_sms,
    }),
    onSuccess: (updatedRun) => {
      qc.setQueryData(['billingRun', updatedRun.id], updatedRun)
      qc.invalidateQueries({ queryKey: ['billingRuns'] })
      qc.invalidateQueries({ queryKey: ['admin-dashboard-summary'] })
      toast.success('Delivery attempt completed.')
    },
    onError: (err) => toast.error(errDetail(err)),
  })

  const retryItemMutation = useMutation({
    mutationFn: (itemId: number) => {
      setRetryingItemId(itemId)
      return retryBillingRunItem(itemId, {
        send_notifications: true,
        send_email: scheduleForm.send_email,
        send_sms: scheduleForm.send_sms,
      })
    },
    onSuccess: (updatedRun) => {
      setRunId(updatedRun.id)
      qc.setQueryData(['billingRun', updatedRun.id], updatedRun)
      qc.invalidateQueries({ queryKey: ['billingRuns'] })
      toast.success('Account retry completed.')
    },
    onError: (err) => toast.error(errDetail(err)),
    onSettled: () => setRetryingItemId(null),
  })

  if (customers.isPending || templates.isPending || schedule.isPending || approvals.isPending || accountQueries.some((query) => query.isPending)) {
    return (
      <div className="flex flex-col gap-6">
        <PageHeader title="Billing Workflow" />
        <CardSkeleton />
        <CardSkeleton />
      </div>
    )
  }
  const loadError = customers.error ?? templates.error ?? schedule.error ?? approvals.error ?? accountQueries.find((query) => query.error)?.error
  if (loadError) return <ErrorState detail={loadError instanceof ApiError ? loadError.detail : loadError.message} />

  const canValidate = scope === 'all' || selectedAccountId !== null
  const validationRows = [
    { label: 'Billing month', value: period, ok: /^\d{4}-(0[1-9]|1[0-2])$/.test(period) },
    { label: 'Billing scope', value: scope === 'all' ? `${activeAccounts.length} active accounts` : selectedAccount ? selectedAccount.account_no : 'No account selected', ok: canValidate },
    { label: 'Invoice template', value: activeTemplate ? activeTemplate.name : 'No active template selected', ok: scope === 'single' || Boolean(activeTemplate) },
    { label: 'Data readiness', value: allAccounts.length > 0 ? 'Accounts loaded' : 'No accounts found', ok: allAccounts.length > 0 },
  ]
  const validationOk = validationRows.every((row) => row.ok)
  const activeStep = run.data ? 5 : generateBatchMutation.isPending || generateOneMutation.isPending ? 4 : validationOk ? 3 : scope === 'single' ? 2 : 1
  const recentApprovals = approvals.data ?? []
  const pendingApprovals = recentApprovals.filter((approval) => approval.status === 'PENDING')
  const canConfirmSend = Boolean(
    run.data?.items?.some((item) => item.pdf_status === 'SUCCESS')
      && (scheduleForm.send_email || scheduleForm.send_sms),
  )

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

      <section className="surface-section p-5">
        <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="flex items-start gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
              <CalendarClock size={18} />
            </div>
            <div>
              <h2 className="text-base font-semibold">Monthly Billing Schedule</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                The scheduler checks this configuration every 15 minutes and runs the previous month once the selected day and time arrive.
              </p>
              {schedule.data?.last_triggered_period && (
                <p className="mt-1 text-xs text-muted-foreground">Last triggered period: {schedule.data.last_triggered_period}</p>
              )}
            </div>
          </div>
          <Button
            onClick={() => updateScheduleMutation.mutate()}
            disabled={updateScheduleMutation.isPending}
          >
            {updateScheduleMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle2 size={14} />}
            Save Schedule
          </Button>
        </div>

        <div className="grid gap-3 lg:grid-cols-[1.3fr_0.9fr]">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <div>
              <Label htmlFor="schedule-day">Day of month</Label>
              <Input
                id="schedule-day"
                type="number"
                min={1}
                max={28}
                value={scheduleForm.day_of_month}
                onChange={(event) => setScheduleForm((form) => ({ ...form, day_of_month: Number(event.target.value) }))}
                className="mt-2"
              />
            </div>
            <div>
              <Label htmlFor="schedule-time">Run time</Label>
              <Input
                id="schedule-time"
                type="time"
                value={scheduleForm.run_time}
                onChange={(event) => setScheduleForm((form) => ({ ...form, run_time: event.target.value }))}
                className="mt-2"
              />
            </div>
            <div>
              <Label htmlFor="schedule-zone">Timezone</Label>
              <Input
                id="schedule-zone"
                value={scheduleForm.timezone}
                onChange={(event) => setScheduleForm((form) => ({ ...form, timezone: event.target.value }))}
                className="mt-2"
              />
            </div>
            <div>
              <Label htmlFor="schedule-mode">Mode</Label>
              <select
                id="schedule-mode"
                value={scheduleForm.schedule_mode}
                onChange={(event) => setScheduleForm((form) => ({ ...form, schedule_mode: event.target.value as BillingScheduleMode }))}
                className="mt-2 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="AUTOMATIC">Automatic</option>
                <option value="APPROVAL_REQUIRED">Approval required</option>
              </select>
            </div>
            <div>
              <Label htmlFor="approval-email">Approval email</Label>
              <Input
                id="approval-email"
                type="email"
                value={scheduleForm.approval_email}
                onChange={(event) => setScheduleForm((form) => ({ ...form, approval_email: event.target.value }))}
                placeholder="admin@slt.lk"
                className="mt-2"
              />
            </div>
            <div>
              <Label htmlFor="approval-lead">Approval lead days</Label>
              <Input
                id="approval-lead"
                type="number"
                min={1}
                max={7}
                value={scheduleForm.approval_lead_days}
                onChange={(event) => setScheduleForm((form) => ({ ...form, approval_lead_days: Number(event.target.value) }))}
                className="mt-2"
              />
            </div>
            <label className="flex min-h-10 items-center gap-2 rounded-md border border-border bg-white px-3 py-2 text-sm">
              <input
                type="checkbox"
                checked={scheduleForm.is_active}
                onChange={(event) => setScheduleForm((form) => ({ ...form, is_active: event.target.checked }))}
              />
              Schedule active
            </label>
            <label className="flex min-h-10 items-center gap-2 rounded-md border border-border bg-white px-3 py-2 text-sm">
              <input
                type="checkbox"
                checked={scheduleForm.send_email}
                onChange={(event) => setScheduleForm((form) => ({ ...form, send_email: event.target.checked }))}
              />
              Send email
            </label>
            <label className="flex min-h-10 items-center gap-2 rounded-md border border-border bg-white px-3 py-2 text-sm">
              <input
                type="checkbox"
                checked={scheduleForm.send_sms}
                onChange={(event) => setScheduleForm((form) => ({ ...form, send_sms: event.target.checked }))}
              />
              Send SMS
            </label>
          </div>

          <div className="rounded-md border border-border bg-white p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Approvals</p>
                <p className="text-sm font-medium">{pendingApprovals.length} pending request{pendingApprovals.length === 1 ? '' : 's'}</p>
              </div>
              <Button variant="outline" size="sm" onClick={() => approvals.refetch()} disabled={approvals.isFetching}>
                <RefreshCw size={13} className={approvals.isFetching ? 'animate-spin' : ''} />
                Refresh
              </Button>
            </div>
            <div className="grid max-h-56 gap-2 overflow-auto">
              {recentApprovals.length === 0 ? (
                <p className="rounded-md border border-dashed border-border px-3 py-6 text-center text-sm text-muted-foreground">No approval requests yet.</p>
              ) : recentApprovals.slice(0, 5).map((approval: BillingRunApproval) => (
                <div key={approval.id} className="rounded-md border border-border p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold">Period {approval.period}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        Requested {new Date(approval.requested_at).toLocaleString()}
                      </p>
                    </div>
                    <StatusBadge status={approval.status} />
                  </div>
                  {approval.status === 'PENDING' && (
                    <div className="mt-3 flex gap-2">
                      <Button size="sm" onClick={() => approveMutation.mutate(approval.id)} disabled={approveMutation.isPending}>
                        <CheckCircle2 size={13} />
                        Approve
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          if (window.confirm(`Reject billing run approval for ${approval.period}?`)) {
                            rejectMutation.mutate(approval.id)
                          }
                        }}
                        disabled={rejectMutation.isPending}
                      >
                        Reject
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

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
        <div className="grid gap-2 md:grid-cols-4">
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
            {scope === 'all' && (
              <p className="mt-1 text-xs text-muted-foreground">
                Active template: {activeTemplate ? `${activeTemplate.name} (${activeTemplate.template_code})` : 'not selected'}
              </p>
            )}
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
            <p className="mt-1 text-sm text-muted-foreground">Review generated invoices, delivery readiness, and failed accounts before sending.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {run.data && (
              <Button
                size="sm"
                onClick={() => sendRunMutation.mutate()}
                disabled={!canConfirmSend || sendRunMutation.isPending}
              >
                {sendRunMutation.isPending ? <Loader2 size={13} className="animate-spin" /> : <Send size={13} />}
                Confirm Send
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={() => run.refetch()} disabled={!runId || run.isFetching}>
              <RefreshCw size={13} className={run.isFetching ? 'animate-spin' : ''} />
              Refresh
            </Button>
          </div>
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
            <div className="grid gap-3 md:grid-cols-5">
              <div className="rounded-md border border-border bg-white p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Status</p>
                <div className="mt-2"><StatusBadge status={run.data.status} /></div>
              </div>
              <div className="rounded-md border border-border bg-white p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Template</p>
                <p className="mt-2 truncate text-sm font-semibold">{run.data.template_name ?? 'Default'}</p>
              </div>
              <div className="rounded-md border border-border bg-white p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Total</p>
                <p className="mt-2 text-2xl font-semibold tabular-nums">{run.data.total}</p>
              </div>
              <div className="rounded-md border border-border bg-white p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">PDF success</p>
                <p className="mt-2 text-2xl font-semibold tabular-nums text-success">{run.data.pdf_success_count || run.data.succeeded}</p>
              </div>
              <div className="rounded-md border border-border bg-white p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">PDF failed</p>
                <p className="mt-2 text-2xl font-semibold tabular-nums text-amber-700">{run.data.pdf_failed_count || run.data.failed}</p>
              </div>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-md border border-border bg-white p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Email status</p>
                <p className="mt-2 text-sm font-medium">{statusSummaryText(run.data.email_status_summary)}</p>
              </div>
              <div className="rounded-md border border-border bg-white p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">SMS status</p>
                <p className="mt-2 text-sm font-medium">{statusSummaryText(run.data.sms_status_summary)}</p>
              </div>
            </div>
            <RunItemTable
              items={run.data.items ?? []}
              onOpenInvoice={(invoiceId) => navigate(`/admin/invoices/${invoiceId}`)}
              onRetryItem={(itemId) => retryItemMutation.mutate(itemId)}
              retryingItemId={retryingItemId}
            />
            {(run.data.failures ?? []).length > 0 && <FailureTable failures={run.data.failures ?? []} />}
          </div>
        ) : (
          <div className="rounded-md border border-dashed border-border px-3 py-8 text-center text-sm text-muted-foreground">
            No generation run selected yet.
          </div>
        )}
      </section>

      <section className="flex flex-col gap-3">
        <div className="flex items-end justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">History</p>
            <h2 className="text-base font-semibold">Recent Billing Runs</h2>
          </div>
          <Button variant="outline" size="sm" onClick={() => recentRuns.refetch()} disabled={recentRuns.isFetching}>
            <RefreshCw size={13} className={recentRuns.isFetching ? 'animate-spin' : ''} />
            Refresh
          </Button>
        </div>
        {recentRuns.error ? (
          <ErrorState detail={errDetail(recentRuns.error)} />
        ) : (
          <DataTable
            columns={[
              { header: 'Run', cell: (item: BillingRun) => <span className="font-medium">#{item.id}</span> },
              { header: 'Period', cell: (item: BillingRun) => item.period },
              { header: 'Template', cell: (item: BillingRun) => item.template_name ?? 'Default' },
              { header: 'Status', cell: (item: BillingRun) => <StatusBadge status={item.status} /> },
              { header: 'Total', numeric: true, cell: (item: BillingRun) => item.total },
              { header: 'PDF ok', numeric: true, cell: (item: BillingRun) => item.pdf_success_count || item.succeeded },
              { header: 'PDF failed', numeric: true, cell: (item: BillingRun) => item.pdf_failed_count || item.failed },
              { header: 'Email', cell: (item: BillingRun) => statusSummaryText(item.email_status_summary) },
              { header: 'SMS', cell: (item: BillingRun) => statusSummaryText(item.sms_status_summary) },
            ]}
            data={recentRuns.data?.items ?? []}
            keyExtractor={(item) => item.id}
            emptyLabel={recentRuns.isPending ? 'Loading billing runs...' : 'No billing runs yet.'}
            onRowClick={(item) => setRunId(item.id)}
          />
        )}
      </section>
    </div>
  )
}
