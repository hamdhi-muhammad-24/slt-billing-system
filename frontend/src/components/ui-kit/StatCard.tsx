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
    card: 'gradient-primary shadow-lg border-0',
    iconWrap: 'bg-white/20 text-white',
    label: 'text-white/75',
    value: 'text-white',
    sub: 'text-white/60',
  },
  green: {
    card: 'gradient-success shadow-lg border-0',
    iconWrap: 'bg-white/20 text-white',
    label: 'text-white/75',
    value: 'text-white',
    sub: 'text-white/60',
  },
  teal: {
    card: 'gradient-teal shadow-lg border-0',
    iconWrap: 'bg-white/20 text-white',
    label: 'text-white/75',
    value: 'text-white',
    sub: 'text-white/60',
  },
  purple: {
    card: 'gradient-purple shadow-lg border-0',
    iconWrap: 'bg-white/20 text-white',
    label: 'text-white/75',
    value: 'text-white',
    sub: 'text-white/60',
  },
  amber: {
    card: 'gradient-amber shadow-lg border-0',
    iconWrap: 'bg-white/20 text-white',
    label: 'text-white/75',
    value: 'text-white',
    sub: 'text-white/60',
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
    <div className={cn('rounded-xl p-5 flex flex-col gap-4', v.card)}>
      <div className="flex items-center justify-between">
        <p className={cn('text-sm font-medium', v.label)}>{label}</p>
        {Icon && (
          <div className={cn('flex size-9 shrink-0 items-center justify-center rounded-lg', v.iconWrap)}>
            <Icon size={17} />
          </div>
        )}
      </div>
      <div>
        <p className={cn('text-3xl font-bold tabular-nums leading-none', v.value)}>{value}</p>
        {sublabel && <p className={cn('text-xs mt-1.5', v.sub)}>{sublabel}</p>}
      </div>
    </div>
  )
}
