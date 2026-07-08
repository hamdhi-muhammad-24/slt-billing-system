import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileText, Eye, CheckCircle2, XCircle, Loader2, Sparkles, FileSearch } from 'lucide-react'
import { getUploads, previewInvoice, approveUpload, rejectUpload } from '../../lib/api'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { motion, AnimatePresence } from 'framer-motion'

export default function InvoicePreview() {
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [previewPdfUrl, setPreviewPdfUrl] = useState<string | null>(null)
  
  const { data: uploads, isLoading } = useQuery({
    queryKey: ['billing-uploads'],
    queryFn: () => getUploads(undefined, undefined),
    refetchInterval: 5000,
  })

  const testGmfs = (uploads || []).filter(u => u.folder_type === 'Test_GMFs')
  const selectedGmf = testGmfs.find(u => u.id === selectedId)

  const previewMutation = useMutation({
    mutationFn: (id: number) => previewInvoice(id),
    onSuccess: (data) => {
      toast.success(data.message)
      setPreviewPdfUrl(data.pdf_url)
      queryClient.invalidateQueries({ queryKey: ['billing-uploads'] })
    },
    onError: (err: any) => toast.error(err.detail || 'Failed to generate preview')
  })

  const approveMutation = useMutation({
    mutationFn: (id: number) => approveUpload(id),
    onSuccess: (data) => {
      toast.success(data.message)
      queryClient.invalidateQueries({ queryKey: ['billing-uploads'] })
    },
    onError: (err: any) => toast.error(err.detail || 'Failed to approve')
  })

  const rejectMutation = useMutation({
    mutationFn: (id: number) => rejectUpload(id, "Rejected by admin via UI"),
    onSuccess: (data) => {
      toast.success(data.message)
      setPreviewPdfUrl(null)
      queryClient.invalidateQueries({ queryKey: ['billing-uploads'] })
    },
    onError: (err: any) => toast.error(err.detail || 'Failed to reject')
  })

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)] gap-4">
      <PageHeader 
        title="Invoice Preview" 
        description="Review test GMFs, generate preview invoices, and approve them for batch generation." 
      />

      <div className="flex flex-1 gap-6 min-h-0">
        {/* Left Panel: List of Test GMFs */}
        <div className="w-1/3 flex flex-col gap-4 overflow-y-auto rounded-xl border bg-card shadow-sm p-4">
          <h3 className="font-semibold text-lg flex items-center gap-2">
            <FileText size={18} className="text-primary" />
            Test GMF Files
          </h3>
          
          {isLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <Loader2 className="animate-spin text-muted-foreground" />
            </div>
          ) : testGmfs.length === 0 ? (
            <div className="text-sm text-muted-foreground p-8 text-center flex flex-col items-center justify-center h-full border border-dashed rounded-lg bg-slate-50/50">
              <FileSearch size={32} className="mb-3 opacity-20" />
              No Test GMFs found.
              <span className="text-xs mt-1">Upload a test file to begin.</span>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {testGmfs.map(gmf => {
                const isSelected = gmf.id === selectedId
                return (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    key={gmf.id}
                    onClick={() => {
                      setSelectedId(gmf.id)
                      setPreviewPdfUrl(null)
                    }}
                    className={cn(
                      "flex flex-col p-3 rounded-lg cursor-pointer border transition-all duration-200",
                      isSelected 
                        ? "border-primary bg-primary/5 shadow-sm ring-1 ring-primary/20" 
                        : "border-transparent hover:bg-muted/80 hover:border-border/50"
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <FileText size={16} className={isSelected ? "text-primary" : "text-slate-400"} />
                      <span className={cn("font-medium text-sm truncate", isSelected ? "text-primary font-semibold" : "")} title={gmf.filename}>
                        {gmf.filename}
                      </span>
                    </div>
                    <div className="flex justify-between items-center mt-2">
                      <span className={cn(
                        "text-xs font-medium px-2 py-0.5 rounded-full transition-colors",
                        gmf.status === 'PENDING_APPROVAL' ? "bg-cyan-100 text-cyan-700 border border-cyan-200/50" :
                        gmf.status === 'APPROVED' ? "bg-emerald-100 text-emerald-700 border border-emerald-200/50" :
                        "bg-slate-100 text-slate-700 border border-slate-200/50"
                      )}>
                        {gmf.status === 'PENDING_APPROVAL' ? 'Pending Review' : gmf.status}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {gmf.template_detected || 'Unknown Template'}
                      </span>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          )}
        </div>

        {/* Right Panel: PDF Viewer and Action Area */}
        <div className="flex-1 flex flex-col rounded-xl border bg-card shadow-sm overflow-hidden relative bg-slate-50/50">
          <AnimatePresence mode="wait">
            {!selectedGmf ? (
              <motion.div 
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex-1 flex flex-col items-center justify-center text-muted-foreground p-8"
              >
                <div className="bg-white p-6 rounded-full shadow-sm border mb-4">
                  <Eye size={32} className="text-slate-300" />
                </div>
                <h3 className="text-lg font-medium text-slate-700 mb-1">No Invoice Selected</h3>
                <p className="text-sm">Select a Test GMF from the sidebar to begin review.</p>
              </motion.div>
            ) : (
              <motion.div 
                key="content"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex-1 flex flex-col h-full"
              >
                {/* Header Actions */}
                <div className="p-4 border-b bg-white flex justify-between items-center shadow-sm z-10">
                  <div className="flex flex-col">
                    <span className="font-semibold text-slate-800 truncate" title={selectedGmf.filename}>
                      {selectedGmf.filename}
                    </span>
                    <span className="text-xs text-muted-foreground font-medium flex items-center gap-1">
                      Template Match: <span className="text-primary">{selectedGmf.template_detected || 'Unrecognized'}</span>
                    </span>
                  </div>
                  
                  {selectedGmf.status === 'PENDING_APPROVAL' && previewPdfUrl && (
                    <div className="flex gap-2">
                      <Button 
                        variant="outline"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                        onClick={() => rejectMutation.mutate(selectedGmf.id)}
                        disabled={rejectMutation.isPending}
                      >
                        <XCircle size={16} className="mr-2" /> Reject
                      </Button>
                      <Button 
                        className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm"
                        onClick={() => approveMutation.mutate(selectedGmf.id)}
                        disabled={approveMutation.isPending}
                      >
                        <CheckCircle2 size={16} className="mr-2" /> Approve for Batch
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
                </div>
                
                {/* Preview Content Area */}
                <div className="flex-1 flex items-center justify-center p-6 bg-slate-100/50">
                  {previewMutation.isPending ? (
                    <motion.div 
                      initial={{ scale: 0.9, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      className="flex flex-col items-center p-8 bg-white rounded-2xl shadow-sm border"
                    >
                      <Loader2 size={40} className="animate-spin text-primary mb-4" />
                      <h3 className="text-lg font-medium mb-1">Generating High-Fidelity Preview</h3>
                      <p className="text-sm text-muted-foreground text-center max-w-[250px]">
                        The billing engine is parsing the GMF data and mapping it to the layout...
                      </p>
                    </motion.div>
                  ) : previewPdfUrl ? (
                    <motion.div 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="w-full h-full"
                    >
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
                      className="flex flex-col items-center justify-center text-center p-10 max-w-md bg-white border rounded-2xl shadow-sm"
                    >
                      <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-6">
                        <Sparkles size={28} className="text-primary" />
                      </div>
                      <h3 className="text-xl font-semibold text-slate-800 mb-2">Ready to Render</h3>
                      <p className="text-muted-foreground mb-8">
                        Generate a high-fidelity PDF preview to verify the layout, calculations, and visual aesthetics before approving this batch for production.
                      </p>
                      <Button 
                        size="lg"
                        className="w-full shadow-md text-base"
                        onClick={() => previewMutation.mutate(selectedGmf.id)}
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
    </div>
  )
}
