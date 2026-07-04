import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { CheckCircle2, Copy, Loader2, Palette, Pencil, Save, X } from 'lucide-react'
import type { InvoiceTemplate } from '../../types'
import {
  activateInvoiceTemplate,
  ApiError,
  listInvoiceTemplates,
  saveInvoiceTemplateCopy,
  saveInvoiceTemplateOriginal,
} from '../../lib/api'
import { ErrorState } from '../../components/states'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { CardSkeleton } from '../../components/ui-kit/Skeletons'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

interface TemplateForm {
  name: string
  description: string
  header_message: string
  footer_message: string
  promotion_message: string
  theme_name: string
  theme_color: string
}

function errDetail(err: unknown): string {
  return err instanceof ApiError ? err.detail : String(err)
}

function formFromTemplate(template: InvoiceTemplate): TemplateForm {
  return {
    name: template.name,
    description: template.description ?? '',
    header_message: template.header_message ?? '',
    footer_message: template.footer_message ?? '',
    promotion_message: template.promotion_message ?? '',
    theme_name: template.theme_name ?? '',
    theme_color: template.theme_color ?? '#004B8D',
  }
}

function TemplateCard({
  template,
  selected,
  onEdit,
  onActivate,
  activating,
}: {
  template: InvoiceTemplate
  selected: boolean
  onEdit: () => void
  onActivate: () => void
  activating: boolean
}) {
  return (
    <article className={cn('surface-section flex min-h-[220px] flex-col p-4 transition-colors', selected && 'border-primary ring-2 ring-primary/15')}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="truncate text-sm font-semibold">{template.name}</h2>
            {template.is_active && (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                <CheckCircle2 size={12} />
                Active
              </span>
            )}
          </div>
          <p className="mt-1 text-xs font-medium text-muted-foreground">{template.template_code}</p>
        </div>
        <span
          className="size-8 shrink-0 rounded-md border border-border"
          style={{ backgroundColor: template.theme_color ?? '#004B8D' }}
          aria-label={template.theme_name ?? 'Template color'}
        />
      </div>

      <p className="mt-3 line-clamp-2 text-sm text-muted-foreground">
        {template.description ?? 'Template metadata placeholder.'}
      </p>

      <div className="mt-4 grid gap-2 text-xs">
        <div className="rounded-md bg-muted/65 px-3 py-2">
          <span className="font-medium text-foreground">Header: </span>
          <span className="text-muted-foreground">{template.header_message ?? 'None'}</span>
        </div>
        <div className="rounded-md bg-muted/65 px-3 py-2">
          <span className="font-medium text-foreground">Promo: </span>
          <span className="text-muted-foreground">{template.promotion_message ?? 'None'}</span>
        </div>
      </div>

      <div className="mt-auto flex flex-wrap gap-2 pt-4">
        <Button size="sm" variant="outline" onClick={onEdit}>
          <Pencil size={13} />
          Edit
        </Button>
        <Button size="sm" disabled={template.is_active || activating} onClick={onActivate}>
          {activating ? <Loader2 size={13} className="animate-spin" /> : <CheckCircle2 size={13} />}
          Set Active
        </Button>
      </div>
    </article>
  )
}

export default function InvoiceTemplates() {
  const qc = useQueryClient()
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<TemplateForm | null>(null)

  const templates = useQuery({
    queryKey: ['invoice-templates'],
    queryFn: listInvoiceTemplates,
  })

  const activeTemplate = useMemo(
    () => templates.data?.find((template) => template.is_active) ?? null,
    [templates.data],
  )
  const editingTemplate = useMemo(
    () => templates.data?.find((template) => template.id === editingId) ?? null,
    [templates.data, editingId],
  )

  useEffect(() => {
    if (editingTemplate) setForm(formFromTemplate(editingTemplate))
  }, [editingTemplate])

  const activateMutation = useMutation({
    mutationFn: activateInvoiceTemplate,
    onSuccess: (template) => {
      qc.invalidateQueries({ queryKey: ['invoice-templates'] })
      toast.success(`${template.name} is now active.`)
    },
    onError: (err) => toast.error(errDetail(err)),
  })

  const copyMutation = useMutation({
    mutationFn: ({ id, body }: { id: number; body: TemplateForm }) => saveInvoiceTemplateCopy(id, body),
    onSuccess: (template) => {
      qc.invalidateQueries({ queryKey: ['invoice-templates'] })
      setEditingId(template.id)
      toast.success('Custom template copy created.')
    },
    onError: (err) => toast.error(errDetail(err)),
  })

  const originalMutation = useMutation({
    mutationFn: ({ id, body }: { id: number; body: TemplateForm }) => saveInvoiceTemplateOriginal(id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoice-templates'] })
      toast.success('Template original updated.')
    },
    onError: (err) => toast.error(errDetail(err)),
  })

  if (templates.isPending) {
    return (
      <div className="flex flex-col gap-6">
        <PageHeader title="Invoice Templates" />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2, 3, 4, 5].map((i) => <CardSkeleton key={i} />)}
        </div>
      </div>
    )
  }
  if (templates.error) return <ErrorState detail={errDetail(templates.error)} />

  function updateField<K extends keyof TemplateForm>(key: K, value: TemplateForm[K]) {
    setForm((current) => current ? { ...current, [key]: value } : current)
  }

  function saveCopy() {
    if (!editingTemplate || !form) return
    copyMutation.mutate({ id: editingTemplate.id, body: form })
  }

  function saveOriginal() {
    if (!editingTemplate || !form) return
    const ok = window.confirm('Save changes to the selected original template? This can affect future generated invoices.')
    if (!ok) return
    originalMutation.mutate({ id: editingTemplate.id, body: form })
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Invoice Templates"
        description="Manage global invoice template metadata used by admin bulk PDF generation."
      />

      <section className="grid gap-4 lg:grid-cols-[0.72fr_0.28fr]">
        <div className="surface-section p-5">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-md bg-primary/10 text-primary">
              <Palette size={18} />
            </div>
            <div>
              <h2 className="text-base font-semibold">Active Template</h2>
              <p className="text-sm text-muted-foreground">
                {activeTemplate ? `${activeTemplate.name} (${activeTemplate.template_code})` : 'No active template selected.'}
              </p>
            </div>
          </div>
        </div>

        <div className="surface-section p-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Templates</p>
          <p className="mt-2 text-3xl font-semibold tabular-nums">{templates.data?.length ?? 0}</p>
          <p className="mt-1 text-sm text-muted-foreground">System and custom templates</p>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1fr_390px]">
        <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
          {(templates.data ?? []).map((template) => (
            <TemplateCard
              key={template.id}
              template={template}
              selected={editingId === template.id}
              onEdit={() => setEditingId(template.id)}
              onActivate={() => activateMutation.mutate(template.id)}
              activating={activateMutation.isPending && activateMutation.variables === template.id}
            />
          ))}
        </div>

        <aside className="surface-section h-fit p-5">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold">Edit Template</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {editingTemplate ? editingTemplate.template_code : 'Select a template to edit messages.'}
              </p>
            </div>
            {editingTemplate && (
              <Button variant="ghost" size="icon" onClick={() => setEditingId(null)} aria-label="Cancel edit">
                <X size={16} />
              </Button>
            )}
          </div>

          {!editingTemplate || !form ? (
            <div className="rounded-md border border-dashed border-border px-3 py-10 text-center text-sm text-muted-foreground">
              Choose a template card to customize header, footer, and promotion text.
            </div>
          ) : (
            <div className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="template-name">Name</Label>
                <Input id="template-name" value={form.name} onChange={(event) => updateField('name', event.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="template-description">Description</Label>
                <textarea
                  id="template-description"
                  value={form.description}
                  onChange={(event) => updateField('description', event.target.value)}
                  className="min-h-20 rounded-md border border-input bg-white px-3 py-2 text-sm outline-none ring-ring/30 focus:ring-2"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="header-message">Header message</Label>
                <textarea
                  id="header-message"
                  value={form.header_message}
                  onChange={(event) => updateField('header_message', event.target.value)}
                  className="min-h-20 rounded-md border border-input bg-white px-3 py-2 text-sm outline-none ring-ring/30 focus:ring-2"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="promotion-message">Promotion message</Label>
                <textarea
                  id="promotion-message"
                  value={form.promotion_message}
                  onChange={(event) => updateField('promotion_message', event.target.value)}
                  className="min-h-20 rounded-md border border-input bg-white px-3 py-2 text-sm outline-none ring-ring/30 focus:ring-2"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="footer-message">Footer message</Label>
                <textarea
                  id="footer-message"
                  value={form.footer_message}
                  onChange={(event) => updateField('footer_message', event.target.value)}
                  className="min-h-20 rounded-md border border-input bg-white px-3 py-2 text-sm outline-none ring-ring/30 focus:ring-2"
                />
              </div>
              <div className="grid gap-3 sm:grid-cols-[1fr_120px]">
                <div className="grid gap-2">
                  <Label htmlFor="theme-name">Theme name</Label>
                  <Input id="theme-name" value={form.theme_name} onChange={(event) => updateField('theme_name', event.target.value)} />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="theme-color">Color</Label>
                  <Input id="theme-color" value={form.theme_color} onChange={(event) => updateField('theme_color', event.target.value)} />
                </div>
              </div>

              <div className="grid gap-2 pt-2 sm:grid-cols-2">
                <Button onClick={saveCopy} disabled={copyMutation.isPending}>
                  {copyMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <Copy size={14} />}
                  Save as Copy
                </Button>
                <Button variant="outline" onClick={saveOriginal} disabled={originalMutation.isPending}>
                  {originalMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                  Save as Original
                </Button>
              </div>
            </div>
          )}
        </aside>
      </section>
    </div>
  )
}
