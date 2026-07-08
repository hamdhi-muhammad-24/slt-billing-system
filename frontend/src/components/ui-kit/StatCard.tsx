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
  label?: string
  title?: string
  value: string | number
  icon?: LucideIcon | React.ReactNode
  sublabel?: string
  description?: string
  variant?: Variant
  className?: string
}

export function StatCard({ label, title, value, icon, sublabel, description, variant = 'default', className }: Props) {
  const v = VARIANTS[variant]
  const displayLabel = title || label
  const displaySub = description || sublabel
  const isLucide = typeof icon === 'function' || (icon && typeof icon === 'object' && '$$typeof' in (icon as any))

  return (
    <div className={cn('flex min-h-[124px] flex-col justify-between rounded-lg p-5', v.card, className)}>
      <div className="flex items-center justify-between">
        <p className={cn('text-xs font-semibold uppercase tracking-wide', v.label)}>{displayLabel}</p>
        {icon && (
          <div className={cn('flex size-9 shrink-0 items-center justify-center rounded-md', v.iconWrap)}>
            {typeof icon === 'function' || (icon && typeof icon === 'object' && 'render' in (icon as any)) ? (
              // @ts-ignore
              <icon.render size={18} />
            ) : isLucide ? (
              // @ts-ignore
              <icon size={18} />
            ) : (
              icon
            )}
          </div>
        )}
      </div>
      <div>
        <p className={cn('text-3xl font-semibold tabular-nums leading-none', v.value)}>{value}</p>
        {displaySub && <p className={cn('mt-2 text-xs leading-5', v.sub)}>{displaySub}</p>}
      </div>
    </div>
  )
}
