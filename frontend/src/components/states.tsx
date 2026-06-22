import { CardSkeleton } from './ui-kit/Skeletons'
import { EmptyState } from './ui-kit/EmptyState'

export function Loading() {
  return <CardSkeleton />
}

export function ErrorState({ detail }: { detail: string }) {
  return (
    <p className="text-destructive py-8 text-center">
      Error: {detail}
    </p>
  )
}

export function Empty({ label }: { label: string }) {
  return <EmptyState title={label} />
}
