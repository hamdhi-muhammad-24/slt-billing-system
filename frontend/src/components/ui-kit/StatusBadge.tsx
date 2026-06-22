import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  active:    { label: 'Active',    className: 'bg-green-100 text-green-800 border-green-200 hover:bg-green-100' },
  done:      { label: 'Done',      className: 'bg-green-100 text-green-800 border-green-200 hover:bg-green-100' },
  pending:   { label: 'Pending',   className: 'bg-blue-100 text-blue-800 border-blue-200 hover:bg-blue-100' },
  running:   { label: 'Running',   className: 'bg-blue-100 text-blue-800 border-blue-200 hover:bg-blue-100' },
  suspended: { label: 'Suspended', className: 'bg-amber-100 text-amber-800 border-amber-200 hover:bg-amber-100' },
  failed:    { label: 'Failed',    className: 'bg-red-100 text-red-800 border-red-200 hover:bg-red-100' },
  closed:    { label: 'Closed',    className: 'bg-gray-100 text-gray-600 border-gray-200 hover:bg-gray-100' },
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
