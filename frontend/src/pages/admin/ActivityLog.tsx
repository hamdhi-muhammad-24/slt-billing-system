import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileSearch, FileText, CheckCircle2, XCircle, Zap, Bell, Check, Trash2, Eye } from 'lucide-react'
import { getNotifications, markNotificationRead, markAllNotificationsRead, clearReadNotifications } from '../../lib/api'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

function EventIcon({ type }: { type: string }) {
  switch (type) {
    case 'GMF_DETECTED': return <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-cyan-100 text-cyan-600"><FileSearch size={18} /></div>
    case 'TEST_GMF_RECEIVED': return <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-indigo-600"><FileText size={18} /></div>
    case 'PREVIEW_GENERATED': return <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-600"><Eye size={18} /></div>
    case 'APPROVED': return <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600"><CheckCircle2 size={18} /></div>
    case 'REJECTED': return <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-rose-100 text-rose-600"><XCircle size={18} /></div>
    case 'BATCH_STARTED': return <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600"><Zap size={18} /></div>
    case 'BATCH_COMPLETED': return <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600"><CheckCircle2 size={18} /></div>
    case 'BATCH_FAILED':
    case 'ERROR': return <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-red-100 text-red-600"><XCircle size={18} /></div>
    default: return <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-600"><Bell size={18} /></div>
  }
}

export default function ActivityLog() {
  const queryClient = useQueryClient()
  
  const { data: notifications, isLoading } = useQuery({
    queryKey: ['billing-notifications-all'],
    queryFn: () => getNotifications(false), // get all
    refetchInterval: 10000,
  })

  const readMutation = useMutation({
    mutationFn: (id: number) => markNotificationRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['billing-notifications-all'] })
  })

  const readAllMutation = useMutation({
    mutationFn: () => markAllNotificationsRead(),
    onSuccess: () => {
      toast.success("All marked as read")
      queryClient.invalidateQueries({ queryKey: ['billing-notifications-all'] })
    }
  })

  const clearMutation = useMutation({
    mutationFn: () => clearReadNotifications(),
    onSuccess: () => {
      toast.success("Cleared read notifications")
      queryClient.invalidateQueries({ queryKey: ['billing-notifications-all'] })
    }
  })

  const unreadCount = notifications?.filter(n => !n.is_read).length || 0

  return (
    <div className="flex flex-col gap-6 max-w-4xl mx-auto">
      <div className="flex justify-between items-end">
        <PageHeader 
          title="Activity Log" 
          description="System events, notifications, and alerts" 
        />
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => readAllMutation.mutate()}
            disabled={unreadCount === 0 || readAllMutation.isPending}
          >
            <Check size={14} className="mr-1.5" /> Mark All Read
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => clearMutation.mutate()}
            disabled={clearMutation.isPending}
            className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
          >
            <Trash2 size={14} className="mr-1.5" /> Clear Read
          </Button>
        </div>
      </div>

      <div className="glass-card shadow-lg overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-4">
            {[1,2,3,4,5].map(i => (
              <div key={i} className="flex gap-4">
                <div className="size-10 animate-pulse rounded-full bg-muted" />
                <div className="flex-1 space-y-2 py-1">
                  <div className="h-4 w-1/4 animate-pulse rounded bg-muted" />
                  <div className="h-3 w-3/4 animate-pulse rounded bg-muted" />
                </div>
              </div>
            ))}
          </div>
        ) : notifications?.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
            <Bell size={48} className="mb-4 opacity-20" />
            <p>No activity recorded yet.</p>
          </div>
        ) : (
          <div className="flex flex-col divide-y divide-border/40">
            {notifications?.map((notif) => (
              <div 
                key={notif.id} 
                className={cn(
                  "flex gap-4 p-4 transition-all duration-150 border-l-4 relative pl-5", 
                  !notif.is_read 
                    ? "border-l-primary bg-primary/5" 
                    : "border-l-transparent hover:bg-muted/40"
                )}
              >
                <EventIcon type={notif.event_type} />
                <div className="flex-1 flex flex-col">
                  <div className="flex justify-between items-start">
                    <span className={cn("font-semibold text-[15px]", !notif.is_read ? "text-primary" : "text-foreground")}>
                      {notif.title}
                    </span>
                    <span className="text-xs text-muted-foreground whitespace-nowrap ml-4">
                      {new Date(notif.created_at).toLocaleString()}
                    </span>
                  </div>
                  <span className={cn("text-sm mt-1 leading-relaxed", !notif.is_read ? "text-foreground" : "text-muted-foreground")}>
                    {notif.message}
                  </span>
                  
                  {!notif.is_read && (
                    <div className="mt-3">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="h-7 text-xs px-2.5 text-primary hover:text-primary hover:bg-primary/10 rounded-full font-semibold border border-primary/20"
                        onClick={() => readMutation.mutate(notif.id)}
                      >
                        <Check size={12} className="mr-1" /> Mark as read
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
