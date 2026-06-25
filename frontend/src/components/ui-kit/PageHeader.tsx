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
    <div className="flex items-start justify-between gap-4 mb-6">
      <div className="flex flex-col gap-1.5">
        {breadcrumbs && breadcrumbs.length > 0 && (
          <nav className="flex items-center gap-1 text-xs text-muted-foreground">
            {breadcrumbs.map((crumb, i) => (
              <span key={i} className="flex items-center gap-1">
                {i > 0 && <ChevronRight size={11} className="text-muted-foreground/40 shrink-0" />}
                {crumb.to
                  ? <Link to={crumb.to} className="hover:text-foreground transition-colors">{crumb.label}</Link>
                  : <span className="text-foreground/70">{crumb.label}</span>
                }
              </span>
            ))}
          </nav>
        )}
        <h1 className="text-2xl font-bold tracking-tight relative inline-block after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-full after:rounded-full after:gradient-primary after:opacity-50">{title}</h1>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="shrink-0">{actions}</div>}
    </div>
  )
}
