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
    <div className="flex flex-col gap-6 max-w-5xl mx-auto">
      <div className="flex justify-between items-end">
        <PageHeader 
          title="Schedule Manager" 
          description="Configure automated monthly generation schedules for billing cycles." 
        />
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus size={16} className="mr-2" /> New Schedule
        </Button>
      </div>

      {showForm && (
        <div className="rounded-xl border bg-card p-6 shadow-sm mb-4">
          <h3 className="font-semibold text-lg mb-4">Create New Schedule</h3>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Schedule Name</label>
              <input 
                type="text" 
                required 
                value={name} 
                onChange={e => setName(e.target.value)} 
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                placeholder="e.g. Cycle 1 Main Run"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Day of Month</label>
              <input 
                type="number" 
                min="1" 
                max="28" 
                required 
                value={day} 
                onChange={e => setDay(e.target.value)} 
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Run Time (HH:MM)</label>
              <input 
                type="time" 
                required 
                value={time} 
                onChange={e => setTime(e.target.value)} 
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Approval Lead Time (Days)</label>
              <input 
                type="number" 
                min="1" 
                max="14" 
                required 
                value={leadDays} 
                onChange={e => setLeadDays(e.target.value)} 
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                title="How many days before the run time should the GMF be approved?"
              />
            </div>
            <div className="col-span-full flex justify-end gap-2 mt-2">
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? <Loader2 size={16} className="mr-2 animate-spin" /> : null}
                Save Schedule
              </Button>
            </div>
          </form>
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="animate-spin text-muted-foreground size-8" />
        </div>
      ) : schedules?.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 border border-dashed rounded-xl text-muted-foreground">
          <CalendarClock size={48} className="mb-4 opacity-20" />
          <p>No schedules configured.</p>
          <p className="text-sm mt-1">Click "New Schedule" to automate your billing runs.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {schedules?.map((schedule) => (
            <div key={schedule.id} className={cn("flex flex-col rounded-xl border bg-card shadow-sm p-5 transition-colors", !schedule.is_active && "bg-muted/50")}>
              <div className="flex justify-between items-start mb-4">
                <div className="flex flex-col">
                  <h3 className="font-semibold text-lg flex items-center gap-2">
                    {schedule.name}
                    {!schedule.is_active && <span className="text-xs bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full">Disabled</span>}
                  </h3>
                  <span className="text-sm text-muted-foreground mt-1">
                    Runs every month on day <strong>{schedule.day_of_month}</strong> at <strong>{schedule.run_time}</strong>
                  </span>
                </div>
                <Switch 
                  checked={schedule.is_active} 
                  onCheckedChange={() => toggleMutation.mutate(schedule.id)}
                  disabled={toggleMutation.isPending}
                />
              </div>
              
              <div className="flex items-center gap-4 text-sm mt-2 pt-4 border-t">
                <div className="flex-1">
                  <span className="text-muted-foreground">Approval Lead: </span>
                  <span className="font-medium">{schedule.approval_lead_days} days</span>
                </div>
                <div className="flex-1">
                  <span className="text-muted-foreground">Timezone: </span>
                  <span className="font-medium">{schedule.timezone}</span>
                </div>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="text-red-500 hover:text-red-600 hover:bg-red-50"
                  onClick={() => {
                    if (confirm("Delete this schedule?")) {
                      deleteMutation.mutate(schedule.id)
                    }
                  }}
                  disabled={deleteMutation.isPending}
                >
                  <Trash2 size={16} />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
