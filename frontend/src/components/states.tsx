export function Loading() {
  return <p className="text-muted-foreground py-8 text-center">Loading…</p>
}

export function ErrorState({ detail }: { detail: string }) {
  return (
    <p className="text-destructive py-8 text-center">
      Error: {detail}
    </p>
  )
}

export function Empty({ label }: { label: string }) {
  return <p className="text-muted-foreground py-8 text-center">{label}</p>
}
