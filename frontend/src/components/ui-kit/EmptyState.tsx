import type { LucideIcon } from 'lucide-react'
import { Inbox } from 'lucide-react'

interface Props {
  icon?: LucideIcon
  title: string
  hint?: string
}

export function EmptyState({ icon: Icon = Inbox, title, hint }: Props) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-border bg-muted/25 px-6 py-10 text-center text-muted-foreground">
      <div className="flex size-10 items-center justify-center rounded-md bg-background text-primary shadow-sm ring-1 ring-border">
        <Icon size={20} strokeWidth={1.8} />
      </div>
      <p className="font-medium text-foreground">{title}</p>
      {hint && <p className="max-w-md text-sm leading-6">{hint}</p>}
    </div>
  )
}
