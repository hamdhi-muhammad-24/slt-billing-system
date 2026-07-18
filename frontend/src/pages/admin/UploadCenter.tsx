import { useState, useRef } from 'react'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { uploadGmf } from '../../lib/api'
import { Upload, File, Archive, X, Trash2, CheckCircle2 } from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

export default function UploadCenter() {
  const [folderType, setFolderType] = useState<string>('Cycle_1')
  const [files, setFiles] = useState<File[]>([])
  const [dragging, setDragging] = useState<boolean>(false)
  const [uploading, setUploading] = useState<boolean>(false)
  const [success, setSuccess] = useState<boolean>(false)
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(true)
  }

  const handleDragLeave = () => {
    setDragging(false)
  }

  const isValidGmfFile = (file: File): boolean => {
    const name = file.name
    const lastDot = name.lastIndexOf('.')
    if (lastDot === -1) return true // no extension is valid GMF
    const ext = name.substring(lastDot).toLowerCase()
    const extClean = ext.startsWith('.') ? ext.substring(1) : ext
    const isNumeric = /^\d+$/.test(extClean)
    return ext === '.zip' || ext === '.gmf' || isNumeric
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    if (e.dataTransfer.files) {
      const droppedFiles = Array.from(e.dataTransfer.files)
      const valid = droppedFiles.filter(isValidGmfFile)
      if (valid.length !== droppedFiles.length) {
        toast.error("Invalid file format. Please upload valid GMF formats (no extension, numeric suffixes like .1, .6, or .gmf, or .zip).")
      }
      if (valid.length > 0) {
        setFiles(prev => [...prev, ...valid])
        setSuccess(false)
      }
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      const valid = selectedFiles.filter(isValidGmfFile)
      if (valid.length !== selectedFiles.length) {
        toast.error("Invalid file format. Please upload valid GMF formats (no extension, numeric suffixes like .1, .6, or .gmf, or .zip).")
      }
      if (valid.length > 0) {
        setFiles(prev => [...prev, ...valid])
        setSuccess(false)
      }
    }
  }

  const removeFile = (idx: number) => {
    setFiles(prev => prev.filter((_, i) => i !== idx))
  }

  const clearAll = () => {
    setFiles([])
    setSuccess(false)
  }

  const handleUpload = async () => {
    if (files.length === 0) {
      toast.error("Please add files to upload first.")
      return
    }

    setUploading(true)
    let processed = 0
    const total = files.length
    const BATCH_SIZE = 200 // Larger batches are safe now that server-side parsing runs in background.

    try {
      for (let i = 0; i < total; i += BATCH_SIZE) {
        const chunk = files.slice(i, i + BATCH_SIZE)
        await uploadGmf(chunk, folderType)
        processed += chunk.length
      }

      toast.success(`Successfully uploaded ${total} files! Processing in background...`)
      setFiles([])
      setSuccess(true)
    } catch (err: any) {
      toast.error(err?.message || `Failed to upload files after processing ${processed}.`)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Upload Center" 
        description="Upload GMF folders, ZIP files, or GMF files without size limitations." 
      />

      <Card className="glass-card shadow-lg">
        <CardContent className="space-y-6 p-6">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center justify-between">
            <div className="flex flex-col gap-1">
              <span className="text-sm font-semibold">Select Destination Folder / Cycle</span>
              <span className="text-xs text-muted-foreground">Select where these uploads will be archived</span>
            </div>
            
            <select
              value={folderType}
              onChange={(e) => setFolderType(e.target.value)}
              className="w-full sm:w-64 rounded-md border-none bg-gradient-to-r from-slate-900 via-blue-900 to-indigo-800 text-white dark:from-slate-100 dark:via-blue-50 dark:to-indigo-200 dark:text-slate-900 font-extrabold px-4 py-2.5 text-sm shadow-[0_4px_12px_rgba(0,0,0,0.15)] hover:scale-[1.01] transition-all cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 text-center"
            >
              <option value="Cycle_1" className="bg-background text-foreground font-bold">Cycle 1</option>
              <option value="Cycle_2" className="bg-background text-foreground font-bold">Cycle 2</option>
              <option value="Cycle_3" className="bg-background text-foreground font-bold">Cycle 3</option>
              <option value="Cycle_4" className="bg-background text-foreground font-bold">Cycle 4</option>
              <option value="Test_GMFs" className="bg-background text-foreground font-bold">Test GMFs</option>
            </select>
          </div>

          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              "flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-12 cursor-pointer transition-all min-h-64 shadow-[inset_0_2px_4px_rgba(0,0,0,0.02)]",
              dragging 
                ? "border-primary bg-primary/5 scale-[1.01] shadow-md" 
                : "border-border/60 bg-gradient-to-b from-card to-slate-50/10 dark:to-slate-900/5 hover:border-primary/50 hover:bg-muted/40"
            )}
          >
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileSelect} 
              multiple 
              className="hidden" 
            />
            <div className="flex size-16 items-center justify-center rounded-full bg-primary/10 text-primary mb-4 shadow-sm">
              <Upload size={32} />
            </div>
            <span className="text-lg font-bold bg-gradient-to-r from-slate-900 via-blue-900 to-indigo-700 dark:from-slate-100 dark:via-blue-100 dark:to-indigo-300 bg-clip-text text-transparent">Drag & Drop files here</span>
            <span className="text-sm text-muted-foreground mt-2 text-center">
              Supports GMF format files (no extension, numeric suffixes like .1, .6, or .gmf) or ZIP archives.<br/>
              Or click to browse from your device.
            </span>
          </div>

          {files.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b pb-2">
                <span className="text-sm font-semibold">Queue ({files.length} items)</span>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={clearAll} 
                  className="text-muted-foreground hover:text-destructive flex items-center gap-1.5"
                >
                  <Trash2 size={14} />
                  Clear All
                </Button>
              </div>

              <div className="max-h-64 overflow-y-auto divide-y">
                {files.length > 100 ? (
                  <div className="py-4 text-center text-sm text-muted-foreground">
                    {files.length} files selected. Ready for chunked upload.
                  </div>
                ) : (
                  files.map((file, idx) => {
                    const isZip = file.name.endsWith('.zip')
                    return (
                      <div key={idx} className="flex items-center justify-between py-2 text-sm">
                        <div className="flex items-center gap-2.5 truncate">
                          {isZip ? (
                            <Archive size={16} className="text-amber-500 shrink-0" />
                          ) : (
                            <File size={16} className="text-blue-500 shrink-0" />
                          )}
                          <span className="font-medium truncate">{file.name}</span>
                          <span className="text-xs text-muted-foreground font-mono">
                            ({(file.size / 1024).toFixed(1)} KB)
                          </span>
                        </div>
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          onClick={() => removeFile(idx)} 
                          className="rounded-full size-8 text-muted-foreground hover:text-destructive"
                        >
                          <X size={14} />
                        </Button>
                      </div>
                    )
                  })
                )}
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t">
                <Button 
                  variant="outline" 
                  onClick={clearAll}
                  disabled={uploading}
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleUpload}
                  disabled={uploading}
                  className="flex items-center gap-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 font-extrabold shadow-[0_4px_12px_rgba(16,185,129,0.25)] text-white hover:scale-[1.01] border-transparent transition-all"
                >
                  {uploading ? "Uploading..." : "Upload"}
                </Button>
              </div>
            </div>
          )}

          {success && (
            <div className="flex items-center gap-3 rounded-lg border border-emerald-500/25 bg-emerald-500/5 p-4 text-emerald-800 dark:text-emerald-300">
              <CheckCircle2 className="size-5 shrink-0 text-emerald-500" />
              <div className="flex flex-col">
                <span className="font-semibold text-sm">Batch upload successfully queued</span>
                <span className="text-xs text-muted-foreground mt-0.5">
                  The files have been transferred to the processing server and will reflect in GMF Monitor shortly.
                </span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
