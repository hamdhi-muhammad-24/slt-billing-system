import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Bot,
  CreditCard,
  FileText,
  Headphones,
  HelpCircle,
  LockKeyhole,
  ReceiptText,
  ShieldCheck,
  Zap
} from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import Brand from '../components/Brand'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

const navLinks = [
  { label: 'Portal Access', href: '#portal-access' },
  { label: 'Smart Features', href: '#smart-features' },
  { label: 'Support', href: '#support' },
]

const actionCards = [
  {
    icon: FileText,
    title: 'Customer Invoice Access',
    description: 'Verify your account and instantly view or download your latest AI-generated billing statements securely.',
    cta: 'View My Bill',
    helper: 'OTP Verified',
    path: '/bill-access',
    accentClass: 'from-blue-500 to-indigo-600',
    iconClass: 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-[0_12px_28px_rgba(59,130,246,0.35)]',
    buttonClass: 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md hover:shadow-lg hover:from-blue-500 hover:to-indigo-500',
  },
  {
    icon: CreditCard,
    title: 'Secure Payments',
    description: 'Quickly look up your account to process a payment through our encrypted payment gateway.',
    cta: 'Pay Now',
    helper: 'Encrypted Gateway',
    path: '/pay-bill',
    accentClass: 'from-emerald-500 to-teal-600',
    iconClass: 'bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-[0_12px_28px_rgba(16,185,129,0.35)]',
    buttonClass: 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-md hover:shadow-lg hover:from-emerald-500 hover:to-teal-500',
  },
  {
    icon: LockKeyhole,
    title: 'Staff / Admin Console',
    description: 'Authorized SLT personnel sign in here to manage GMF uploads, trigger AI generation, and monitor cycle batches.',
    cta: 'Sign In',
    helper: 'Staff Only',
    path: 'signin' as const,
    accentClass: 'from-slate-700 to-slate-900 dark:from-slate-400 dark:to-slate-600',
    iconClass: 'bg-gradient-to-br from-slate-700 to-slate-900 dark:from-slate-400 dark:to-slate-600 text-white shadow-[0_12px_28px_rgba(51,65,85,0.35)]',
    buttonClass: 'bg-gradient-to-r from-slate-800 to-slate-900 dark:from-slate-600 dark:to-slate-700 text-white shadow-md hover:shadow-lg hover:from-slate-700 hover:to-slate-800 dark:hover:from-slate-500 dark:hover:to-slate-600',
  },
]

const featureCards = [
  {
    icon: Bot,
    title: 'AI-Powered Generation',
    description: 'Our system intelligently parses massive GMF files to instantly generate visually striking, accurate PDF invoices.',
  },
  {
    icon: Zap,
    title: 'High-Speed Processing',
    description: 'Built to handle millions of records. Upload batch cycles and watch them process in real-time on the Admin Hub.',
  },
  {
    icon: ShieldCheck,
    title: 'Enterprise Security',
    description: 'From OTP customer verification to role-based Admin 1 and Admin access, every byte of data is tightly protected.',
  },
]

const heroHighlights = [
  {
    label: 'Smart Billing',
    text: 'AI-driven accuracy',
  },
  {
    label: 'GMF Processing',
    text: 'Millions of records, seconds to process',
  },
  {
    label: 'Role-Based',
    text: 'Distinct customer & admin portals',
  },
]

const gatewayStatusRows = [
  {
    icon: ReceiptText,
    label: 'Cycle Generation Hub',
    text: 'Automated and Manual Modes',
  },
  {
    icon: FileText,
    label: 'GMF Watcher Service',
    text: 'Real-time folder scanning',
  },
  {
    icon: LockKeyhole,
    label: 'Secure Archiving',
    text: 'Dual-sync to VM & G-Drive',
  },
]

const supportLinks = [
  { label: 'Contact Support', href: 'mailto:support@slt.lk' },
  { label: 'Smart Features', href: '#smart-features' },
  { label: 'Privacy Policy', href: '#terms-privacy' },
]

export default function PublicPortal() {
  const { session } = useAuth()
  const signInPath = !session ? '/login' : session.role === 'admin' ? '/admin' : session.role === 'admin1' ? '/admin1' : '/app'

  function resolveActionPath(action: (typeof actionCards)[number]): string {
    if (action.path === 'signin') return signInPath
    return action.path
  }

  return (
    <main className="min-h-svh bg-background text-foreground relative selection:bg-primary/20 selection:text-primary">
      {/* Global Background Ambient Effects */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden z-0">
        <div className="absolute -left-[10%] -top-[10%] size-[500px] rounded-full bg-blue-500/10 blur-[120px] dark:bg-blue-600/15" />
        <div className="absolute -right-[10%] top-[20%] size-[600px] rounded-full bg-indigo-500/10 blur-[120px] dark:bg-indigo-600/15" />
        <div className="absolute bottom-[-20%] left-[20%] size-[800px] rounded-full bg-emerald-500/10 blur-[150px] dark:bg-emerald-600/10" />
      </div>

      <header className="sticky top-0 z-40 border-b border-border/50 bg-background/75 shadow-sm backdrop-blur-xl">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="flex min-h-18 items-center justify-between gap-4 py-3">
            <Brand size="md" />

            <div className="flex min-w-0 items-center gap-4">
              <nav className="hidden items-center gap-7 text-sm font-medium text-muted-foreground md:flex">
                {navLinks.map((link) => (
                  <a
                    key={link.label}
                    href={link.href}
                    className="relative transition-colors hover:text-primary after:absolute after:-bottom-2 after:left-0 after:h-0.5 after:w-0 after:rounded-full after:bg-primary after:transition-all hover:after:w-full"
                  >
                    {link.label}
                  </a>
                ))}
              </nav>

              <Button asChild size="sm" className="h-10 shrink-0 bg-gradient-to-r from-blue-600 to-indigo-600 px-4 text-white shadow-md hover:shadow-lg hover:-translate-y-0.5 hover:from-blue-500 hover:to-indigo-500 transition-all border-none">
                <Link to={signInPath}>
                  Sign In
                  <ArrowRight size={14} className="ml-1" />
                </Link>
              </Button>
            </div>
          </div>

          <nav className="flex gap-4 overflow-x-auto border-t border-border/50 py-2 text-xs font-medium text-muted-foreground md:hidden">
            {navLinks.map((link) => (
              <a key={link.label} href={link.href} className="shrink-0 transition-colors hover:text-primary">
                {link.label}
              </a>
            ))}
          </nav>
        </div>
      </header>

      <section className="relative z-10 overflow-hidden py-16 sm:py-24 lg:py-32">
        <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-border to-transparent" />

        <div className="relative mx-auto grid max-w-6xl gap-10 px-4 sm:px-6 lg:grid-cols-[minmax(0,1fr)_420px] lg:items-center lg:gap-16 lg:px-8">
          <div className="max-w-3xl">
            <p className="inline-flex max-w-full items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3.5 py-1.5 text-sm font-medium text-primary shadow-sm backdrop-blur-md">
              <ShieldCheck size={16} />
              <span className="min-w-0">SLT-MOBITEL Next-Gen Billing System</span>
            </p>
            <h1 className="mt-6 max-w-4xl text-4xl font-extrabold tracking-tight leading-[1.1] sm:text-5xl lg:text-6xl bg-gradient-to-br from-foreground to-foreground/70 bg-clip-text text-transparent">
              Smart Invoice Generation & Billing Gateway
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground">
              Experience the future of telecommunications billing. Our AI-driven platform processes millions of GMF records, generating beautiful, accurate invoices instantly while providing a secure portal for both customers and administrators.
            </p>

            <div className="mt-10 grid max-w-2xl gap-4 sm:grid-cols-3">
              {heroHighlights.map((item) => (
                <div
                  key={item.label}
                  className="glass-card rounded-xl p-4 transition-all hover:-translate-y-1 hover:shadow-lg"
                >
                  <p className="text-sm font-bold text-foreground">{item.label}</p>
                  <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{item.text}</p>
                </div>
              ))}
            </div>
          </div>

          <aside className="relative overflow-hidden rounded-[2rem] glass-card p-6 sm:p-8 shadow-2xl ring-1 ring-white/10 dark:ring-white/5">
            <div className="pointer-events-none absolute -right-20 -top-20 size-64 rounded-full bg-primary/20 blur-[80px]" />

            <div className="relative">
              <div className="flex items-start justify-between gap-4">
                <div className="flex min-w-0 items-center gap-4">
                  <div className="flex size-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-lg">
                    <ReceiptText size={24} />
                  </div>
                  <div className="min-w-0">
                    <h2 className="text-xl font-bold text-foreground">System Status</h2>
                    <p className="mt-1 text-sm font-medium text-emerald-500 flex items-center gap-1.5">
                      <span className="relative flex size-2.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full size-2.5 bg-emerald-500"></span>
                      </span>
                      All Services Operational
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-8 grid gap-3">
                {gatewayStatusRows.map((item) => {
                  const Icon = item.icon
                  return (
                    <div
                      key={item.label}
                      className="group flex items-center gap-4 rounded-xl border border-border/50 bg-muted/30 p-4 transition-all duration-300 hover:border-primary/30 hover:bg-muted/50 hover:shadow-md"
                    >
                      <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-background text-primary shadow-sm ring-1 ring-border group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                        <Icon size={18} />
                      </span>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-foreground">{item.label}</p>
                        <p className="mt-0.5 text-xs text-muted-foreground">{item.text}</p>
                      </div>
                    </div>
                  )
                })}
              </div>

              <div className="mt-8 flex items-center gap-3 border-t border-border pt-5">
                <LockKeyhole size={16} className="shrink-0 text-muted-foreground" />
                <p className="text-xs leading-relaxed text-muted-foreground">End-to-end encryption active for all customer billing data and staff generation operations.</p>
              </div>
            </div>
          </aside>
        </div>
      </section>

      <section id="portal-access" className="relative z-10 mx-auto max-w-6xl px-4 pb-16 sm:px-6 lg:px-8">
        <div className="grid gap-6 md:grid-cols-3">
          {actionCards.map((action) => {
            const Icon = action.icon
            return (
              <Card
                key={action.title}
                className={`glass-card relative overflow-hidden rounded-2xl py-0 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl`}
              >
                <div className={`absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r ${action.accentClass}`} />
                <CardContent className="flex h-full min-h-[280px] flex-col p-6 sm:p-8">
                  <div className="flex items-start justify-between gap-3">
                    <div className={`flex size-14 items-center justify-center rounded-xl ${action.iconClass}`}>
                      <Icon size={26} />
                    </div>
                    <span className="whitespace-nowrap rounded-full bg-primary/10 px-3 py-1.5 text-xs font-semibold text-primary">
                      {action.helper}
                    </span>
                  </div>
                  <h2 className="mt-6 text-xl font-bold text-foreground">{action.title}</h2>
                  <p className="mt-3 flex-1 text-sm leading-relaxed text-muted-foreground">{action.description}</p>
                  <Button asChild className={`mt-8 h-12 w-full justify-between px-5 font-semibold border-none ${action.buttonClass}`}>
                    <Link to={resolveActionPath(action)}>
                      <span className="truncate">{action.cta}</span>
                      <ArrowRight size={16} />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </section>

      <section id="smart-features" className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="glass-card relative overflow-hidden rounded-[2rem] p-8 sm:p-12">
          <div className="absolute inset-0 opacity-[0.03] dark:opacity-[0.05] [background-image:radial-gradient(var(--foreground)_1px,transparent_1px)] [background-size:24px_24px]" />
          
          <div className="relative flex flex-col gap-4 md:flex-row md:items-end md:justify-between mb-10">
            <div className="max-w-2xl">
              <p className="text-sm font-bold uppercase tracking-wider text-primary">Why use this portal?</p>
              <h2 className="mt-3 text-3xl font-extrabold text-foreground sm:text-4xl">
                Modern Telecom E-Billing Made Simple
              </h2>
              <p className="mt-4 text-base leading-relaxed text-muted-foreground max-w-xl">
                We've revolutionized how billing data is processed. By ingesting complex GMF files, our AI engine designs, formats, and generates pixel-perfect PDF statements, ensuring accuracy and security for every customer.
              </p>
            </div>
          </div>

          <div className="relative grid gap-6 md:grid-cols-3">
            {featureCards.map((feature) => {
              const Icon = feature.icon
              return (
                <div
                  key={feature.title}
                  className="group rounded-2xl border border-border/50 bg-background/50 p-6 transition duration-300 hover:-translate-y-1 hover:border-primary/40 hover:bg-background hover:shadow-xl"
                >
                  <div className="flex size-12 items-center justify-center rounded-xl bg-primary/10 text-primary ring-1 ring-primary/20 group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    <Icon size={22} />
                  </div>
                  <h3 className="mt-5 text-lg font-bold text-foreground">{feature.title}</h3>
                  <p className="mt-2.5 text-sm leading-relaxed text-muted-foreground">{feature.description}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      <section id="support" className="mx-auto max-w-6xl px-4 pb-16 sm:px-6 lg:px-8">
        <div className="glass-card rounded-[2rem] p-6 sm:p-8 lg:flex lg:items-center lg:justify-between lg:gap-8">
          <div className="flex items-start gap-5">
            <div className="flex size-14 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-500 ring-1 ring-emerald-500/20">
              <Headphones size={26} />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-foreground">Need Assistance?</h2>
              <p className="mt-2 max-w-lg text-sm leading-relaxed text-muted-foreground">
                Get help with OTP verification, portal access issues, or questions regarding your AI-generated billing statements.
              </p>
            </div>
          </div>

          <div className="mt-8 grid gap-3 sm:grid-cols-3 lg:mt-0 lg:min-w-[420px]">
            {supportLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="inline-flex h-11 items-center justify-center gap-2.5 whitespace-nowrap rounded-xl border border-border bg-background/50 px-4 text-sm font-semibold text-foreground shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary/40 hover:bg-primary hover:text-primary-foreground hover:shadow-md"
              >
                <HelpCircle size={16} />
                {link.label}
              </a>
            ))}
          </div>
        </div>
      </section>

      <footer id="terms-privacy" className="border-t border-border/60 bg-background/50 backdrop-blur-sm mt-auto">
        <div className="mx-auto flex max-w-6xl flex-col gap-5 px-4 py-8 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <Brand size="sm" />
          <p className="font-medium text-center sm:text-right">&copy; {new Date().getFullYear()} SLT-MOBITEL. All rights reserved. Smart Billing System.</p>
        </div>
      </footer>
    </main>
  )
}
