import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
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
import { authLogin, authMe, setToken, clearToken, ApiError } from '../lib/api'
import Brand from '../components/Brand'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

const ROLE_HOME = { admin: '/admin', customer: '/app' } as const

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
    label: 'Role-based access',
  },
  {
    icon: LockKeyhole,
    label: 'Protected billing data',
  },
  {
    icon: Download,
    label: 'Secure PDF bill downloads',
  },
]

function modeSubtitle(mode: GatewayMode): string {
  if (mode === 'staff') return 'Use authorized staff credentials to manage billing operations securely.'
  return 'Use registered customer credentials to open your billing workspace.'
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
      const role = me.role === 'ADMIN' ? 'admin' : 'customer'

      if (activeMode === 'staff' && role !== 'admin') {
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
          : { role: 'admin' as const }
      login(nextSession)
      navigate(role === 'admin' ? '/admin' : '/app', { replace: true })
    } catch (err: any) {
      console.error("Login error:", err)
      setError(err?.detail || err?.message || 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-svh overflow-hidden bg-[#F3F8FD] text-[#0B1F33]">
      <header className="relative z-20 border-b border-[#DCE8F2] bg-white/90 shadow-[0_4px_24px_rgba(6,43,85,0.05)] backdrop-blur-xl">
        <div className="mx-auto flex min-h-18 max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
          <Brand tone="light" size="md" />
          <Button asChild variant="outline" size="sm" className="h-9 shrink-0 border-[#CADAEA] bg-white px-3 text-[#05264A] shadow-sm hover:border-[#0066B3]/35 hover:bg-[#F4F8FB] hover:text-[#0066B3]">
            <Link to="/">
              <ArrowLeft size={14} />
              <span className="hidden sm:inline">Back to Portal</span>
              <span className="sm:hidden">Portal</span>
            </Link>
          </Button>
        </div>
      </header>

      <section className="relative">
        <div className="absolute inset-x-0 top-0 h-80 bg-[linear-gradient(135deg,#05264A_0%,#063B73_52%,#0066B3_100%)]" />
        <div className="absolute inset-x-0 top-0 h-80 bg-[radial-gradient(circle_at_16%_18%,rgba(14,165,233,0.30),transparent_34%),radial-gradient(circle_at_86%_12%,rgba(57,181,74,0.18),transparent_28%)]" />
        <div className="absolute inset-x-0 top-0 h-80 opacity-25 [background-image:linear-gradient(rgba(255,255,255,0.14)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.14)_1px,transparent_1px)] [background-size:42px_42px]" />
        <div className="absolute inset-x-0 top-80 h-56 bg-[linear-gradient(180deg,rgba(243,248,253,0),#F3F8FD_72%)]" />

        <div className="relative mx-auto grid max-w-6xl gap-5 px-4 py-8 sm:px-6 sm:py-10 lg:grid-cols-[minmax(0,1fr)_430px] lg:items-stretch lg:px-8 lg:py-14">
          <section className="relative overflow-hidden rounded-lg border border-white/16 bg-[linear-gradient(145deg,rgba(5,38,74,0.98),rgba(6,59,115,0.96)_48%,rgba(0,102,179,0.90))] p-5 text-white shadow-[0_28px_80px_rgba(6,43,85,0.26)] sm:p-8 lg:min-h-[620px]">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_14%_12%,rgba(14,165,233,0.25),transparent_34%),radial-gradient(circle_at_92%_88%,rgba(57,181,74,0.16),transparent_32%)]" />
            <div className="absolute inset-0 opacity-20 [background-image:linear-gradient(rgba(255,255,255,0.12)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.12)_1px,transparent_1px)] [background-size:38px_38px]" />
            <div className="relative flex h-full flex-col">
              <p className="inline-flex max-w-full items-center gap-2 rounded-md border border-white/18 bg-white/12 px-3 py-1.5 text-sm font-medium text-white/90 shadow-[0_12px_30px_rgba(0,0,0,0.16)] backdrop-blur-md">
                <ShieldCheck size={15} />
                <span className="min-w-0">Secure SLT-MOBITEL portal gateway</span>
              </p>

              <div className="mt-8 max-w-xl sm:mt-10 lg:mt-16">
                <h1 className="text-3xl font-semibold leading-[1.08] sm:text-5xl">
                  Sign in to your billing workspace
                </h1>
                <p className="mt-5 text-base leading-7 text-white/76">
                  Customers can view invoices and payment history, while authorized staff can manage
                  billing operations securely.
                </p>
              </div>

              <div className="mt-8 grid gap-3 sm:max-w-lg">
                {trustItems.map((item) => {
                  const Icon = item.icon
                  return (
                    <div key={item.label} className="flex items-center gap-3 rounded-md border border-white/14 bg-white/10 px-3.5 py-3 text-sm text-white/88 shadow-sm backdrop-blur">
                      <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-white text-[#0066B3] shadow-[0_10px_24px_rgba(255,255,255,0.14)]">
                        <Icon size={17} />
                      </span>
                      <span className="font-medium">{item.label}</span>
                    </div>
                  )
                })}
              </div>

              <div className="mt-auto hidden pt-10 lg:block">
                <div className="rounded-lg border border-white/14 bg-white/10 p-4 shadow-[0_18px_50px_rgba(0,0,0,0.14)] backdrop-blur">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 text-sm font-semibold text-white">
                        <CheckCircle2 size={16} className="text-[#6FE17D]" />
                        Secure billing summary
                      </div>
                      <p className="mt-2 text-sm leading-6 text-white/68">
                        Customer self-care and staff billing operations share one protected gateway.
                      </p>
                    </div>
                    <div className="hidden rounded-md border border-white/10 bg-white/10 p-3 text-right sm:block">
                      <p className="text-xs text-white/55">Session</p>
                      <p className="mt-1 text-sm font-semibold text-[#8CF09B]">Encrypted</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <Card className="rounded-lg border border-[#D8E6F2] bg-white/95 py-0 shadow-[0_28px_80px_rgba(6,43,85,0.16)] backdrop-blur">
            <CardContent className="p-5 sm:p-7">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold uppercase text-[#0066B3]">Billing portal login</p>
                  <h2 className="mt-2 text-3xl font-semibold text-[#0B1F33]">Welcome back</h2>
                  <p className="mt-2 text-sm leading-6 text-[#52677A]">{modeSubtitle(activeMode)}</p>
                </div>
                <div className="hidden size-12 shrink-0 items-center justify-center rounded-md bg-[linear-gradient(135deg,#EAF4FF,#EAF8EE)] text-[#0066B3] ring-1 ring-[#0066B3]/10 sm:flex">
                  <LockKeyhole size={21} />
                </div>
              </div>

              <div className="mt-6 grid grid-cols-2 gap-2 rounded-lg border border-[#DDE8F1] bg-[linear-gradient(135deg,#F3F8FD,#FFFFFF)] p-1 shadow-inner">
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
                        'inline-flex h-10 min-w-0 items-center justify-center gap-2 rounded-md px-2 text-sm font-semibold transition sm:px-3',
                        isActive
                          ? 'bg-white text-[#05264A] shadow-[0_10px_24px_rgba(6,43,85,0.10)] ring-1 ring-[#CADAEA]'
                          : 'text-[#52677A] hover:bg-white/75 hover:text-[#05264A]',
                      )}
                    >
                      <Icon size={16} />
                      {tab.label}
                    </button>
                  )
                })}
              </div>

              <form onSubmit={handleSubmit} className="mt-7 grid gap-5">
                <div className="grid gap-2">
                  <Label htmlFor="email" className="text-sm font-medium text-[#0B1F33]">
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
                    className="h-11 border-[#CADAEA] bg-white text-[#0B1F33] shadow-sm placeholder:text-[#8CA1B4] focus-visible:border-[#0066B3] focus-visible:ring-[#0EA5E9]/25"
                  />
                </div>

                <div className="grid gap-2">
                  <div className="flex items-center justify-between gap-3">
                    <Label htmlFor="password" className="text-sm font-medium text-[#0B1F33]">
                      Password
                    </Label>
                    <a
                      href="mailto:support@slt.lk?subject=Billing%20portal%20password%20help"
                      className="text-xs font-semibold text-[#0066B3] hover:text-[#05264A]"
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
                      className="h-11 border-[#CADAEA] bg-white pr-11 text-[#0B1F33] shadow-sm placeholder:text-[#8CA1B4] focus-visible:border-[#0066B3] focus-visible:ring-[#0EA5E9]/25"
                    />
                    <button
                      type="button"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      onClick={() => setShowPassword((value) => !value)}
                      className="absolute right-2 top-1/2 flex size-8 -translate-y-1/2 items-center justify-center rounded-md text-[#536B7D] transition hover:bg-[#F4F8FB] hover:text-[#062B55]"
                    >
                      {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                    </button>
                  </div>
                </div>

                {error && (
                  <div className="flex gap-3 rounded-md border border-destructive/25 bg-destructive/5 px-3.5 py-3">
                    <AlertCircle size={17} className="mt-0.5 shrink-0 text-destructive" />
                    <p className="text-sm leading-6 text-destructive" role="alert">
                      {error}
                    </p>
                  </div>
                )}

                <Button type="submit" className="h-11 w-full justify-between bg-[linear-gradient(135deg,#05264A,#0066B3)] px-3 font-semibold text-white shadow-sm hover:shadow-[0_14px_30px_rgba(0,102,179,0.24)] active:translate-y-px" disabled={loading}>
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

              <div className="mt-6 rounded-lg border border-[#DDE8F1] bg-[linear-gradient(135deg,#F3F8FD,#EAF8EE)] p-4 shadow-sm">
                <div className="flex gap-3">
                  <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-white text-[#248D36] shadow-sm ring-1 ring-[#39B54A]/15">
                    <CheckCircle2 size={18} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-[#0B1F33]">Protected billing access</p>
                    <p className="mt-1 text-sm leading-6 text-[#52677A]">
                      Your billing information is protected and only visible after sign in.
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-5 flex flex-col gap-2 text-sm text-[#52677A] sm:flex-row sm:items-center sm:justify-between">
                <span>Need access help?</span>
                <a href="mailto:support@slt.lk" className="inline-flex items-center gap-2 font-semibold text-[#0066B3] hover:text-[#05264A]">
                  Contact support
                  <Headphones size={14} />
                </a>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  )
}
