import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

type Variant = 'default' | 'blue' | 'green' | 'teal' | 'purple' | 'amber'

const VARIANTS: Record<Variant, { card: string; iconWrap: string; label: string; value: string; sub: string }> = {
  default: {
    card: 'bg-card border border-border shadow-sm',
    iconWrap: 'bg-primary/10 text-primary',
    label: 'text-muted-foreground',
    value: 'text-foreground',
    sub: 'text-muted-foreground',
  },
  blue: {
    card: 'bg-card border border-blue-100 shadow-sm',
    iconWrap: 'bg-primary/10 text-primary',
    label: 'text-muted-foreground',
    value: 'text-primary',
    sub: 'text-muted-foreground',
  },
  green: {
    card: 'bg-card border border-emerald-100 shadow-sm',
    iconWrap: 'bg-success/10 text-success',
    label: 'text-muted-foreground',
    value: 'text-success',
    sub: 'text-muted-foreground',
  },
  teal: {
    card: 'bg-card border border-cyan-100 shadow-sm',
    iconWrap: 'bg-cyan-500/10 text-cyan-700',
    label: 'text-muted-foreground',
    value: 'text-cyan-700',
    sub: 'text-muted-foreground',
  },
  purple: {
    card: 'bg-card border border-violet-100 shadow-sm',
    iconWrap: 'bg-violet-500/10 text-violet-700',
    label: 'text-muted-foreground',
    value: 'text-violet-700',
    sub: 'text-muted-foreground',
  },
  amber: {
    card: 'bg-card border border-amber-100 shadow-sm',
    iconWrap: 'bg-amber-500/10 text-amber-700',
    label: 'text-muted-foreground',
    value: 'text-amber-700',
    sub: 'text-muted-foreground',
  },
}

interface Props {
  label: string
  value: string | number
  icon?: LucideIcon
  sublabel?: string
  variant?: Variant
}

export function StatCard({ label, value, icon: Icon, sublabel, variant = 'default' }: Props) {
  const v = VARIANTS[variant]

  return (
    <div className={cn('flex min-h-[124px] flex-col justify-between rounded-lg p-5', v.card)}>
      <div className="flex items-center justify-between">
        <p className={cn('text-xs font-semibold uppercase tracking-wide', v.label)}>{label}</p>
        {Icon && (
          <div className={cn('flex size-9 shrink-0 items-center justify-center rounded-md', v.iconWrap)}>
            <Icon size={18} />
          </div>
        )}
      </div>
      <div>
        <p className={cn('text-3xl font-semibold tabular-nums leading-none', v.value)}>{value}</p>
        {sublabel && <p className={cn('mt-2 text-xs leading-5', v.sub)}>{sublabel}</p>}
      </div>
    </div>
  )
}
