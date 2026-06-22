import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from './AuthProvider'
import type { Session } from './AuthProvider'

const roleHome: Record<Session['role'], string> = {
  admin: '/admin',
  customer: '/app',
}

interface Props {
  role: Session['role']
}

export default function RequireRole({ role }: Props) {
  const { session } = useAuth()

  if (!session) return <Navigate to="/login" replace />
  if (session.role !== role) return <Navigate to={roleHome[session.role]} replace />
  return <Outlet />
}
