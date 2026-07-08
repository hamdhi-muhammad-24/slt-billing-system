import { useQuery } from '@tanstack/react-query'
import { FileText, CheckCircle2, AlertTriangle, Loader2, XCircle } from 'lucide-react'
import { getUploads, type GmfUploadOut } from '../../lib/api'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { DataTable, type ColumnDef } from '../../components/ui-kit/DataTable'

function StatusBadge({ status }: { status: string }) {
  if (status === 'PENDING_APPROVAL') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-cyan-50 px-2 py-0.5 text-xs font-medium text-cyan-700 ring-1 ring-inset ring-cyan-700/10">
        <div className="size-1.5 rounded-full bg-cyan-500" />
        Pending Review
      </span>
    )
  }
  if (status === 'APPROVED') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-700/10">
        <CheckCircle2 size={12} className="text-blue-600" />
        Approved / Waiting
      </span>
    )
  }
  if (status === 'GENERATING') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-600/20">
        <Loader2 size={12} className="animate-spin text-amber-600" />
        Generating
      </span>
    )
  }
  if (status === 'COMPLETED') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
        <CheckCircle2 size={12} className="text-emerald-600" />
        Completed
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/10">
      <XCircle size={12} className="text-red-600" />
      {status}
    </span>
  )
}

export default function GmfMonitor() {
  const { data: uploads, isLoading } = useQuery({
    queryKey: ['billing-uploads'],
    queryFn: () => getUploads(),
    refetchInterval: 5000,
  })

  const COLS: ColumnDef<GmfUploadOut>[] = [
    {
      header: 'Filename',
      cell: (upload) => (
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <FileText size={16} className="text-muted-foreground" />
            <span className="font-medium">{upload.filename}</span>
          </div>
          {upload.error_message && (
             <span className="text-xs text-red-500 mt-1 flex items-center gap-1">
               <AlertTriangle size={10} />
               {upload.error_message}
             </span>
          )}
        </div>
      ),
    },
    {
      header: 'Cycle',
      cell: (upload) => (
        <span className="inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-800">
          {upload.cycle_number ? `Cycle ${upload.cycle_number}` : 'Test GMF'}
        </span>
      ),
    },
    {
      header: 'Detected Template',
      cell: (upload) => (
        <span className="text-sm font-medium">
          {upload.template_detected ? upload.template_detected.replace('_', ' ') : <span className="text-muted-foreground">Unknown</span>}
        </span>
      ),
    },
    {
      header: 'Detected At',
      cell: (upload) => new Date(upload.detected_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }),
    },
    {
      header: 'Status',
      cell: (upload) => <StatusBadge status={upload.status} />,
    }
  ]

  const summary = {
    total: uploads?.length || 0,
    pending: uploads?.filter(u => u.status === 'PENDING_APPROVAL').length || 0,
    completed: uploads?.filter(u => u.status === 'COMPLETED').length || 0,
    failed: uploads?.filter(u => u.status === 'FAILED').length || 0,
  }

  return (
    <div className="space-y-6">
      <PageHeader 
        title="GMF Monitor" 
        description="Monitor detected GMF files and their generation status." 
      />

      <div className="grid grid-cols-4 gap-4 rounded-xl border bg-card p-4 shadow-sm">
        <div className="flex flex-col items-center justify-center border-r">
          <span className="text-2xl font-bold">{summary.total}</span>
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Total Detected</span>
        </div>
        <div className="flex flex-col items-center justify-center border-r">
          <span className="text-2xl font-bold text-cyan-600">{summary.pending}</span>
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Pending Review</span>
        </div>
        <div className="flex flex-col items-center justify-center border-r">
          <span className="text-2xl font-bold text-emerald-600">{summary.completed}</span>
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Completed</span>
        </div>
        <div className="flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-rose-600">{summary.failed}</span>
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Failed</span>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {isLoading ? (
          <div className="h-64 animate-pulse rounded-lg bg-muted" />
        ) : (
          <DataTable
            columns={COLS}
            data={uploads || []}
            keyExtractor={(upload) => upload.id}
            emptyLabel="No GMF uploads detected yet."
          />
        )}
      </div>
    </div>
  )
}
