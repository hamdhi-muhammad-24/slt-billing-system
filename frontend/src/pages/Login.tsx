import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Bot,
  Building2,
  CheckCircle2,
  Download,
  Eye,
  EyeOff,
  Headphones,
  LockKeyhole,
  ShieldCheck,
  UserRound,
} from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import { authLogin, authMe, setToken, clearToken } from '../lib/api'
import Brand from '../components/Brand'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

const ROLE_HOME = { admin: '/admin', admin1: '/admin1', customer: '/app' } as const

type GatewayMode = 'customer' | 'staff'

const roleTabs = [
  {
    id: 'customer' as const,
    icon: UserRound,
    label: 'Customer',
  },
  {
    id: 'staff' as const,
    icon: Building2,
    label: 'Staff/Admin',
  },
]

const trustItems = [
  {
    icon: ShieldCheck,
    label: 'Role-Based Authentication',
  },
  {
    icon: Bot,
    label: 'AI-Generated Invoices',
  },
  {
    icon: Download,
    label: 'Secure PDF Statements',
  },
]

function modeSubtitle(mode: GatewayMode): string {
  if (mode === 'staff') return 'Use authorized staff credentials to manage billing generation and GMF operations securely.'
  return 'Use registered customer credentials to view your AI-generated billing statements.'
}

export default function Login() {
  const { session, isChecking, login } = useAuth()
  const navigate = useNavigate()
  const [activeMode, setActiveMode] = useState<GatewayMode>('customer')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (isChecking) return null
  if (session) return <Navigate to={ROLE_HOME[session.role]} replace />

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const { access_token } = await authLogin(email, password)
      setToken(access_token)
      const me = await authMe()
      const role = me.role === 'ADMIN' ? 'admin' : me.role === 'ADMIN1' ? 'admin1' : 'customer'

      if (activeMode === 'staff' && role !== 'admin' && role !== 'admin1') {
        clearToken()
        setError('These credentials are not authorised for staff access. Please use the Customer portal.')
        return
      }
      if (activeMode === 'customer' && role !== 'customer') {
        clearToken()
        setError('Staff accounts must sign in through the Staff / Admin portal.')
        return
      }

      const nextSession =
        role === 'customer' && me.customer_id != null
          ? { role: 'customer' as const, customerId: me.customer_id }
          : role === 'admin1'
          ? { role: 'admin1' as const }
          : { role: 'admin' as const }
      login(nextSession)
      navigate(role === 'admin1' ? '/admin1' : role === 'admin' ? '/admin' : '/app', { replace: true })
    } catch (err: any) {
      console.error("Login error:", err)
      setError(err?.detail || err?.message || 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-svh overflow-hidden bg-background text-foreground relative selection:bg-primary/20 selection:text-primary">
      {/* Global Background Ambient Effects */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden z-0">
        <div className="absolute -left-[10%] -top-[10%] size-[500px] rounded-full bg-blue-500/10 blur-[120px] dark:bg-blue-600/15" />
        <div className="absolute -right-[10%] top-[20%] size-[600px] rounded-full bg-indigo-500/10 blur-[120px] dark:bg-indigo-600/15" />
        <div className="absolute bottom-[-20%] left-[20%] size-[800px] rounded-full bg-emerald-500/10 blur-[150px] dark:bg-emerald-600/10" />
      </div>

      <header className="relative z-20 border-b border-border/50 bg-background/75 shadow-sm backdrop-blur-xl">
        <div className="mx-auto flex min-h-18 max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
          <Brand size="md" />
          <Button asChild variant="outline" size="sm" className="h-9 shrink-0 border-border bg-background px-4 text-foreground shadow-sm hover:border-primary/40 hover:bg-muted transition-all">
            <Link to="/">
              <ArrowLeft size={14} className="mr-2" />
              <span className="hidden sm:inline">Back to Portal</span>
              <span className="sm:hidden">Portal</span>
            </Link>
          </Button>
        </div>
      </header>

      <section className="relative z-10">
        <div className="absolute inset-x-0 top-0 h-80 bg-gradient-to-b from-primary/10 via-background to-background dark:from-primary/5" />
        
        <div className="relative mx-auto grid max-w-6xl gap-6 px-4 py-8 sm:px-6 sm:py-12 lg:grid-cols-[minmax(0,1fr)_440px] lg:items-stretch lg:px-8 lg:py-16">
          <section className="glass-card relative overflow-hidden rounded-[2rem] p-6 shadow-2xl sm:p-10 lg:min-h-[660px]">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-indigo-600/5" />
            <div className="absolute inset-0 opacity-[0.03] dark:opacity-[0.05] [background-image:radial-gradient(var(--foreground)_1px,transparent_1px)] [background-size:24px_24px]" />
            <div className="relative flex h-full flex-col">
              <p className="inline-flex max-w-full items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3.5 py-1.5 text-sm font-medium text-primary shadow-sm backdrop-blur-md">
                <ShieldCheck size={16} />
                <span className="min-w-0">Secure SLT-MOBITEL Smart Gateway</span>
              </p>

              <div className="mt-10 max-w-xl sm:mt-12 lg:mt-20">
                <h1 className="text-4xl font-extrabold tracking-tight leading-[1.1] sm:text-5xl lg:text-6xl bg-gradient-to-br from-foreground to-foreground/70 bg-clip-text text-transparent">
                  Sign in to your AI Billing Workspace
                </h1>
                <p className="mt-6 text-lg leading-relaxed text-muted-foreground">
                  Access your intelligent billing dashboard. Customers can view generated invoices, while authorized staff can securely manage massive GMF cycle runs.
                </p>
              </div>

              <div className="mt-10 grid gap-3 sm:max-w-md">
                {trustItems.map((item) => {
                  const Icon = item.icon
                  return (
                    <div key={item.label} className="flex items-center gap-4 rounded-xl border border-border/50 bg-background/50 px-4 py-3.5 text-sm shadow-sm backdrop-blur transition-colors hover:border-primary/30 hover:bg-muted/50">
                      <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
                        <Icon size={18} />
                      </span>
                      <span className="font-semibold text-foreground">{item.label}</span>
                    </div>
                  )
                })}
              </div>

              <div className="mt-auto hidden pt-12 lg:block">
                <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-5 shadow-sm backdrop-blur">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 text-sm font-bold text-emerald-600 dark:text-emerald-400">
                        <CheckCircle2 size={18} className="text-emerald-500" />
                        Secure Billing Session Active
                      </div>
                      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                        Customer self-care and staff cycle generation share one protected, encrypted gateway.
                      </p>
                    </div>
                    <div className="hidden rounded-xl border border-border bg-background p-3 text-right shadow-sm sm:block">
                      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Connection</p>
                      <p className="mt-1 text-sm font-bold text-emerald-500">Encrypted</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <Card className="glass-card rounded-[2rem] py-0 shadow-2xl relative overflow-hidden border-border/50">
            <div className="absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r from-blue-600 to-indigo-600" />
            <CardContent className="p-6 sm:p-8 flex flex-col h-full">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-primary">Smart Billing Login</p>
                  <h2 className="mt-2 text-3xl font-extrabold text-foreground">Welcome Back</h2>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{modeSubtitle(activeMode)}</p>
                </div>
                <div className="hidden size-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-lg sm:flex">
                  <LockKeyhole size={22} />
                </div>
              </div>

              <div className="mt-8 grid grid-cols-2 gap-2 rounded-xl border border-border bg-muted/30 p-1.5 shadow-inner">
                {roleTabs.map((tab) => {
                  const Icon = tab.icon
                  const isActive = activeMode === tab.id
                  return (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => {
                        setActiveMode(tab.id)
                        setError(null)
                      }}
                      className={cn(
                        'inline-flex h-11 min-w-0 items-center justify-center gap-2.5 rounded-lg px-2 text-sm font-bold transition-all sm:px-3',
                        isActive
                          ? 'bg-background text-foreground shadow-sm ring-1 ring-border'
                          : 'text-muted-foreground hover:bg-background/50 hover:text-foreground',
                      )}
                    >
                      <Icon size={18} />
                      {tab.label}
                    </button>
                  )
                })}
              </div>

              <form onSubmit={handleSubmit} className="mt-8 grid gap-5 flex-1">
                <div className="grid gap-2">
                  <Label htmlFor="email" className="text-sm font-semibold text-foreground">
                    Email address
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    autoComplete="username"
                    required
                    placeholder={activeMode === 'staff' ? 'name@slt.lk' : 'name@example.com'}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="h-12 border-border bg-background text-foreground shadow-sm focus-visible:border-primary focus-visible:ring-primary/25 rounded-xl transition-all"
                  />
                </div>

                <div className="grid gap-2">
                  <div className="flex items-center justify-between gap-3">
                    <Label htmlFor="password" className="text-sm font-semibold text-foreground">
                      Password
                    </Label>
                    <a
                      href="mailto:support@slt.lk?subject=Billing%20portal%20password%20help"
                      className="text-xs font-semibold text-primary hover:underline"
                    >
                      Need help signing in?
                    </a>
                  </div>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      autoComplete="current-password"
                      required
                      placeholder="Password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="h-12 border-border bg-background text-foreground shadow-sm focus-visible:border-primary focus-visible:ring-primary/25 rounded-xl transition-all"
                    />
                    <button
                      type="button"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      onClick={() => setShowPassword((value) => !value)}
                      className="absolute right-2 top-1/2 flex size-8 -translate-y-1/2 items-center justify-center rounded-lg text-muted-foreground transition hover:bg-muted hover:text-foreground"
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>

                {error && (
                  <div className="flex gap-3 rounded-xl border border-destructive/25 bg-destructive/10 px-4 py-3">
                    <AlertCircle size={18} className="mt-0.5 shrink-0 text-destructive" />
                    <p className="text-sm leading-relaxed text-destructive font-medium" role="alert">
                      {error}
                    </p>
                  </div>
                )}

                <Button type="submit" className="mt-2 h-12 w-full justify-between bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 px-5 font-bold text-white shadow-md hover:shadow-lg active:translate-y-px border-none transition-all rounded-xl" disabled={loading}>
                  {loading ? (
                    <span className="flex items-center gap-2.5">
                      <span className="size-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                      Authenticating...
                    </span>
                  ) : (
                    <>
                      Enter Workspace
                      <ArrowRight size={18} />
                    </>
                  )}
                </Button>
              </form>

              <div className="mt-8 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 shadow-sm">
                <div className="flex gap-3.5">
                  <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-background text-emerald-500 shadow-sm ring-1 ring-border">
                    <CheckCircle2 size={20} />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-foreground">Protected access</p>
                    <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                      Your AI-generated billing information and network access is protected by enterprise-grade encryption.
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex flex-col gap-2 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between border-t border-border pt-6">
                <span>Access denied?</span>
                <a href="mailto:support@slt.lk" className="inline-flex items-center gap-2 font-bold text-primary hover:text-primary/80 transition-colors">
                  Contact Support
                  <Headphones size={16} />
                </a>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  )
}
