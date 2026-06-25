import { useState } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthProvider'
import { authLogin, authMe, setToken } from '../lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { ApiError } from '../lib/api'
import { Wifi, Shield, Zap, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'

const ROLE_HOME = { admin: '/admin', customer: '/app' } as const

const STAT_PILLS = [
  { icon: Shield, label: '99.9% uptime' },
  { icon: Zap,    label: 'Instant PDF' },
  { icon: Clock,  label: 'Real-time billing' },
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
      const s =
        role === 'customer' && me.customer_id != null
          ? { role: 'customer' as const, customerId: me.customer_id }
          : { role: 'admin' as const }
      login(s)
      navigate(role === 'admin' ? '/admin' : '/app', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-svh">
      {/* Left hero panel */}
      <div className="hidden lg:flex flex-col justify-between w-[46%] shrink-0 gradient-hero p-10 relative overflow-hidden">
        {/* Decorative blobs */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute -top-20 -left-20 size-72 rounded-full bg-white/5 blur-3xl" />
          <div className="absolute top-1/3 -right-16 size-56 rounded-full bg-white/10 blur-2xl" />
          <div className="absolute -bottom-16 left-1/4 size-64 rounded-full bg-white/4 blur-3xl" />
        </div>

        {/* Brand badge */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm shadow-lg">
            <Wifi size={16} className="text-white" />
          </div>
          <div>
            <p className="text-white font-bold text-sm leading-none">SLT e-Bill</p>
            <p className="text-white/50 text-xs mt-0.5">Sri Lanka Telecom</p>
          </div>
        </div>

        {/* Main copy */}
        <div className="relative z-10 flex flex-col gap-5">
          <h1 className="text-4xl font-bold text-white leading-tight">
            Your telecom bills,<br />
            <span className="text-white/70">beautifully managed.</span>
          </h1>
          <p className="text-white/60 text-sm leading-relaxed max-w-xs">
            Generate, view, and download SLT invoice PDFs — for every account, every period, in seconds.
          </p>
          <div className="flex flex-wrap gap-2 mt-1">
            {STAT_PILLS.map(({ icon: Icon, label }) => (
              <div
                key={label}
                className="flex items-center gap-1.5 rounded-full bg-white/10 border border-white/15 px-3 py-1.5 text-xs text-white/80 backdrop-blur-sm"
              >
                <Icon size={11} />
                {label}
              </div>
            ))}
          </div>
        </div>

        {/* Footer note */}
        <p className="relative z-10 text-white/30 text-xs">
          © {new Date().getFullYear()} Sri Lanka Telecom PLC
        </p>
      </div>

      {/* Right auth panel */}
      <div className="flex flex-1 items-center justify-center bg-background p-6">
        <div className="w-full max-w-sm flex flex-col gap-8">
          {/* Mobile brand */}
          <div className="flex items-center gap-2.5 lg:hidden">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-lg gradient-primary shadow-sm">
              <Wifi size={13} className="text-white" />
            </div>
            <span className="font-bold text-sm tracking-tight">SLT e-Bill</span>
          </div>

          <div className="flex flex-col gap-1">
            <h2 className="text-2xl font-bold tracking-tight">Sign in</h2>
            <p className="text-sm text-muted-foreground">Enter your credentials to access your portal.</p>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div className="flex flex-col gap-2">
              <Label htmlFor="email" className="text-sm font-medium">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="username"
                required
                placeholder="you@slt.lk"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={cn(
                  'h-10 transition-shadow',
                  'focus-visible:ring-2 focus-visible:ring-primary/40',
                )}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="password" className="text-sm font-medium">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={cn(
                  'h-10 transition-shadow',
                  'focus-visible:ring-2 focus-visible:ring-primary/40',
                )}
              />
            </div>

            {error && (
              <div className="rounded-lg bg-destructive/5 border border-destructive/20 px-3.5 py-2.5">
                <p className="text-sm text-destructive" role="alert">{error}</p>
              </div>
            )}

            <Button
              type="submit"
              className="w-full h-10 font-semibold relative overflow-hidden"
              disabled={loading}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="size-3.5 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                  Signing in…
                </span>
              ) : (
                'Sign in'
              )}
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
