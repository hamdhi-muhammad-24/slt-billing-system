import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileText, Eye, CheckCircle2, XCircle, Loader2, Sparkles, FileSearch, Maximize2, Download, X, AlertCircle, History } from 'lucide-react'
import { getUploads, previewInvoice, updateTemplateStatus, getSettings, updateSettings, getTemplateHistory } from '../../lib/api'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { motion, AnimatePresence } from 'framer-motion'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet"

export default function InvoicePreview() {
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [previewPdfUrl, setPreviewPdfUrl] = useState<string | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [selectedMode, setSelectedMode] = useState<'auto' | 'manual' | null>(null)
  const [showHistory, setShowHistory] = useState(false)
  
  // Rejection dialog state
  const [rejectTemplateId, setRejectTemplateId] = useState<string | null>(null)
  const [rejectReason, setRejectReason] = useState<string>('')
  
  const { data: uploads, isLoading } = useQuery({
    queryKey: ['billing-uploads'],
    queryFn: () => getUploads(undefined, undefined),
    refetchInterval: 5000,
  })

  const { data: settingsData } = useQuery({
    queryKey: ['billing-settings'],
    queryFn: getSettings,
  })

  useEffect(() => {
    if (settingsData?.billing_mode) {
      setSelectedMode(settingsData.billing_mode as 'auto' | 'manual')
    }
  }, [settingsData])

  const { data: historyData } = useQuery({
    queryKey: ['template-history'],
    queryFn: getTemplateHistory,
    refetchInterval: 5000,
  })

  const testGmfs = (uploads || []).filter(u => u.folder_type === 'Test_GMFs')
  const selectedGmf = testGmfs.find(u => u.id === selectedId)

  const settingsMutation = useMutation({
    mutationFn: (mode: string) => updateSettings({ billing_mode: mode }),
    onSuccess: (resData) => {
      setSelectedMode(resData.billing_mode as 'auto' | 'manual')
      queryClient.invalidateQueries({ queryKey: ['billing-settings'] })
      toast.success(`Validation mode switched to ${resData.billing_mode.toUpperCase()}`)
    },
    onError: (err: any) => toast.error(err.detail || 'Failed to update billing mode')
  })

  const previewMutation = useMutation({
    mutationFn: (id: number) => previewInvoice(id),
    onSuccess: (resData) => {
      toast.success(resData.message)
      setPreviewPdfUrl(resData.pdf_url)
      queryClient.invalidateQueries({ queryKey: ['billing-uploads'] })
    },
    onError: (err: any) => toast.error(err.detail || 'Failed to generate preview')
  })

  const approveMutation = useMutation({
    mutationFn: (templateId: string) => updateTemplateStatus(templateId, 'APPROVED'),
    onSuccess: () => {
      toast.success(`Template APPROVED successfully`)
      queryClient.invalidateQueries({ queryKey: ['billing-templates'] })
      queryClient.invalidateQueries({ queryKey: ['billing-uploads'] })
      queryClient.invalidateQueries({ queryKey: ['template-history'] })
    },
    onError: (err: any) => toast.error(err.detail || 'Failed to approve template')
  })

  const rejectMutation = useMutation({
    mutationFn: ({ templateId, reason }: { templateId: string, reason: string }) => 
      updateTemplateStatus(templateId, 'REJECTED', reason),
    onSuccess: () => {
      toast.success(`Template REJECTED successfully`)
      setRejectTemplateId(null)
      setRejectReason('')
      queryClient.invalidateQueries({ queryKey: ['billing-templates'] })
      queryClient.invalidateQueries({ queryKey: ['billing-uploads'] })
      queryClient.invalidateQueries({ queryKey: ['template-history'] })
    },
    onError: (err: any) => toast.error(err.detail || 'Failed to reject template')
  })

  const checkMode = (action: () => void) => {
    if (selectedMode === null) {
      toast.error("First select the mode", {
        style: {
          backgroundColor: '#ef4444',
          color: '#ffffff',
          fontWeight: 'bold',
          border: '1px solid #dc2626'
        }
      })
      return
    }
    action()
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between shrink-0">
        <PageHeader 
          title="Invoice Preview" 
          description="Review test GMFs, generate preview invoices, and approve them for batch generation." 
        />
        <Button 
          variant="outline" 
          onClick={() => setShowHistory(true)}
          className="flex items-center gap-2 font-bold shadow-sm"
        >
          <History size={16} />
          Validation Logs
        </Button>
      </div>

      {/* Mode Selector */}
      <div className="flex flex-col gap-3 p-4 rounded-xl border bg-card shadow-sm shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex flex-col">
            <span className="text-sm font-semibold">Template Validation Mode</span>
            <span className="text-xs text-muted-foreground">Select a mode before executing preview or approval actions.</span>
          </div>
          {selectedMode === null && (
            <span className="text-xs font-bold text-red-500 flex items-center gap-1 animate-pulse">
              <AlertCircle size={14} /> Mode selection required!
            </span>
          )}
        </div>
        <div className="flex gap-3">
          <Button
            type="button"
            className={cn(
              "flex-1 py-6 text-base font-bold shadow-sm transition-all border",
              selectedMode === 'auto' 
                ? "bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white scale-[1.01] shadow-[0_4px_15px_rgba(59,130,246,0.3)] font-extrabold border-transparent" 
                : "bg-card border-border hover:bg-muted/50 hover:border-primary/20 text-muted-foreground hover:text-foreground font-semibold"
            )}
            onClick={() => settingsMutation.mutate('auto')}
            disabled={settingsMutation.isPending}
          >
            Auto Mode
            <span className="ml-2 text-xs font-normal opacity-85 block sm:inline">(Automated generation on approval)</span>
          </Button>
          <Button
            type="button"
            className={cn(
              "flex-1 py-6 text-base font-bold shadow-sm transition-all border",
              selectedMode === 'manual' 
                ? "bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white scale-[1.01] shadow-[0_4px_15px_rgba(59,130,246,0.3)] font-extrabold border-transparent" 
                : "bg-card border-border hover:bg-muted/50 hover:border-primary/20 text-muted-foreground hover:text-foreground font-semibold"
            )}
            onClick={() => settingsMutation.mutate('manual')}
            disabled={settingsMutation.isPending}
          >
            Manual Mode
            <span className="ml-2 text-xs font-normal opacity-85 block sm:inline">(Manual run inside Generation Hub)</span>
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel: List of Test GMFs */}
        <div className="lg:col-span-1 rounded-xl border bg-card shadow-sm p-4 flex flex-col h-[620px]">
          <h3 className="font-semibold text-lg flex items-center gap-2 border-b pb-2 shrink-0">
            <FileText size={18} className="text-primary" />
            Test GMF Files
          </h3>
          
          <div className="flex-1 overflow-y-auto pr-1 mt-2">
            {isLoading ? (
              <div className="h-32 flex items-center justify-center">
                <Loader2 className="animate-spin text-muted-foreground" />
              </div>
            ) : testGmfs.length === 0 ? (
              <div className="text-sm text-muted-foreground p-6 text-center flex flex-col items-center justify-center border border-dashed rounded-lg bg-slate-50/50 dark:bg-slate-900/10 h-full">
                <FileSearch size={28} className="mb-2 opacity-20" />
                No Test GMFs found.
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {testGmfs.map(gmf => {
                  const isSelected = gmf.id === selectedId
                  return (
                    <motion.div 
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      key={gmf.id}
                      onClick={() => {
                        setSelectedId(gmf.id)
                        setPreviewPdfUrl(null)
                      }}
                      className={cn(
                        "flex flex-col gap-2 p-3 rounded-lg cursor-pointer border transition-all duration-150 relative pl-4 overflow-hidden",
                        isSelected 
                          ? "border-primary bg-primary/5 shadow-sm" 
                          : "border-border/30 hover:bg-muted/70 hover:border-border/60"
                      )}
                    >
                      <div className={cn("absolute left-0 top-0 bottom-0 w-1 transition-all", isSelected ? "bg-primary" : "bg-transparent")} />
                      <div className="flex items-center gap-2">
                        <FileText size={16} className={cn("shrink-0", isSelected ? "text-primary animate-pulse" : "text-slate-400")} />
                        <span className={cn("font-semibold text-sm leading-none text-foreground truncate flex-1", isSelected ? "text-primary font-bold animate-fade-in" : "")} title={gmf.filename}>
                          {gmf.filename}
                        </span>
                      </div>
                      
                      <div className="flex items-center justify-between mt-1 text-[11px] text-muted-foreground">
                        <div className="flex items-center gap-2">
                          <span className={cn(
                            "text-[10px] font-extrabold px-2 py-0.5 rounded-full transition-colors uppercase border",
                            gmf.status === 'PENDING_APPROVAL' ? "bg-cyan-50 text-cyan-600 border-cyan-200/50 dark:bg-cyan-950/20" :
                            gmf.status === 'APPROVED' ? "bg-emerald-50 text-emerald-600 border-emerald-200/50 dark:bg-emerald-950/20" :
                            gmf.status === 'REJECTED' ? "bg-red-50 text-red-600 border-red-200/50 dark:bg-red-950/20" :
                            "bg-slate-100 text-slate-600 border-slate-200/50 dark:bg-slate-800"
                          )}>
                            {gmf.status === 'PENDING_APPROVAL' ? 'Pending Review' : gmf.status}
                          </span>
                          {gmf.rejection_reason && (
                            <span className="text-[10px] text-red-500 font-semibold truncate max-w-[100px]" title={gmf.rejection_reason}>
                              Reason: {gmf.rejection_reason}
                            </span>
                          )}
                        </div>
                        <span className="font-bold bg-muted/80 px-1.5 py-0.5 rounded text-xs text-slate-600 dark:text-slate-300">
                          {gmf.template_detected || 'Unknown'}
                        </span>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: PDF Viewer and Action Area */}
        <div className="lg:col-span-2 rounded-xl border bg-card shadow-sm overflow-hidden flex flex-col h-[620px] relative bg-slate-50/50 dark:bg-slate-900/10">
          <AnimatePresence mode="wait">
            {!selectedGmf ? (
              <motion.div 
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex-1 flex flex-col items-center justify-center text-muted-foreground p-8"
              >
                <div className="bg-card p-6 rounded-full shadow-sm border mb-4">
                  <Eye size={32} className="text-slate-300 dark:text-slate-600" />
                </div>
                <h3 className="text-lg font-medium text-slate-700 dark:text-slate-300 mb-1">No Invoice Selected</h3>
                <p className="text-sm">Select a Test GMF from the sidebar to begin review.</p>
              </motion.div>
            ) : (
              <motion.div 
                key="content"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex-1 flex flex-col h-full min-h-0"
              >
                {/* Header Actions */}
                <div className="p-4 border-b bg-card flex justify-between items-center shadow-sm z-10 shrink-0">
                  <div className="flex flex-col">
                    <span className="font-semibold text-slate-800 dark:text-slate-200 truncate max-w-[280px]" title={selectedGmf.filename}>
                      {selectedGmf.filename}
                    </span>
                    <span className="text-xs text-muted-foreground font-medium flex items-center gap-1">
                      Template Match: <span className="text-primary font-bold">{selectedGmf.template_detected || 'Unrecognized'}</span>
                    </span>
                  </div>
                  
                  {selectedGmf.status === 'PENDING_APPROVAL' && previewPdfUrl && selectedGmf.template_detected && (
                    <div className="flex gap-2">
                      <Button 
                        variant="outline"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/20 border-red-200"
                        onClick={() => checkMode(() => setRejectTemplateId(selectedGmf.template_detected!))}
                        disabled={rejectMutation.isPending}
                      >
                        <XCircle size={16} className="mr-2" /> Reject Template
                      </Button>
                      <Button 
                        className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm font-bold"
                        onClick={() => checkMode(() => approveMutation.mutate(selectedGmf.template_detected!))}
                        disabled={approveMutation.isPending}
                      >
                        <CheckCircle2 size={16} className="mr-2" /> Approve Template
                      </Button>
                    </div>
                  )}
                  {selectedGmf.status === 'APPROVED' && (
                    <div className="flex gap-2">
                      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-sm font-medium text-emerald-700 border border-emerald-200">
                        <CheckCircle2 size={16} className="text-emerald-600" />
                        Approved
                      </span>
                    </div>
                  )}
                  {selectedGmf.status === 'REJECTED' && (
                    <div className="flex gap-2">
                      <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-3 py-1 text-sm font-medium text-red-700 border border-red-200">
                        <XCircle size={16} className="text-red-600" />
                        Rejected
                      </span>
                    </div>
                  )}
                </div>
                
                {/* Preview Content Area */}
                <div className="flex-1 flex items-center justify-center p-6 bg-slate-100/10 dark:bg-slate-900/20 min-h-0">
                  {previewMutation.isPending ? (
                    <motion.div 
                      initial={{ scale: 0.9, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      className="flex flex-col items-center p-8 bg-card rounded-2xl shadow-sm border"
                    >
                      <Loader2 size={40} className="animate-spin text-primary mb-4" />
                      <h3 className="text-lg font-medium mb-1">Rendering Preview...</h3>
                      <p className="text-sm text-muted-foreground text-center max-w-[250px]">
                        The billing engine is parsing the GMF data and mapping it to the layout...
                      </p>
                    </motion.div>
                  ) : previewPdfUrl ? (
                    <motion.div 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="w-full h-full relative"
                    >
                      <div className="absolute top-2 right-4 flex gap-2 z-10">
                        <Button variant="secondary" size="sm" className="h-8 shadow-sm opacity-80 hover:opacity-100" onClick={() => setIsFullscreen(true)}>
                          <Maximize2 size={14} className="mr-1.5" /> Maximize
                        </Button>
                        <Button variant="secondary" size="sm" className="h-8 shadow-sm opacity-80 hover:opacity-100" onClick={() => window.open(previewPdfUrl, '_blank')}>
                          <Download size={14} className="mr-1.5" /> Download
                        </Button>
                      </div>
                      <iframe 
                        src={`${previewPdfUrl}#toolbar=0`} 
                        className="w-full h-full rounded-lg shadow-md border border-slate-200 bg-white"
                        title="Invoice Preview"
                      />
                    </motion.div>
                  ) : (
                    <motion.div 
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="flex flex-col items-center justify-center text-center p-10 max-w-md bg-card border rounded-2xl shadow-sm"
                    >
                      <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-6">
                        <Sparkles size={28} className="text-primary" />
                      </div>
                      <h3 className="text-xl font-semibold text-slate-800 dark:text-slate-200 mb-2">Ready to Render</h3>
                      <p className="text-muted-foreground mb-8">
                        Generate a high-fidelity PDF preview to verify the layout, calculations, and visual aesthetics before approving this batch for production.
                      </p>
                      <Button 
                        size="lg"
                        className="w-full shadow-md text-base font-bold"
                        onClick={() => checkMode(() => previewMutation.mutate(selectedGmf.id))}
                        disabled={previewMutation.isPending}
                      >
                        <Eye size={18} className="mr-2" />
                        Generate PDF Preview
                      </Button>
                    </motion.div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Full Screen PDF Modal */}
      <AnimatePresence>
        {isFullscreen && previewPdfUrl && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 md:p-8"
            onClick={() => setIsFullscreen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              transition={{ type: "spring", bounce: 0, duration: 0.3 }}
              className="relative max-h-full max-w-5xl w-full h-[90vh] flex flex-col bg-slate-100 rounded-xl overflow-hidden shadow-2xl border border-white/10"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="absolute top-4 right-4 z-10 flex gap-2">
                <button 
                  className="text-slate-600 hover:text-slate-900 bg-white/80 hover:bg-white rounded-full p-2 shadow-sm transition-colors backdrop-blur-sm"
                  onClick={() => setIsFullscreen(false)}
                >
                  <X size={20} />
                </button>
              </div>
              
              <iframe 
                src={`${previewPdfUrl}#toolbar=0&navpanes=0`} 
                title="Full Template Preview" 
                className="w-full h-full bg-white"
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Rejection Reason Modal */}
      <AnimatePresence>
        {rejectTemplateId !== null && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 backdrop-blur-xs p-4"
            onClick={() => setRejectTemplateId(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="relative w-full max-w-md bg-white dark:bg-card border rounded-xl overflow-hidden shadow-xl p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-bold text-slate-800 dark:text-foreground mb-2 flex items-center gap-2">
                <XCircle className="text-red-500" size={20} /> Reject Template
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                Please provide the reason for rejecting template <span className="font-semibold text-slate-700 dark:text-foreground">{rejectTemplateId}</span>:
              </p>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="Describe layout issues, mismatch, or errors..."
                rows={4}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 mb-4"
              />
              <div className="flex justify-end gap-2">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setRejectTemplateId(null)
                    setRejectReason('')
                  }}
                >
                  Cancel
                </Button>
                <Button
                  className="bg-red-600 hover:bg-red-700 text-white font-bold"
                  onClick={() => rejectMutation.mutate({ templateId: rejectTemplateId, reason: rejectReason || 'No reason specified' })}
                  disabled={rejectMutation.isPending}
                >
                  Confirm Rejection
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Validation Logs Drawer */}
      <Sheet open={showHistory} onOpenChange={setShowHistory}>
        <SheetContent side="right" className="w-full sm:max-w-md overflow-y-auto">
          <SheetHeader className="border-b pb-4">
            <SheetTitle className="flex items-center gap-2">
              <History className="text-primary" />
              Template History Logs
            </SheetTitle>
            <SheetDescription>
              View approval and rejection log history for test GMF templates.
            </SheetDescription>
          </SheetHeader>
          <div className="mt-6 flex flex-col gap-3">
            {!historyData || historyData.length === 0 ? (
              <span className="text-sm text-muted-foreground block text-center py-8">No validation history logged.</span>
            ) : (
              historyData.map(log => (
                <div key={log.id} className="p-3 border rounded-lg bg-muted/45 text-xs flex flex-col gap-1.5">
                  <div className="flex items-center justify-between font-bold">
                    <span className="text-foreground dark:text-slate-200 text-[13px]">{log.template_name}</span>
                    <span className={cn(
                      "px-2 py-0.5 rounded text-[10px] uppercase font-bold",
                      log.action === 'APPROVED' ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400" : "bg-red-100 text-red-700 dark:bg-red-950/30 dark:text-red-400"
                    )}>
                      {log.action}
                    </span>
                  </div>
                  {log.filename && <div className="text-muted-foreground text-xs mt-1">File: {log.filename}</div>}
                  {log.reason && <div className="text-red-500 font-semibold text-xs mt-1">Reason: {log.reason}</div>}
                  <div className="text-[10px] text-muted-foreground mt-1.5 font-mono">
                    {new Date(log.timestamp).toLocaleString()}
                  </div>
                </div>
              ))
            )}
          </div>
        </SheetContent>
      </Sheet>
    </div>
  )
}
