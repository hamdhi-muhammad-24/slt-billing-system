import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileText, Play, CheckCircle2, Zap, Loader2, XCircle, AlertTriangle, Download, Eye } from 'lucide-react'
import { getPendingBatches, getRuns, generateGroupBatch, retryFailedRun, getRunResults, fetchPdfBlobUrl, type BillingRunOut, type PendingBatchOut, type RunResultsOut } from '../../lib/api'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { Progress } from '@/components/ui/progress'
import { useState } from 'react'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet"

function RunCard({ run, onRetry, onClick }: { run: BillingRunOut, onRetry?: (id: number) => void, onClick?: (id: number) => void }) {
  const isRunning = run.status === 'RUNNING' || run.status === 'QUEUED' || run.status === 'PENDING'
  const isComplete = run.status === 'COMPLETED' || run.status === 'SUCCESS'
  const isFailed = run.status === 'FAILED'
  const isPartial = run.status === 'COMPLETED_WITH_ERRORS' || run.status === 'PARTIAL'
  
  let total = run.total_accounts || 1
  if (total === 0) total = 1
  const progress = Math.round(((run.succeeded + run.failed) / total) * 100)

  return (
    <div 
      className={cn("flex flex-col gap-3 rounded-lg border bg-card p-4 shadow-sm", onClick && "cursor-pointer hover:border-primary/50 transition-colors")}
      onClick={() => onClick && onClick(run.id)}
    >
      <div className="flex items-center justify-between border-b pb-3">
        <div className="flex items-center gap-2">
          <Zap className={cn("size-5", isRunning ? "text-amber-500 fill-amber-500 animate-pulse" : isComplete ? "text-emerald-500" : isFailed ? "text-red-500" : "text-blue-500")} />
          <span className="font-semibold">{run.batch_name}</span>
          <span className="text-xs text-muted-foreground ml-2 px-2 py-0.5 bg-slate-100 rounded-full">
            Cycle {run.cycle_number}
          </span>
        </div>
        <div className="text-sm font-medium">
          {isRunning && <span className="text-amber-600 flex items-center gap-1"><Loader2 size={12} className="animate-spin" /> {run.status}</span>}
          {isComplete && <span className="text-emerald-600 flex items-center gap-1"><CheckCircle2 size={12} /> {run.status}</span>}
          {isFailed && <span className="text-red-600 flex items-center gap-1"><XCircle size={12} /> {run.status}</span>}
          {isPartial && <span className="text-orange-600 flex items-center gap-1"><AlertTriangle size={12} /> {run.status}</span>}
        </div>
      </div>
      
      <div className="flex flex-col gap-1.5 mt-1">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>{run.succeeded + run.failed} / {run.total_accounts} accounts processed</span>
          <span>{progress}%</span>
        </div>
        <Progress value={progress} className="h-2" />
        <div className="flex justify-between mt-2 text-xs">
          <span className="text-emerald-600 font-medium">{run.succeeded} Success</span>
          {run.failed > 0 && <span className="text-red-600 font-medium">{run.failed} Failed</span>}
        </div>
        
        {run.failures && run.failures.length > 0 && (
          <div className="mt-2 bg-red-50 rounded-md border border-red-100 p-2 text-xs">
            <p className="font-semibold text-red-700 mb-1 flex items-center gap-1">
              <AlertTriangle size={12} /> Failure Details:
            </p>
            <ul className="list-disc pl-4 text-red-600 space-y-1 mb-2">
              {run.failures.map((f: any, i: number) => (
                <li key={i}>
                  <strong>{f.account_number}:</strong> {f.error_message}
                </li>
              ))}
            </ul>
            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                className="mt-1 h-7 text-xs bg-white text-red-700 hover:bg-red-50 hover:text-red-800"
                onClick={(e) => {
                  e.stopPropagation()
                  onRetry(run.id)
                }}
                disabled={isRunning}
              >
                {isRunning ? <Loader2 size={12} className="animate-spin mr-1" /> : <Play size={12} className="mr-1" />}
                Retry Failed
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default function GenerationHub() {
  const queryClient = useQueryClient()
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null)

  const { data: runResults, isLoading: loadingResults } = useQuery({
    queryKey: ['run-results', selectedRunId],
    queryFn: () => getRunResults(selectedRunId!),
    enabled: !!selectedRunId
  })

  const handleViewPdf = async (success: any) => {
    try {
      const url = await fetchPdfBlobUrl(success.date, success.cycle, success.batch, success.filename)
      window.open(url, '_blank')
    } catch (e) {
      toast.error('Failed to open PDF')
    }
  }

  const handleDownloadPdf = async (success: any) => {
    try {
      const url = await fetchPdfBlobUrl(success.date, success.cycle, success.batch, success.filename)
      const a = document.createElement('a')
      a.href = url
      a.download = success.filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    } catch (e) {
      toast.error('Failed to download PDF')
    }
  }
  
  const { data: pendingBatches, isLoading: loadingBatches } = useQuery({
    queryKey: ['billing-pending-batches'],
    queryFn: () => getPendingBatches(),
    refetchInterval: 5000,
  })

  const { data: runs, isLoading: loadingRuns } = useQuery({
    queryKey: ['billing-runs'],
    queryFn: () => getRuns(),
    refetchInterval: 3000,
  })

  const batchMutation = useMutation({
    mutationFn: (uploadIds: number[]) => generateGroupBatch(uploadIds),
    onSuccess: (data) => {
      toast.success(data.message)
      queryClient.invalidateQueries({ queryKey: ['billing-pending-batches'] })
      queryClient.invalidateQueries({ queryKey: ['billing-runs'] })
    },
    onError: (err: any) => toast.error(err.detail || 'Failed to start batch generation')
  })

  const retryMutation = useMutation({
    mutationFn: (runId: number) => retryFailedRun(runId),
    onSuccess: (data) => {
      toast.success(data.message)
      queryClient.invalidateQueries({ queryKey: ['billing-runs'] })
    },
    onError: (err: any) => toast.error(err.detail || 'Failed to retry run')
  })

  const handleGenerateAll = async () => {
    if (!pendingBatches || pendingBatches.length === 0) return
    let i = 0;
    for (const batch of pendingBatches) {
      toast.success(`Queueing Cycle ${batch.cycle_number}...`)
      await batchMutation.mutateAsync(batch.upload_ids)
      i++
      await new Promise(r => setTimeout(r, 1000))
    }
    toast.success(`Queued ${i} cycles successfully!`)
  }

  const activeRuns = runs?.filter(r => r.status === 'RUNNING' || r.status === 'QUEUED' || r.status === 'PENDING') || []
  const recentRuns = runs?.filter(r => r.status !== 'RUNNING' && r.status !== 'QUEUED' && r.status !== 'PENDING').slice(0, 10) || []
  const batchesList = pendingBatches || []
  const hasBatches = batchesList.length > 0

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <PageHeader 
          title="Generation Hub" 
          description="Monitor active batch jobs and trigger grouped invoice generation for real GMF cycles." 
        />
        {hasBatches && (
          <Button onClick={handleGenerateAll} disabled={batchMutation.isPending} className="bg-emerald-600 hover:bg-emerald-700 font-semibold shadow-sm">
            <Play size={16} className="mr-2 fill-current" />
            Generate All Batches ({batchesList.length})
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Approved GMFs ready to generate */}
        <div className="flex flex-col gap-4">
          <h3 className="font-semibold text-lg">Ready for Generation (Batches of 10)</h3>
          <div className="rounded-xl border bg-card shadow-sm flex flex-col min-h-[400px]">
            {loadingBatches ? (
              <div className="flex-1 flex items-center justify-center">
                <Loader2 className="animate-spin text-muted-foreground" />
              </div>
            ) : !hasBatches ? (
              <div className="flex-1 flex flex-col items-center justify-center p-8 text-muted-foreground text-center">
                <CheckCircle2 size={48} className="mb-4 text-emerald-500/20" />
                <p>No pending grouped batches.</p>
                <p className="text-sm mt-1">All approved GMFs have been queued or processed.</p>
              </div>
            ) : (
              <div className="flex flex-col p-2 gap-2 max-h-[600px] overflow-y-auto">
                {batchesList.map(batch => (
                  <div key={`${batch.cycle_number}-${batch.date}`} className="flex items-center justify-between p-4 rounded-lg border bg-background hover:border-border/80 transition-colors">
                    <div className="flex flex-col">
                      <div className="flex items-center gap-2">
                        <FileText size={16} className="text-blue-500" />
                        <span className="font-medium text-[15px]">Cycle {batch.cycle_number}</span>
                        <span className="text-muted-foreground text-sm mx-2">|</span>
                        <span className="text-muted-foreground text-sm">{batch.date}</span>
                      </div>
                      <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
                        <span className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full font-medium">
                          {batch.file_count} Invoices
                        </span>
                      </div>
                    </div>
                    <Button 
                      onClick={() => batchMutation.mutate(batch.upload_ids)}
                      disabled={batchMutation.isPending}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      {batchMutation.isPending && batchMutation.variables === batch.upload_ids ? (
                        <Loader2 size={16} className="mr-2 animate-spin" />
                      ) : (
                        <Play size={16} className="mr-2" />
                      )}
                      Generate Cycle
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Live Runs and History */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-lg flex items-center gap-2">
              Live Runs
              {activeRuns.length > 0 && (
                <span className="bg-amber-100 text-amber-700 text-xs px-2 py-0.5 rounded-full animate-pulse">
                  {activeRuns.length} Active
                </span>
              )}
            </h3>
          </div>
          
          <div className="flex flex-col gap-3">
            {loadingRuns ? (
              <div className="h-32 animate-pulse rounded-lg bg-muted" />
            ) : activeRuns.length === 0 ? (
              <div className="rounded-xl border bg-card p-6 text-center text-sm text-muted-foreground shadow-sm">
                No active billing runs at the moment.
              </div>
            ) : (
              activeRuns.map(run => <RunCard key={run.id} run={run} onRetry={(id) => retryMutation.mutate(id)} onClick={(id) => setSelectedRunId(id)} />)
            )}
          </div>

          <h3 className="font-semibold text-lg mt-6">Recent Completed Runs</h3>
          <div className="flex flex-col gap-3">
            {loadingRuns ? (
              <div className="h-32 animate-pulse rounded-lg bg-muted" />
            ) : recentRuns.length === 0 ? (
              <div className="rounded-xl border border-dashed bg-transparent p-6 text-center text-sm text-muted-foreground">
                No recent run history.
              </div>
            ) : (
              recentRuns.map(run => <RunCard key={run.id} run={run} onRetry={(id) => retryMutation.mutate(id)} onClick={(id) => setSelectedRunId(id)} />)
            )}
          </div>
        </div>
      </div>

      <Sheet open={!!selectedRunId} onOpenChange={(open) => !open && setSelectedRunId(null)}>
        <SheetContent side="right" className="w-full sm:max-w-xl overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Run Details</SheetTitle>
            <SheetDescription>
              View successful generated invoices and failures for this run.
            </SheetDescription>
          </SheetHeader>
          
          <div className="mt-6 flex flex-col gap-6">
            {loadingResults ? (
              <div className="flex justify-center p-8"><Loader2 className="animate-spin text-muted-foreground" /></div>
            ) : runResults ? (
              <>
                <div className="flex flex-col gap-3">
                  <h4 className="font-semibold text-sm flex items-center gap-2">
                    <CheckCircle2 size={16} className="text-emerald-500" />
                    Generated Invoices ({runResults.successes.length})
                  </h4>
                  {runResults.successes.length === 0 ? (
                    <p className="text-sm text-muted-foreground italic">No successful invoices.</p>
                  ) : (
                    <div className="flex flex-col gap-2 max-h-[300px] overflow-y-auto pr-2">
                      {runResults.successes.map((s: any, idx: number) => (
                        <div key={idx} className="flex items-center justify-between p-3 rounded border bg-slate-50 text-sm">
                          <div className="flex items-center gap-2">
                            <FileText size={16} className="text-blue-500" />
                            <span className="font-medium">{s.account_number}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button variant="ghost" size="icon-sm" onClick={() => handleViewPdf(s)} title="View PDF">
                              <Eye size={14} />
                            </Button>
                            <Button variant="ghost" size="icon-sm" onClick={() => handleDownloadPdf(s)} title="Download PDF">
                              <Download size={14} />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {runResults.failures.length > 0 && (
                  <div className="flex flex-col gap-3">
                    <h4 className="font-semibold text-sm flex items-center gap-2 text-red-600">
                      <XCircle size={16} />
                      Failures ({runResults.failures.length})
                    </h4>
                    <div className="flex flex-col gap-2 max-h-[300px] overflow-y-auto pr-2">
                      {runResults.failures.map((f: any, idx: number) => (
                        <div key={idx} className="flex flex-col p-3 rounded border border-red-100 bg-red-50 text-sm">
                          <span className="font-medium text-red-700">{f.account_number}</span>
                          <span className="text-red-600/80 text-xs mt-1">{f.error_message}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : null}
          </div>
        </SheetContent>
      </Sheet>
    </div>
  )
}
