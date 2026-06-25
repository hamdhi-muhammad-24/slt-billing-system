import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../auth/AuthProvider'
import { getCustomer } from '../lib/api'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import Brand from './Brand'

function initials(name: string): string {
  return name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase()
}

export default function CustomerLayout() {
  const { session, logout } = useAuth()
  const navigate = useNavigate()
  const customerId = session?.customerId ?? 0

  const { data: customer } = useQuery({
    queryKey: ['customer', customerId],
    queryFn: () => getCustomer(customerId),
    enabled: customerId > 0,
  })

  const displayName = customer?.name ?? `Customer #${customerId}`

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex min-h-svh flex-col bg-background">
      <header className="shrink-0 border-b border-border bg-card shadow-sm">
        <div className="mx-auto flex max-w-6xl items-center gap-5 px-5 py-4 sm:px-6">
          <Brand tone="light" size="md" />

          <NavLink
            to="/app"
            end
            className={({ isActive }) =>
              cn(
                'rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground',
              )
            }
          >
            My Accounts
          </NavLink>

          <span className="flex-1" />

          {/* Avatar + name */}
          <div className="flex items-center gap-2.5">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-primary text-xs font-semibold text-primary-foreground">
              {initials(displayName)}
            </div>
            <span className="hidden text-sm font-medium text-foreground sm:block">{displayName}</span>
          </div>

          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-muted-foreground hover:text-foreground"
            onClick={handleLogout}
          >
            <LogOut size={13} />
            <span className="hidden sm:inline">Logout</span>
          </Button>
        </div>
      </header>

      <main className="flex flex-1 justify-center">
        <div className="w-full max-w-6xl px-5 py-8 sm:px-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
