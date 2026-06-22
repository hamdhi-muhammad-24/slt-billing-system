import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthProvider'
import { Button } from '@/components/ui/button'

const navLinks = [
  { to: '/admin', label: 'Dashboard', end: true },
  { to: '/admin/customers', label: 'Customers', end: false },
  { to: '/admin/billing', label: 'Billing', end: false },
]

export default function AdminLayout() {
  const { logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-svh flex flex-col">
      <nav className="border-b bg-background px-6 py-3 flex items-center gap-6">
        <span className="font-semibold text-sm">SLT Admin</span>
        <div className="flex items-center gap-4 flex-1">
          {navLinks.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `text-sm ${isActive ? 'font-semibold text-foreground' : 'text-muted-foreground hover:text-foreground'}`
              }
            >
              {label}
            </NavLink>
          ))}
        </div>
        <Button variant="outline" size="sm" onClick={handleLogout}>
          Logout
        </Button>
      </nav>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  )
}
