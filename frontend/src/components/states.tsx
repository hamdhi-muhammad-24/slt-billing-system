import { CardSkeleton } from './ui-kit/Skeletons'
import { EmptyState } from './ui-kit/EmptyState'
import { AlertTriangle } from 'lucide-react'

export function Loading() {
  return <CardSkeleton />
}

export function ErrorState({ detail }: { detail: string }) {
  return (
    <div className="surface-section mx-auto flex max-w-2xl items-start gap-3 p-5">
      <div className="flex size-10 shrink-0 items-center justify-center rounded-md bg-destructive/10 text-destructive">
        <AlertTriangle size={18} />
      </div>
      <div>
        <p className="font-semibold text-foreground">Something went wrong</p>
        <p className="mt-1 text-sm leading-6 text-muted-foreground">{detail}</p>
      </div>
    </div>
  )
}

export function Empty({ label }: { label: string }) {
  return <EmptyState title={label} />
}
