import { ChevronRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'

export interface Breadcrumb {
  label: string
  to?: string
}

interface Props {
  title: string
  description?: string
  breadcrumbs?: Breadcrumb[]
  actions?: ReactNode
}

export function PageHeader({ title, description, breadcrumbs, actions }: Props) {
  return (
    <div className="mb-6 flex flex-col gap-4 border-b border-border/80 pb-5 sm:flex-row sm:items-end sm:justify-between">
      <div className="flex min-w-0 flex-col gap-2">
        {breadcrumbs && breadcrumbs.length > 0 && (
          <nav className="flex flex-wrap items-center gap-1 text-xs font-medium text-muted-foreground">
            {breadcrumbs.map((crumb, i) => (
              <span key={i} className="flex items-center gap-1">
                {i > 0 && <ChevronRight size={11} className="text-muted-foreground/40 shrink-0" />}
                {crumb.to
                  ? <Link to={crumb.to} className="transition-colors hover:text-primary">{crumb.label}</Link>
                  : <span className="text-foreground/70">{crumb.label}</span>
                }
              </span>
            ))}
          </nav>
        )}
        <h1 className="text-2xl font-extrabold tracking-tight bg-gradient-to-r from-slate-900 via-blue-900 to-blue-600 dark:from-slate-100 dark:via-blue-100 dark:to-blue-400 bg-clip-text text-transparent sm:text-[1.85rem]">{title}</h1>
        {description && <p className="max-w-2xl text-sm leading-6 text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  )
}
