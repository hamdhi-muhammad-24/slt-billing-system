import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Building2,
  Eye,
  EyeOff,
  UserRound,
  ShieldCheck,
  Zap,
  Mail,
  Lock,
  Moon,
  Sun
} from 'lucide-react'
import { useTheme } from 'next-themes'
import { useAuth } from '../auth/AuthProvider'
import { authLogin, authMe, setToken, clearToken } from '../lib/api'
import Brand from '../components/Brand'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

const ROLE_HOME = { admin: '/admin', admin1: '/admin1', customer: '/app' } as const

type GatewayMode = 'customer' | 'staff'

const roleTabs = [
  {
    id: 'customer' as const,
    icon: UserRound,
    label: 'Customer Portal',
  },
  {
    id: 'staff' as const,
    icon: Building2,
    label: 'Staff Console',
  },
]

export default function Login() {
  const { session, isChecking, login } = useAuth()
  const { theme, setTheme } = useTheme()
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
      setError(err?.detail || err?.message || 'Login failed. Please verify your credentials and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-svh w-full flex bg-background selection:bg-[#0066b3]/20 selection:text-[#0066b3]">

      {/* Left Panel: SLT-MOBITEL Premium Branding */}
      <div className="relative hidden lg:flex flex-1 flex-col overflow-hidden bg-slate-950">
        {/* Elegant Animated Gradient Orbs */}
        <div className="absolute inset-0 z-0">
          <div className="absolute -left-[10%] top-[10%] h-[700px] w-[700px] rounded-full bg-[#0066b3]/30 blur-[140px] animate-pulse [animation-duration:15s]" />
          <div className="absolute right-[0%] top-[30%] h-[600px] w-[600px] rounded-full bg-[#00a651]/20 blur-[130px] animate-pulse [animation-duration:12s] [animation-delay:2s]" />
          <div className="absolute -bottom-[20%] left-[30%] h-[800px] w-[800px] rounded-full bg-[#00b2e3]/20 blur-[150px] animate-pulse [animation-duration:18s] [animation-delay:4s]" />
        </div>

        {/* Fixed Brand Logo exactly matching Admin Sidebar Top-Left alignment */}
        <div className="absolute top-0 left-0 w-full h-16 flex items-center px-8 z-20">
          <Brand size="md" tone="dark" className="text-white drop-shadow-md" />
        </div>

        {/* Value Proposition Content (Perfectly Centered) */}
        <div className="relative z-10 flex h-full w-full flex-col justify-center px-10 xl:px-16 pt-10">
          <div className="max-w-xl xl:max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-[13px] font-bold tracking-wide text-white shadow-sm backdrop-blur-md mb-8">
              <ShieldCheck size={16} className="text-[#00b2e3]" />
              SLT-MOBITEL SECURE GATEWAY
            </div>

            <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl xl:text-6xl leading-[1.15]">
              AI-Powered <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#00b2e3] to-[#00a651]">
                Invoice Generation
              </span>
            </h1>
            <p className="mt-8 text-lg font-medium leading-relaxed text-slate-300">
              Access the centralized SLT-MOBITEL billing environment. Manage massive GMF batch cycles securely, verify generated statements, and monitor the automated pipeline in real-time.
            </p>

            <div className="mt-12 flex items-center gap-8">
              <div className="flex items-center gap-4">
                <div className="flex size-14 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-white backdrop-blur-sm border border-white/10 shadow-lg">
                  <Zap size={26} className="text-[#00b2e3]" />
                </div>
                <div>
                  <p className="text-[15px] font-bold text-white">High-Speed Pipeline</p>
                  <p className="text-[13px] font-medium text-slate-400">Process millions of records</p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="flex size-14 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-white backdrop-blur-sm border border-white/10 shadow-lg">
                  <ShieldCheck size={26} className="text-[#00a651]" />
                </div>
                <div>
                  <p className="text-[15px] font-bold text-white">Bank-Grade Security</p>
                  <p className="text-[13px] font-medium text-slate-400">AES-256 Encrypted Storage</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel: Clean, High-Contrast Form */}
      <div className="relative flex w-full flex-col bg-background lg:w-[500px] xl:w-[650px] lg:shrink-0">

        {/* Navigation Header - Matches Admin Top Nav Bar Height & Padding */}
        <div className="absolute top-0 left-0 w-full h-16 px-6 sm:px-8 flex justify-between items-center z-20">
          <div className="lg:hidden">
            <Brand size="md" />
          </div>
          <div className="ml-auto flex items-center gap-3">
            <Button
              variant="outline"
              size="icon"
              className="rounded-full bg-background hover:bg-muted border-border transition-all"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              title="Toggle theme"
            >
              <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0 text-foreground" />
              <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100 text-foreground" />
              <span className="sr-only">Toggle theme</span>
            </Button>
            <Button asChild variant="outline" className="gap-2 text-foreground font-semibold shadow-sm rounded-full bg-background hover:bg-muted border-border transition-all">
              <Link to="/">
                <ArrowLeft size={16} />
                Return to Portal
              </Link>
            </Button>
          </div>
        </div>

        {/* Subtle background glow for mobile */}
        <div className="absolute inset-0 z-0 lg:hidden overflow-hidden">
          <div className="absolute -top-[10%] right-[0%] h-[500px] w-[500px] rounded-full bg-[#0066b3]/5 blur-[100px]" />
          <div className="absolute bottom-[0%] left-[0%] h-[500px] w-[500px] rounded-full bg-[#00a651]/5 blur-[100px]" />
        </div>

        {/* Form Container */}
        <div className="relative z-10 flex h-full w-full flex-col justify-center px-6 sm:px-12 xl:px-20 pt-28 lg:pt-0">

          <div className="flex flex-col space-y-2 mb-8">
            <h2 className="text-3xl font-extrabold tracking-tight text-foreground">Welcome Back</h2>
            <p className="text-[15px] font-medium text-muted-foreground">
              Sign in to access the SLT-MOBITEL {activeMode === 'staff' ? 'staff console' : 'customer billing portal'}.
            </p>
          </div>

          <div className="mb-10">
            <div className="grid grid-cols-2 gap-2 rounded-xl bg-muted p-1.5 ring-1 ring-inset ring-border/80 shadow-inner">
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
                      'flex h-12 items-center justify-center gap-2.5 rounded-lg text-[14px] font-bold transition-all duration-300',
                      isActive
                        ? 'bg-background text-foreground shadow-md ring-1 ring-border/50'
                        : 'text-muted-foreground hover:text-foreground hover:bg-background/50',
                    )}
                  >
                    <Icon size={18} />
                    {tab.label}
                  </button>
                )
              })}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="grid gap-7">
            <div className="grid gap-2.5">
              <Label htmlFor="email" className="text-[14px] font-bold text-foreground">
                Email address
              </Label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 flex items-center pl-4 text-muted-foreground pointer-events-none">
                  <Mail size={18} />
                </div>
                <Input
                  id="email"
                  type="email"
                  autoComplete="username"
                  required
                  placeholder={activeMode === 'staff' ? 'admin@slt.lk' : 'customer@example.com'}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="h-14 pl-12 pr-4 text-[15px] bg-background border-border shadow-sm focus-visible:ring-2 focus-visible:border-[#0066b3] focus-visible:ring-[#0066b3]/20 rounded-xl transition-all placeholder:text-muted-foreground/60 font-medium"
                />
              </div>
            </div>

            <div className="grid gap-2.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-[14px] font-bold text-foreground">
                  Password
                </Label>
                <a
                  href="mailto:support@slt.lk?subject=Billing%20portal%20password%20help"
                  className="text-[13px] font-bold text-[#0066b3] dark:text-[#66c2ff] hover:underline"
                >
                  Forgot password?
                </a>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 flex items-center pl-4 text-muted-foreground pointer-events-none">
                  <Lock size={18} />
                </div>
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-14 pl-12 pr-12 text-[15px] bg-background border-border shadow-sm focus-visible:ring-2 focus-visible:border-[#0066b3] focus-visible:ring-[#0066b3]/20 rounded-xl transition-all placeholder:text-muted-foreground/60 font-medium"
                />
                <button
                  type="button"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  onClick={() => setShowPassword((value) => !value)}
                  className="absolute right-2 top-1/2 flex size-10 -translate-y-1/2 items-center justify-center rounded-xl text-muted-foreground transition-all hover:bg-muted hover:text-foreground"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="flex gap-3 rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-4 mt-2">
                <AlertCircle size={20} className="mt-0.5 shrink-0 text-destructive" />
                <p className="text-[14px] leading-relaxed text-destructive font-bold" role="alert">
                  {error}
                </p>
              </div>
            )}

            <Button
              type="submit"
              className="mt-4 h-14 w-full bg-gradient-to-r from-[#0066b3] to-[#00b2e3] hover:opacity-90 font-extrabold text-[16px] text-white shadow-lg shadow-[#0066b3]/25 active:scale-[0.98] border-none transition-all duration-300 rounded-xl group"
              disabled={loading}
            >
              {loading ? (
                <span className="flex items-center gap-3">
                  <span className="size-5 animate-spin rounded-full border-[3px] border-white/30 border-t-white" />
                  Authenticating...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-3 w-full px-2 tracking-wide">
                  Secure Login
                  <ArrowRight size={20} className="transition-transform group-hover:translate-x-1" />
                </span>
              )}
            </Button>
          </form>

          <p className="mt-12 text-center text-[13px] font-medium text-muted-foreground leading-relaxed">
            Secured by SLT-MOBITEL Enterprise Gateway. <br className="hidden sm:block" /> By signing in, you agree to our <a href="#" className="text-foreground font-bold hover:text-[#0066b3] transition-colors">Terms of Service</a> & <a href="#" className="text-foreground font-bold hover:text-[#0066b3] transition-colors">Privacy Policy</a>.
          </p>
        </div>
      </div>
    </main>
  )
}
