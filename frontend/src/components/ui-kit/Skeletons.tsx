import { Skeleton } from '@/components/ui/skeleton'

export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
      <div className="flex gap-8 bg-muted/55 px-4 py-3">
        {Array.from({ length: cols }, (_, i) => (
          <Skeleton key={i} className="h-4 w-20" />
        ))}
      </div>
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex gap-8 border-t border-border/70 px-4 py-3">
          {Array.from({ length: cols }, (_, j) => (
            <Skeleton key={j} className="h-4 w-28" />
          ))}
        </div>
      ))}
    </div>
  )
}

export function CardSkeleton() {
  return (
    <div className="flex flex-col gap-4 rounded-lg border border-border bg-card p-6 shadow-sm">
      <Skeleton className="h-5 w-36" />
      <div className="grid grid-cols-2 gap-3">
        {Array.from({ length: 6 }, (_, i) => (
          <Skeleton key={i} className="h-4" />
        ))}
      </div>
    </div>
  )
}
