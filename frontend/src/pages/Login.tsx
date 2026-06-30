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
import { authLogin, authMe, setToken, ApiError } from '../lib/api'
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
  if (mode === 'staff') return 'Use authorized SLT-MOBITEL staff credentials to continue.'
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
    <main className="min-h-svh overflow-hidden bg-[#F4F8FB] text-[#0B1F33]">
      <header className="relative z-20 border-b border-[#DCE8F2] bg-white/95 backdrop-blur">
        <div className="mx-auto flex min-h-18 max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
          <Brand tone="light" size="md" />
          <Button asChild variant="outline" size="sm" className="h-9 shrink-0 border-[#CADAEA] bg-white px-3 text-[#062B55] shadow-sm hover:bg-[#F4F8FB]">
            <Link to="/">
              <ArrowLeft size={14} />
              <span className="hidden sm:inline">Back to Portal</span>
              <span className="sm:hidden">Portal</span>
            </Link>
          </Button>
        </div>
      </header>

      <section className="relative">
        <div className="absolute inset-x-0 top-0 h-72 bg-[linear-gradient(135deg,#062B55_0%,#083F78_58%,#0057A8_100%)]" />
        <div className="absolute inset-x-0 top-0 h-72 opacity-25 [background-image:linear-gradient(rgba(255,255,255,0.14)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.14)_1px,transparent_1px)] [background-size:42px_42px]" />

        <div className="relative mx-auto grid max-w-6xl gap-5 px-4 py-8 sm:px-6 sm:py-10 lg:grid-cols-[minmax(0,1fr)_430px] lg:items-stretch lg:px-8 lg:py-14">
          <section className="rounded-lg border border-white/16 bg-[linear-gradient(145deg,rgba(6,43,85,0.98),rgba(0,87,168,0.92))] p-5 text-white shadow-[0_24px_70px_rgba(6,43,85,0.24)] sm:p-8 lg:min-h-[620px]">
            <div className="flex h-full flex-col">
              <p className="inline-flex max-w-full items-center gap-2 rounded-md border border-white/18 bg-white/10 px-3 py-1.5 text-sm font-medium text-white/90">
                <ShieldCheck size={15} />
                <span>Secure SLT-MOBITEL portal gateway</span>
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
                    <div key={item.label} className="flex items-center gap-3 rounded-md border border-white/12 bg-white/8 px-3.5 py-3 text-sm text-white/88">
                      <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-white text-[#0057A8]">
                        <Icon size={17} />
                      </span>
                      <span className="font-medium">{item.label}</span>
                    </div>
                  )
                })}
              </div>

              <div className="mt-auto hidden pt-10 lg:block">
                <div className="rounded-lg border border-white/12 bg-white/8 p-4">
                  <div className="flex items-center gap-2 text-sm font-semibold text-white">
                    <CheckCircle2 size={16} className="text-[#6FE17D]" />
                    SLT-MOBITEL Billing Management
                  </div>
                  <p className="mt-2 text-sm leading-6 text-white/68">
                    A secure gateway for customer self-care and staff billing operations.
                  </p>
                </div>
              </div>
            </div>
          </section>

          <Card className="rounded-lg border border-[#D8E6F2] bg-white py-0 shadow-[0_24px_70px_rgba(6,43,85,0.14)]">
            <CardContent className="p-5 sm:p-7">
              <div>
                <p className="text-sm font-semibold uppercase text-[#0057A8]">Billing portal login</p>
                <h2 className="mt-2 text-3xl font-semibold text-[#0B1F33]">Welcome back</h2>
                <p className="mt-2 text-sm leading-6 text-[#536B7D]">{modeSubtitle(activeMode)}</p>
              </div>

              <div className="mt-6 grid grid-cols-2 gap-2 rounded-lg border border-[#DDE8F1] bg-[#F4F8FB] p-1">
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
                          ? 'bg-white text-[#062B55] shadow-sm ring-1 ring-[#CADAEA]'
                          : 'text-[#536B7D] hover:bg-white/70 hover:text-[#062B55]',
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
                    className="h-11 border-[#CADAEA] bg-white text-[#0B1F33] placeholder:text-[#8CA1B4] focus-visible:ring-[#0057A8]/25"
                  />
                </div>

                <div className="grid gap-2">
                  <div className="flex items-center justify-between gap-3">
                    <Label htmlFor="password" className="text-sm font-medium text-[#0B1F33]">
                      Password
                    </Label>
                    <a
                      href="mailto:support@slt.lk?subject=Billing%20portal%20password%20help"
                      className="text-xs font-semibold text-[#0057A8] hover:text-[#062B55]"
                    >
                      Forgot password?
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
                      className="h-11 border-[#CADAEA] bg-white pr-11 text-[#0B1F33] placeholder:text-[#8CA1B4] focus-visible:ring-[#0057A8]/25"
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

                <Button type="submit" className="h-11 w-full justify-between bg-[#062B55] px-3 font-semibold text-white shadow-sm hover:bg-[#0057A8]" disabled={loading}>
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

              <div className="mt-6 rounded-lg border border-[#DDE8F1] bg-[#F7FAFD] p-4">
                <div className="flex gap-3">
                  <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-[#EAF8EE] text-[#248D36]">
                    <CheckCircle2 size={18} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-[#0B1F33]">Protected billing access</p>
                    <p className="mt-1 text-sm leading-6 text-[#536B7D]">
                      Your billing information is protected and only visible after sign in.
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-5 flex flex-col gap-2 text-sm text-[#536B7D] sm:flex-row sm:items-center sm:justify-between">
                <span>Need access help?</span>
                <a href="mailto:support@slt.lk" className="inline-flex items-center gap-2 font-semibold text-[#0057A8] hover:text-[#062B55]">
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
