import { Skeleton } from '@/components/ui/skeleton'

export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="rounded-lg ring-1 ring-foreground/10 overflow-hidden">
      <div className="bg-muted/50 px-4 py-3 flex gap-8">
        {Array.from({ length: cols }, (_, i) => (
          <Skeleton key={i} className="h-4 w-20" />
        ))}
      </div>
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="border-t border-foreground/5 px-4 py-3 flex gap-8">
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
    <div className="rounded-xl ring-1 ring-foreground/10 p-6 flex flex-col gap-4">
      <Skeleton className="h-5 w-36" />
      <div className="grid grid-cols-2 gap-3">
        {Array.from({ length: 6 }, (_, i) => (
          <Skeleton key={i} className="h-4" />
        ))}
      </div>
    </div>
  )
}
