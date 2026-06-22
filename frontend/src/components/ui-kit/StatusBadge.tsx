import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  // positive — SLTMobitel green (#50B848 ≈ oklch 0.67 0.10 131)
  active: { label: 'Active',    className: 'bg-success/10 text-success border-success/25 hover:bg-success/10' },
  done:   { label: 'Done',      className: 'bg-success/10 text-success border-success/25 hover:bg-success/10' },
  paid:   { label: 'Paid',      className: 'bg-success/10 text-success border-success/25 hover:bg-success/10' },
  // in-progress — primary blue
  pending: { label: 'Pending',  className: 'bg-primary/10 text-primary border-primary/25 hover:bg-primary/10' },
  running: { label: 'Running',  className: 'bg-primary/10 text-primary border-primary/25 hover:bg-primary/10' },
  // warn / error
  suspended: { label: 'Suspended', className: 'bg-amber-100 text-amber-800 border-amber-200 hover:bg-amber-100' },
  failed:    { label: 'Failed',    className: 'bg-red-100  text-red-800  border-red-200  hover:bg-red-100'  },
  // neutral
  closed:    { label: 'Closed',    className: 'bg-muted    text-muted-foreground border-border hover:bg-muted' },
  // line item label
  tax:       { label: 'Tax',       className: 'bg-success/10 text-success border-success/25 hover:bg-success/10' },
}

interface Props {
  status: string
}

export function StatusBadge({ status }: Props) {
  const config = STATUS_CONFIG[status.toLowerCase()]
  if (!config) {
    return <Badge variant="outline" className="capitalize">{status}</Badge>
  }
  return (
    <Badge variant="outline" className={cn(config.className)}>
      {config.label}
    </Badge>
  )
}
