import { cn } from '@/lib/utils'

type StatusConfig = {
  label: string
  className: string
  dot?: string
}

const STATUS_CONFIG: Record<string, StatusConfig> = {
  active:    { label: 'Active',     className: 'bg-success/10 text-success border border-success/25',          dot: 'bg-success' },
  done:      { label: 'Done',       className: 'bg-success/10 text-success border border-success/25',          dot: 'bg-success' },
  paid:      { label: 'Paid',       className: 'bg-success/10 text-success border border-success/25',          dot: 'bg-success' },
  completed: { label: 'Completed',  className: 'bg-success/10 text-success border border-success/25',          dot: 'bg-success' },
  pending:   { label: 'Pending',    className: 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-800', dot: 'bg-amber-500' },
  due:       { label: 'Due',        className: 'bg-primary/10 text-primary border border-primary/25',          dot: 'bg-primary' },
  generated: { label: 'Generated',  className: 'bg-muted text-muted-foreground border border-border',          dot: 'bg-muted-foreground' },
  partial:   { label: 'Partial',    className: 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-800', dot: 'bg-amber-500' },
  running:   { label: 'Running',    className: 'bg-primary/10 text-primary border border-primary/25',          dot: 'bg-primary animate-pulse' },
  suspended: { label: 'Suspended',  className: 'bg-orange-50 text-orange-700 border border-orange-200 dark:bg-orange-950/30 dark:text-orange-400 dark:border-orange-800', dot: 'bg-orange-500' },
  failed:    { label: 'Failed',     className: 'bg-destructive/10 text-destructive border border-destructive/25', dot: 'bg-destructive' },
  overdue:   { label: 'Overdue',    className: 'bg-destructive/10 text-destructive border border-destructive/25', dot: 'bg-destructive' },
  closed:    { label: 'Closed',     className: 'bg-muted text-muted-foreground border border-border',          dot: 'bg-muted-foreground' },
  tax:       { label: 'Tax',        className: 'bg-teal-50 text-teal-700 border border-teal-200 dark:bg-teal-950/30 dark:text-teal-400 dark:border-teal-800', dot: 'bg-teal-500' },
}

interface Props {
  status: string
}

export function StatusBadge({ status }: Props) {
  const config = STATUS_CONFIG[status.toLowerCase()]

  if (!config) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium bg-muted text-muted-foreground border border-border capitalize">
        {status}
      </span>
    )
  }

  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium', config.className)}>
      {config.dot && <span className={cn('size-1.5 rounded-full shrink-0', config.dot)} />}
      {config.label}
    </span>
  )
}
