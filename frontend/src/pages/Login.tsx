import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { FileText, LockKeyhole, Server, ShieldCheck } from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import { authLogin, authMe, setToken, ApiError } from '../lib/api'
import Brand from '../components/Brand'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

const ROLE_HOME = { admin: '/admin', customer: '/app' } as const

const CAPABILITIES = [
  { icon: FileText, label: 'Invoice generation' },
  { icon: Server, label: 'Billing operations' },
  { icon: ShieldCheck, label: 'Role based access' },
]

export default function Login() {
  const { session, isChecking, login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (isChecking) return null
  if (session) return <Navigate to={ROLE_HOME[session.role]} replace />

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const { access_token } = await authLogin(email, password)
      setToken(access_token)
      const me = await authMe()
      const role = me.role === 'ADMIN' ? 'admin' : 'customer'
      const nextSession =
        role === 'customer' && me.customer_id != null
          ? { role: 'customer' as const, customerId: me.customer_id }
          : { role: 'admin' as const }
      login(nextSession)
      navigate(role === 'admin' ? '/admin' : '/app', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-svh bg-background">
      <aside className="network-grid hidden w-[47%] shrink-0 flex-col justify-between gradient-hero p-10 lg:flex">
        <Brand tone="dark" size="lg" />

        <div className="flex max-w-md flex-col gap-6">
          <div className="inline-flex w-fit items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-xs font-medium text-white/80">
            <LockKeyhole size={13} />
            Authorized access only
          </div>

          <div className="flex flex-col gap-4">
            <h1 className="text-4xl font-semibold leading-tight text-white">
              Billing management for national telecom operations.
            </h1>
            <p className="text-sm leading-6 text-white/70">
              Generate SLT-MOBITEL invoices, review customer accounts, download PDFs,
              and manage monthly billing runs from one secure workspace.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {CAPABILITIES.map(({ icon: Icon, label }) => (
              <div
                key={label}
                className="flex items-center gap-1.5 rounded-md border border-white/15 bg-white/10 px-3 py-2 text-xs text-white/82"
              >
                <Icon size={13} />
                {label}
              </div>
            ))}
          </div>
        </div>

        <p className="text-xs text-white/45">
          Sri Lanka Telecom PLC | Internal billing platform | {new Date().getFullYear()}
        </p>
      </aside>

      <main className="flex flex-1 items-center justify-center p-6">
        <div className="w-full max-w-[400px]">
          <div className="surface-card flex flex-col gap-7 p-7">
            <Brand tone="light" size="md" className="lg:hidden" />

            <div className="flex flex-col gap-1.5">
              <h2 className="text-2xl font-semibold tracking-tight">Sign in</h2>
              <p className="text-sm leading-6 text-muted-foreground">
                Use your SLT-MOBITEL billing credentials to continue.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-5">
              <div className="flex flex-col gap-2">
                <Label htmlFor="email" className="text-sm font-medium">Email</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="username"
                  required
                  placeholder="name@slt.lk"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={cn('h-10 bg-white transition-shadow focus-visible:ring-2 focus-visible:ring-primary/35')}
                />
              </div>

              <div className="flex flex-col gap-2">
                <Label htmlFor="password" className="text-sm font-medium">Password</Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={cn('h-10 bg-white transition-shadow focus-visible:ring-2 focus-visible:ring-primary/35')}
                />
              </div>

              {error && (
                <div className="rounded-md border border-destructive/20 bg-destructive/5 px-3.5 py-2.5">
                  <p className="text-sm text-destructive" role="alert">{error}</p>
                </div>
              )}

              <Button type="submit" className="h-10 w-full font-semibold" disabled={loading}>
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="size-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                    Signing in...
                  </span>
                ) : (
                  'Sign in'
                )}
              </Button>
            </form>

            <p className="border-t border-border pt-4 text-xs leading-5 text-muted-foreground">
              Access is restricted to authorized SLT-MOBITEL staff and registered customer users.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
