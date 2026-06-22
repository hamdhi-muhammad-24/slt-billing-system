import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { ChevronDown, LogOut } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../auth/AuthProvider'
import { getCustomer } from '../lib/api'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import Brand from './Brand'

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
      <header className="h-14 shrink-0 border-b bg-background flex items-center gap-6 px-6">
        <Brand />

        <NavLink
          to="/app"
          end
          className={({ isActive }) =>
            cn('text-sm transition-colors', isActive
              ? 'font-semibold text-foreground'
              : 'text-muted-foreground hover:text-foreground')
          }
        >
          My Accounts
        </NavLink>

        <span className="flex-1" />

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="gap-1.5">
              {displayName}
              <ChevronDown size={14} />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuLabel className="text-xs text-muted-foreground font-normal">
              Customer portal
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout}>
              <LogOut size={14} className="mr-2" />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </header>

      <main className="flex-1 flex justify-center">
        <div className="w-full max-w-4xl px-6 py-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
