import { createContext, useContext, useState, useEffect } from 'react'
import type { ReactNode } from 'react'
import { clearToken, getToken, authMe } from '../lib/api'

export interface Session {
  role: 'admin' | 'admin1' | 'customer'
  customerId?: number
}

interface AuthContextValue {
  session: Session | null
  isChecking: boolean
  login: (session: Session) => void
  logout: () => void
}

const STORAGE_KEY = 'slt-auth'

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [isChecking, setIsChecking] = useState(() => getToken() !== null)

  useEffect(() => {
    const token = getToken()
    if (!token) {
      localStorage.removeItem(STORAGE_KEY)
      return
    }
    authMe()
      .then((me) => {
        const role = me.role === 'ADMIN' ? 'admin' : me.role === 'ADMIN1' ? 'admin1' : 'customer'
        const verified: Session =
          role === 'customer' && me.customer_id != null
            ? { role: 'customer', customerId: me.customer_id }
            : role === 'admin1'
            ? { role: 'admin1' }
            : { role: 'admin' }
        setSession(verified)
        localStorage.setItem(STORAGE_KEY, JSON.stringify(verified))
      })
      .catch(() => {
        clearToken()
        localStorage.removeItem(STORAGE_KEY)
        setSession(null)
      })
      .finally(() => {
        setIsChecking(false)
      })
  }, [])

  function login(s: Session) {
    setSession(s)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(s))
  }

  function logout() {
    setSession(null)
    localStorage.removeItem(STORAGE_KEY)
    clearToken()
  }

  return (
    <AuthContext.Provider value={{ session, isChecking, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
