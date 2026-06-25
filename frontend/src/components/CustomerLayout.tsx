import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { LogOut, Wifi } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../auth/AuthProvider'
import { getCustomer } from '../lib/api'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

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
    <div className="min-h-svh flex flex-col">
      {/* Gradient header */}
      <header className="shrink-0 gradient-hero">
        <div className="max-w-4xl mx-auto px-6 py-5 flex items-center gap-4">
          {/* Brand */}
          <div className="flex items-center gap-2.5 mr-2">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-white/20 backdrop-blur-sm">
              <Wifi size={13} className="text-white" />
            </div>
            <span className="font-bold text-sm text-white tracking-tight">SLT e-Bill</span>
          </div>

          <NavLink
            to="/app"
            end
            className={({ isActive }) =>
              cn(
                'text-sm transition-colors',
                isActive
                  ? 'font-semibold text-white'
                  : 'text-white/60 hover:text-white',
              )
            }
          >
            My Accounts
          </NavLink>

          <span className="flex-1" />

          {/* Avatar + name */}
          <div className="flex items-center gap-2.5">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-white/20 text-white text-xs font-bold backdrop-blur-sm">
              {initials(displayName)}
            </div>
            <span className="hidden sm:block text-sm text-white/90 font-medium">{displayName}</span>
          </div>

          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-white/70 hover:text-white hover:bg-white/10"
            onClick={handleLogout}
          >
            <LogOut size={13} />
            <span className="hidden sm:inline">Logout</span>
          </Button>
        </div>
      </header>

      <main className="flex-1 flex justify-center">
        <div className="w-full max-w-4xl px-6 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
