import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Users, Receipt, Menu, LogOut } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../auth/AuthProvider'
import { authMe } from '../lib/api'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'
import Brand from './Brand'

interface NavItem {
  to: string
  label: string
  icon: LucideIcon
  end: boolean
  pill: string
}

const NAV_ITEMS: NavItem[] = [
  { to: '/admin',           label: 'Dashboard', icon: LayoutDashboard, end: true,  pill: 'bg-blue-500/20 text-blue-300'   },
  { to: '/admin/customers', label: 'Customers', icon: Users,           end: false, pill: 'bg-violet-500/20 text-violet-300' },
  { to: '/admin/billing',   label: 'Billing',   icon: Receipt,         end: false, pill: 'bg-emerald-500/20 text-emerald-300' },
]

function SidebarNav({ onNav }: { onNav?: () => void }) {
  return (
    <nav className="flex flex-col gap-0.5 p-2 flex-1">
      {NAV_ITEMS.map(({ to, label, icon: Icon, end, pill }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onNav}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors',
              isActive
                ? 'bg-sidebar-accent text-sidebar-accent-foreground font-medium'
                : 'text-sidebar-foreground/60 hover:text-sidebar-foreground hover:bg-sidebar-accent/40',
            )
          }
        >
          {({ isActive }) => (
            <>
              <span className={cn('flex size-6 shrink-0 items-center justify-center rounded-md', isActive ? pill : 'bg-white/5 text-sidebar-foreground/50')}>
                <Icon size={13} />
              </span>
              {label}
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}

function SidebarFrame({ email, onNav }: { email?: string; onNav?: () => void }) {
  const initials = email ? email.slice(0, 2).toUpperCase() : 'AD'

  return (
    <div className="flex flex-col h-full bg-sidebar text-sidebar-foreground">
      <div className="h-14 flex items-center px-4 border-b border-sidebar-border shrink-0">
        <Brand />
      </div>

      <SidebarNav onNav={onNav} />

      {/* Avatar badge at bottom */}
      <div className="shrink-0 p-3 border-t border-sidebar-border">
        <div className="flex items-center gap-2.5 px-1 py-1">
          <div className="flex size-7 shrink-0 items-center justify-center rounded-full gradient-primary text-white text-xs font-bold">
            {initials}
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-xs font-medium text-sidebar-foreground truncate">
              {email ?? 'Administrator'}
            </span>
            <span className="inline-flex w-fit items-center rounded-full bg-blue-500/20 text-blue-300 px-1.5 py-px text-[10px] font-medium mt-0.5">
              Admin
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function AdminLayout() {
  const [sheetOpen, setSheetOpen] = useState(false)
  const { logout } = useAuth()
  const navigate = useNavigate()

  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: authMe,
    staleTime: Infinity,
  })

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-svh">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex flex-col w-56 shrink-0 border-r border-sidebar-border">
        <SidebarFrame email={me?.email} />
      </aside>

      {/* Mobile sidebar sheet */}
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent side="left" className="p-0 w-56">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <SidebarFrame email={me?.email} onNav={() => setSheetOpen(false)} />
        </SheetContent>
      </Sheet>

      {/* Main column */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Top bar */}
        <header className="h-14 shrink-0 flex items-center gap-3 px-4 bg-background border-b border-border/60"
          style={{ boxShadow: 'inset 0 -1px 0 oklch(0.40 0.145 258 / 12%)' }}
        >
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setSheetOpen(true)}
            aria-label="Open navigation"
          >
            <Menu size={20} />
          </Button>

          <span className="flex-1" />

          {me?.email && (
            <span className="hidden sm:block text-xs text-muted-foreground">{me.email}</span>
          )}

          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-muted-foreground hover:text-foreground"
            onClick={handleLogout}
          >
            <LogOut size={14} />
            Logout
          </Button>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
