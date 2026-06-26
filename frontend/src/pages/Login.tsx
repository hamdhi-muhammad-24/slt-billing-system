import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import {
  ArrowLeft,
  ArrowRight,
  BadgeHelp,
  Building2,
  CheckCircle2,
  CreditCard,
  Headphones,
  LockKeyhole,
  ShieldCheck,
  Smartphone,
  UserRound,
} from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import { authLogin, authMe, setToken, ApiError } from '../lib/api'
import Brand from '../components/Brand'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

const ROLE_HOME = { admin: '/admin', customer: '/app' } as const

type GatewayMode = 'customer' | 'staff' | 'otp' | 'quickPay'

const gatewayModes = [
  {
    id: 'customer' as const,
    icon: UserRound,
    title: 'Customer Sign In',
    text: 'View bills, statements, service accounts, and payment history.',
  },
  {
    id: 'staff' as const,
    icon: Building2,
    title: 'Staff/Admin Sign In',
    text: 'Access billing operations, customers, invoices, and reports.',
  },
  {
    id: 'otp' as const,
    icon: Smartphone,
    title: 'View Bill With OTP',
    text: 'Frontend preview for one-time bill access verification.',
  },
  {
    id: 'quickPay' as const,
    icon: CreditCard,
    title: 'Quick Pay',
    text: 'Frontend preview for payment lookup before secure processing.',
  },
]

const trustItems = [
  'Role-based portal access',
  'Customer and admin entry points',
  'Private billing data protected behind sign in',
]

function modeTitle(mode: GatewayMode): string {
  if (mode === 'staff') return 'Staff/Admin Sign In'
  if (mode === 'otp') return 'View Bill With OTP'
  if (mode === 'quickPay') return 'Quick Pay'
  return 'Customer Sign In'
}

function modeDescription(mode: GatewayMode): string {
  if (mode === 'staff') return 'Use authorized SLT-MOBITEL staff credentials to continue.'
  if (mode === 'otp') return 'Enter account details to request a one-time passcode. This is a UI placeholder.'
  if (mode === 'quickPay') return 'Look up a bill for quick payment. This is a UI placeholder.'
  return 'Use registered customer credentials to open your billing workspace.'
}

export default function Login() {
  const { session, isChecking, login } = useAuth()
  const navigate = useNavigate()
  const [activeMode, setActiveMode] = useState<GatewayMode>('customer')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [accountNo, setAccountNo] = useState('')
  const [mobileNo, setMobileNo] = useState('')
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

  function handlePlaceholderSubmit(e: FormEvent) {
    e.preventDefault()
    toast.info('This portal option is a frontend placeholder for now.')
  }

  const isCredentialMode = activeMode === 'customer' || activeMode === 'staff'

  return (
    <main className="min-h-svh bg-[#f4f8fc] text-foreground">
      <header className="border-b border-border/70 bg-white">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <Brand tone="light" size="lg" />
          <Button asChild variant="outline" size="sm" className="shrink-0">
            <Link to="/">
              <ArrowLeft size={14} />
              Portal Home
            </Link>
          </Button>
        </div>
      </header>

      <section className="relative overflow-hidden">
        <div className="absolute inset-x-0 top-0 h-[360px] bg-[#07284d]" />
        <div className="network-grid absolute inset-x-0 top-0 h-[360px] opacity-35" />
        <div className="absolute inset-x-0 top-0 h-[360px] bg-[radial-gradient(circle_at_16%_20%,rgba(73,173,235,0.26),transparent_30%),radial-gradient(circle_at_86%_18%,rgba(78,184,72,0.20),transparent_28%)]" />

        <div className="relative mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
          <div className="mb-8 max-w-3xl text-white">
            <p className="inline-flex items-center gap-2 rounded-md border border-white/20 bg-white/10 px-3 py-1.5 text-sm font-medium text-white/85">
              <ShieldCheck size={15} />
              Secure SLT-MOBITEL portal gateway
            </p>
            <h1 className="mt-5 text-3xl font-semibold tracking-tight sm:text-5xl">
              Choose how you want to continue
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-white/72 sm:text-base">
              Customers can view bills and payment options, while authorized staff can continue to
              billing administration from the same trusted gateway.
            </p>
          </div>

          <div className="grid gap-5 lg:grid-cols-[380px_1fr]">
            <aside className="surface-section overflow-hidden">
              <div className="border-b border-border bg-muted/35 p-5">
                <p className="text-sm font-medium text-muted-foreground">Portal options</p>
                <h2 className="mt-1 text-xl font-semibold">Access gateway</h2>
              </div>

              <div className="grid gap-2 p-3">
                {gatewayModes.map((mode) => {
                  const Icon = mode.icon
                  const isActive = activeMode === mode.id
                  return (
                    <button
                      key={mode.id}
                      type="button"
                      onClick={() => {
                        setActiveMode(mode.id)
                        setError(null)
                      }}
                      className={cn(
                        'grid grid-cols-[42px_1fr] gap-3 rounded-lg border p-3 text-left transition',
                        isActive
                          ? 'border-primary/40 bg-primary/8 shadow-sm'
                          : 'border-transparent hover:border-border hover:bg-muted/40',
                      )}
                    >
                      <span
                        className={cn(
                          'flex size-10 items-center justify-center rounded-md',
                          isActive ? 'bg-primary text-primary-foreground' : 'bg-muted text-primary',
                        )}
                      >
                        <Icon size={18} />
                      </span>
                      <span className="min-w-0">
                        <span className="block text-sm font-semibold">{mode.title}</span>
                        <span className="mt-1 block text-xs leading-5 text-muted-foreground">{mode.text}</span>
                      </span>
                    </button>
                  )
                })}
              </div>
            </aside>

            <section className="grid gap-5 xl:grid-cols-[1fr_320px]">
              <div className="surface-section p-5 sm:p-7">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Selected service</p>
                    <h2 className="mt-1 text-2xl font-semibold tracking-tight">{modeTitle(activeMode)}</h2>
                    <p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">
                      {modeDescription(activeMode)}
                    </p>
                  </div>
                  <div className="hidden size-12 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary sm:flex">
                    {activeMode === 'quickPay' ? <CreditCard size={22} /> : activeMode === 'otp' ? <Smartphone size={22} /> : <LockKeyhole size={22} />}
                  </div>
                </div>

                {isCredentialMode ? (
                  <form onSubmit={handleSubmit} className="mt-7 grid gap-5">
                    <div className="grid gap-2">
                      <Label htmlFor="email" className="text-sm font-medium">Email address</Label>
                      <Input
                        id="email"
                        type="email"
                        autoComplete="username"
                        required
                        placeholder={activeMode === 'staff' ? 'name@slt.lk' : 'name@example.com'}
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="h-11 bg-white"
                      />
                    </div>

                    <div className="grid gap-2">
                      <Label htmlFor="password" className="text-sm font-medium">Password</Label>
                      <Input
                        id="password"
                        type="password"
                        autoComplete="current-password"
                        required
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="h-11 bg-white"
                      />
                    </div>

                    {error && (
                      <div className="rounded-md border border-destructive/20 bg-destructive/5 px-3.5 py-2.5">
                        <p className="text-sm text-destructive" role="alert">{error}</p>
                      </div>
                    )}

                    <Button type="submit" className="h-11 w-full justify-between font-semibold" disabled={loading}>
                      {loading ? (
                        <span className="flex items-center gap-2">
                          <span className="size-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                          Signing in...
                        </span>
                      ) : (
                        <>
                          Continue securely
                          <ArrowRight size={15} />
                        </>
                      )}
                    </Button>
                  </form>
                ) : (
                  <form onSubmit={handlePlaceholderSubmit} className="mt-7 grid gap-5">
                    <div className="grid gap-2">
                      <Label htmlFor="accountNo" className="text-sm font-medium">Account number</Label>
                      <Input
                        id="accountNo"
                        required
                        placeholder="Enter SLT-MOBITEL account number"
                        value={accountNo}
                        onChange={(e) => setAccountNo(e.target.value)}
                        className="h-11 bg-white"
                      />
                    </div>

                    <div className="grid gap-2">
                      <Label htmlFor="mobileNo" className="text-sm font-medium">
                        {activeMode === 'otp' ? 'Mobile number for OTP' : 'Contact mobile number'}
                      </Label>
                      <Input
                        id="mobileNo"
                        required
                        placeholder="07X XXX XXXX"
                        value={mobileNo}
                        onChange={(e) => setMobileNo(e.target.value)}
                        className="h-11 bg-white"
                      />
                    </div>

                    <div className="rounded-md border border-warning/25 bg-warning/10 px-3.5 py-3">
                      <p className="text-sm leading-6 text-warning-foreground">
                        This option is currently a frontend placeholder. Full OTP and quick-pay
                        processing can be connected in a later backend phase.
                      </p>
                    </div>

                    <Button type="submit" className="h-11 w-full justify-between font-semibold">
                      {activeMode === 'otp' ? 'Request OTP' : 'Continue to Quick Pay'}
                      <ArrowRight size={15} />
                    </Button>
                  </form>
                )}
              </div>

              <aside className="surface-section p-5">
                <div className="flex items-center gap-3">
                  <div className="flex size-11 items-center justify-center rounded-md bg-success/10 text-success">
                    <CheckCircle2 size={20} />
                  </div>
                  <div>
                    <h2 className="font-semibold">Trusted gateway</h2>
                    <p className="text-sm text-muted-foreground">Designed for public portal entry</p>
                  </div>
                </div>

                <div className="mt-5 grid gap-3">
                  {trustItems.map((item) => (
                    <div key={item} className="flex gap-3 rounded-md border border-border bg-muted/25 p-3 text-sm">
                      <ShieldCheck size={16} className="mt-0.5 shrink-0 text-primary" />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>

                <div className="mt-5 rounded-md bg-[#eef6ff] p-4">
                  <div className="flex items-center gap-2 text-sm font-semibold text-[#0b3a67]">
                    <BadgeHelp size={16} />
                    Need help signing in?
                  </div>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    Use support if you cannot access your customer account or staff billing console.
                  </p>
                  <Button asChild variant="outline" size="sm" className="mt-4 w-full justify-between bg-white">
                    <a href="mailto:support@slt.lk">
                      Contact support
                      <Headphones size={14} />
                    </a>
                  </Button>
                </div>
              </aside>
            </section>
          </div>
        </div>
      </section>
    </main>
  )
}
