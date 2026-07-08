import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CalendarClock, Plus, Trash2, Loader2 } from 'lucide-react'
import { getSchedules, createSchedule, toggleSchedule, deleteSchedule } from '../../lib/api'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { Switch } from '@/components/ui/switch'

export default function ScheduleManager() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  
  // Form State
  const [name, setName] = useState('')
  const [day, setDay] = useState('1')
  const [time, setTime] = useState('02:00')
  const [leadDays, setLeadDays] = useState('2')

  const { data: schedules, isLoading } = useQuery({
    queryKey: ['billing-schedules'],
    queryFn: getSchedules,
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => createSchedule(data),
    onSuccess: () => {
      toast.success("Schedule created successfully")
      setShowForm(false)
      setName('')
      queryClient.invalidateQueries({ queryKey: ['billing-schedules'] })
    },
    onError: (err: any) => toast.error(err.detail || 'Failed to create schedule')
  })

  const toggleMutation = useMutation({
    mutationFn: (id: number) => toggleSchedule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['billing-schedules'] })
    }
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteSchedule(id),
    onSuccess: () => {
      toast.success("Schedule deleted")
      queryClient.invalidateQueries({ queryKey: ['billing-schedules'] })
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({
      name,
      day_of_month: parseInt(day),
      run_time: time,
      approval_lead_days: parseInt(leadDays),
      timezone: 'Asia/Colombo',
      schedule_mode: 'MONTHLY'
    })
  }

  return (
    <div className="flex flex-col gap-8 max-w-5xl mx-auto pb-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <PageHeader 
          title="Schedule Manager" 
          description="Configure automated monthly generation schedules for billing cycles with precision." 
        />
        <Button 
          onClick={() => setShowForm(!showForm)}
          size="lg"
          className="shadow-lg shadow-primary/20 hover:shadow-primary/40 transition-all duration-300"
        >
          <Plus size={18} className="mr-2" /> 
          {showForm ? 'Cancel Creation' : 'New Schedule'}
        </Button>
      </div>

      {showForm && (
        <div className="rounded-2xl border border-primary/10 bg-card/40 backdrop-blur-xl p-8 shadow-2xl shadow-primary/5 animate-in slide-in-from-top-4 zoom-in-95 duration-300">
          <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border/50">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
              <CalendarClock size={20} />
            </div>
            <div>
              <h3 className="font-semibold text-lg">Create New Schedule</h3>
              <p className="text-sm text-muted-foreground">Automate your monthly billing runs</p>
            </div>
          </div>
          
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2.5">
              <label className="text-sm font-semibold tracking-tight">Schedule Name</label>
              <input 
                type="text" 
                required 
                value={name} 
                onChange={e => setName(e.target.value)} 
                className="flex h-11 w-full rounded-xl border border-input/60 bg-background/50 px-4 py-2 text-sm ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-ring"
                placeholder="e.g. Cycle 1 Main Run"
              />
            </div>
            <div className="space-y-2.5">
              <label className="text-sm font-semibold tracking-tight">Day of Month</label>
              <div className="relative">
                <input 
                  type="number" 
                  min="1" 
                  max="28" 
                  required 
                  value={day} 
                  onChange={e => setDay(e.target.value)} 
                  className="flex h-11 w-full rounded-xl border border-input/60 bg-background/50 px-4 py-2 text-sm ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-ring pl-12"
                />
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground font-medium text-sm">
                  Day
                </div>
              </div>
            </div>
            <div className="space-y-2.5">
              <label className="text-sm font-semibold tracking-tight">Run Time (HH:MM)</label>
              <input 
                type="time" 
                required 
                value={time} 
                onChange={e => setTime(e.target.value)} 
                className="flex h-11 w-full rounded-xl border border-input/60 bg-background/50 px-4 py-2 text-sm ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-ring"
              />
            </div>
            <div className="space-y-2.5">
              <label className="text-sm font-semibold tracking-tight">Approval Lead Time</label>
              <div className="relative">
                <input 
                  type="number" 
                  min="1" 
                  max="14" 
                  required 
                  value={leadDays} 
                  onChange={e => setLeadDays(e.target.value)} 
                  className="flex h-11 w-full rounded-xl border border-input/60 bg-background/50 px-4 py-2 text-sm ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-ring pl-12"
                />
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground font-medium text-sm">
                  Days
                </div>
              </div>
            </div>
            <div className="col-span-full flex justify-end gap-3 mt-4 pt-4 border-t border-border/50">
              <Button type="button" variant="ghost" onClick={() => setShowForm(false)} className="rounded-xl">
                Cancel
              </Button>
              <Button type="submit" disabled={createMutation.isPending} className="rounded-xl px-8 shadow-md">
                {createMutation.isPending ? <Loader2 size={16} className="mr-2 animate-spin" /> : null}
                Save Schedule
              </Button>
            </div>
          </form>
        </div>
      )}

      {isLoading ? (
        <div className="flex flex-col items-center justify-center p-20 gap-4">
          <Loader2 className="animate-spin text-primary size-10" />
          <p className="text-muted-foreground font-medium animate-pulse">Loading schedules...</p>
        </div>
      ) : schedules?.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-16 border-2 border-dashed border-border/60 rounded-3xl bg-card/30 text-muted-foreground">
          <div className="size-20 rounded-full bg-primary/5 flex items-center justify-center mb-6">
            <CalendarClock size={40} className="text-primary/40" />
          </div>
          <h3 className="text-xl font-semibold text-foreground mb-2">No schedules configured</h3>
          <p className="text-center max-w-sm mb-6">Automate your billing runs by creating a new schedule. The system will handle generation automatically.</p>
          <Button onClick={() => setShowForm(true)} variant="outline" className="rounded-xl">
            Create First Schedule
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {schedules?.map((schedule) => (
            <div 
              key={schedule.id} 
              className={cn(
                "group relative flex flex-col rounded-2xl border bg-card p-6 transition-all duration-300 hover:shadow-xl hover:-translate-y-1", 
                schedule.is_active ? "border-primary/20 shadow-lg shadow-primary/5" : "border-border/40 bg-muted/20 opacity-80"
              )}
            >
              <div className="flex justify-between items-start mb-6">
                <div className="flex items-start gap-4">
                  <div className={cn(
                    "p-3 rounded-xl flex items-center justify-center transition-colors",
                    schedule.is_active ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                  )}>
                    <CalendarClock size={24} />
                  </div>
                  <div>
                    <h4 className="font-semibold text-lg tracking-tight group-hover:text-primary transition-colors">{schedule.name}</h4>
                    <span className="text-sm font-medium text-muted-foreground flex items-center gap-2 mt-1">
                      <span className={cn(
                        "size-2 rounded-full",
                        schedule.is_active ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-slate-400"
                      )} />
                      {schedule.is_active ? 'Active Schedule' : 'Paused'}
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 bg-background/50 p-1.5 rounded-full border border-border/50">
                  <Switch 
                    checked={schedule.is_active} 
                    onCheckedChange={() => toggleMutation.mutate(schedule.id)}
                    className="data-[state=checked]:bg-emerald-500"
                    disabled={toggleMutation.isPending}
                  />
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="size-8 rounded-full text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                    onClick={() => {
                      if(confirm('Are you sure you want to delete this schedule?')) {
                        deleteMutation.mutate(schedule.id)
                      }
                    }}
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 size={16} />
                  </Button>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mt-auto pt-5 border-t border-border/50">
                <div className="flex flex-col bg-background/50 p-3 rounded-xl border border-border/50">
                  <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">Execution Time</span>
                  <span className="font-medium text-foreground flex items-baseline gap-1">
                    Day {schedule.day_of_month} <span className="text-muted-foreground font-normal text-sm">at</span> {schedule.run_time}
                  </span>
                </div>
                <div className="flex flex-col bg-background/50 p-3 rounded-xl border border-border/50">
                  <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">Approval Window</span>
                  <span className="font-medium text-foreground">
                    {schedule.approval_lead_days} Days prior
                  </span>
                </div>
              </div>

              {schedule.is_active && (
                <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl -z-10 group-hover:bg-primary/10 transition-colors" />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
