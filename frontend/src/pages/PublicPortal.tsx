import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Building2,
  CheckCircle2,
  CreditCard,
  FileText,
  Headphones,
  HelpCircle,
  LockKeyhole,
  ReceiptText,
  ShieldCheck,
  Smartphone,
  Wifi,
} from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import Brand from '../components/Brand'
import { Button } from '@/components/ui/button'

const actionCards = [
  {
    icon: FileText,
    title: 'View My Bill',
    text: 'Access your latest bills and download statement copies after secure sign in.',
    to: 'customer' as const,
    className: 'bg-primary text-primary-foreground',
  },
  {
    icon: CreditCard,
    title: 'Pay Bill',
    text: 'Continue to authenticated billing access before making a payment.',
    to: 'login' as const,
    className: 'bg-success text-success-foreground',
  },
  {
    icon: LockKeyhole,
    title: 'Sign In',
    text: 'Enter the customer portal or staff billing console with role-based access.',
    to: 'signin' as const,
    className: 'bg-[#102f55] text-white',
  },
]

const portalPaths = [
  {
    icon: Smartphone,
    title: 'Customer Self-Care',
    text: 'View bills, statements, service accounts, and payment history.',
  },
  {
    icon: Building2,
    title: 'Staff Billing Console',
    text: 'Manage customers, accounts, invoices, and billing operations.',
  },
  {
    icon: Headphones,
    title: 'Billing Support',
    text: 'Find help for billing questions, account access, and statements.',
  },
]

const supportLinks = [
  { label: 'Contact support', href: 'mailto:support@slt.lk' },
  { label: 'Billing help', href: '#billing-help' },
  { label: 'Terms and privacy', href: '#terms-privacy' },
]

export default function PublicPortal() {
  const { session } = useAuth()
  const customerPortalPath = session?.role === 'customer' ? '/app' : '/login'
  const signInPath = !session ? '/login' : session.role === 'admin' ? '/admin' : '/app'

  function resolveActionPath(action: (typeof actionCards)[number]): string {
    if (action.to === 'customer') return customerPortalPath
    if (action.to === 'signin') return signInPath
    return '/login'
  }

  return (
    <main className="min-h-svh bg-[#f4f8fc] text-foreground">
      <header className="sticky top-0 z-40 border-b border-border/70 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-20 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <Brand tone="light" size="lg" />

          <nav className="hidden items-center gap-7 text-sm font-medium text-muted-foreground lg:flex">
            <a href="#portal-access" className="transition-colors hover:text-primary">
              Portal access
            </a>
            <a href="#billing-help" className="transition-colors hover:text-primary">
              Billing help
            </a>
            <a href="#support" className="transition-colors hover:text-primary">
              Support
            </a>
          </nav>

          <Button asChild size="sm" className="shrink-0">
            <Link to={signInPath}>
              Sign In
              <ArrowRight size={14} />
            </Link>
          </Button>
        </div>
      </header>

      <section className="relative overflow-hidden bg-white">
        <div className="absolute inset-x-0 top-0 h-[560px] bg-[#07284d]" />
        <div className="network-grid absolute inset-x-0 top-0 h-[560px] opacity-35" />
        <div className="absolute inset-x-0 top-0 h-[560px] bg-[radial-gradient(circle_at_18%_22%,rgba(73,173,235,0.28),transparent_30%),radial-gradient(circle_at_84%_18%,rgba(78,184,72,0.20),transparent_30%)]" />

        <div className="relative mx-auto max-w-7xl px-4 pb-14 pt-10 sm:px-6 lg:px-8">
          <div className="grid min-h-[560px] items-center gap-10 lg:grid-cols-[minmax(0,1fr)_440px]">
            <div className="max-w-3xl text-white">
              <p className="inline-flex items-center gap-2 rounded-md border border-white/20 bg-white/10 px-3 py-1.5 text-sm font-medium text-white/85">
                <ShieldCheck size={15} />
                Secure billing access for customers and administrators
              </p>
              <h1 className="mt-6 text-4xl font-semibold leading-[1.04] sm:text-5xl lg:text-7xl">
                SLT-MOBITEL Billing Portal
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-7 text-white/76 sm:text-lg">
                View bills, continue to payment access, and sign in to manage SLT-MOBITEL
                broadband, voice, PeoTV, and bundled service accounts.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Button asChild size="lg" className="bg-white text-[#07284d] hover:bg-white/90">
                  <Link to={customerPortalPath}>
                    View My Bill
                    <ArrowRight size={16} />
                  </Link>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="border-white/25 bg-white/5 text-white hover:bg-white/10 hover:text-white"
                >
                  <Link to="/login">
                    Pay Bill
                    <CreditCard size={16} />
                  </Link>
                </Button>
              </div>
            </div>

            <div className="rounded-lg border border-white/18 bg-white p-5 shadow-2xl">
              <div className="flex items-center justify-between gap-4 border-b border-border pb-5">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Access center</p>
                  <h2 className="mt-1 text-2xl font-semibold text-[#07284d]">What do you need today?</h2>
                </div>
                <div className="flex size-12 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                  <ReceiptText size={22} />
                </div>
              </div>

              <div className="mt-5 grid gap-3">
                {actionCards.map((action) => {
                  const Icon = action.icon
                  return (
                    <Link
                      key={action.title}
                      to={resolveActionPath(action)}
                      className="group grid grid-cols-[44px_1fr_18px] items-center gap-3 rounded-lg border border-border bg-white p-3 transition hover:border-primary/35 hover:bg-muted/30"
                    >
                      <span className={`flex size-11 items-center justify-center rounded-md ${action.className}`}>
                        <Icon size={19} />
                      </span>
                      <span className="min-w-0">
                        <span className="block text-sm font-semibold">{action.title}</span>
                        <span className="mt-0.5 block text-xs leading-5 text-muted-foreground">{action.text}</span>
                      </span>
                      <ArrowRight size={16} className="text-muted-foreground transition-transform group-hover:translate-x-1 group-hover:text-primary" />
                    </Link>
                  )
                })}
              </div>

              <div className="mt-5 flex items-center gap-2 rounded-md bg-[#eef7f0] px-3 py-3 text-sm text-[#1d5b27]">
                <CheckCircle2 size={16} />
                <span className="font-medium">No account details are shown before sign in.</span>
              </div>
            </div>
          </div>

          <div id="portal-access" className="-mt-4 grid gap-4 lg:grid-cols-3">
            {portalPaths.map((path) => {
              const Icon = path.icon
              return (
                <article key={path.title} className="surface-card p-5">
                  <div className="flex items-start gap-4">
                    <div className="flex size-11 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                      <Icon size={20} />
                    </div>
                    <div>
                      <h2 className="text-base font-semibold">{path.title}</h2>
                      <p className="mt-2 text-sm leading-6 text-muted-foreground">{path.text}</p>
                    </div>
                  </div>
                </article>
              )
            })}
          </div>
        </div>
      </section>

      <section id="billing-help" className="mx-auto grid max-w-7xl gap-5 px-4 py-10 sm:px-6 lg:grid-cols-[1fr_380px] lg:px-8">
        <div className="surface-section p-5 sm:p-6">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Customer journeys</p>
              <h2 className="mt-1 text-2xl font-semibold">Designed around common billing tasks</h2>
            </div>
            <p className="max-w-md text-sm leading-6 text-muted-foreground">
              The first screen guides people directly to bill viewing, payment access, sign in, and
              support without exposing private account data.
            </p>
          </div>

          <div className="mt-6 grid gap-3 md:grid-cols-3">
            <div className="rounded-lg border border-border bg-muted/25 p-4">
              <FileText size={20} className="text-primary" />
              <h3 className="mt-4 font-semibold">Bill access</h3>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                Customers can enter the portal to view bill copies and statement downloads.
              </p>
            </div>
            <div className="rounded-lg border border-border bg-muted/25 p-4">
              <CreditCard size={20} className="text-success" />
              <h3 className="mt-4 font-semibold">Payment path</h3>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                Payment access stays behind secure authentication for safer billing workflows.
              </p>
            </div>
            <div className="rounded-lg border border-border bg-muted/25 p-4">
              <Wifi size={20} className="text-primary" />
              <h3 className="mt-4 font-semibold">Service visibility</h3>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                Broadband, voice, PeoTV, and bundle services can be reviewed after sign in.
              </p>
            </div>
          </div>
        </div>

        <aside id="support" className="surface-section p-5 sm:p-6">
          <div className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-md bg-success/10 text-success">
              <Headphones size={20} />
            </div>
            <div>
              <h2 className="font-semibold">Support</h2>
              <p className="text-sm text-muted-foreground">Help for billing and portal access</p>
            </div>
          </div>

          <div className="mt-5 grid gap-2">
            {supportLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="flex items-center justify-between rounded-md border border-border bg-muted/25 px-3 py-3 text-sm font-medium transition-colors hover:border-primary/40 hover:text-primary"
              >
                <span className="flex items-center gap-2">
                  <HelpCircle size={15} />
                  {link.label}
                </span>
                <ArrowRight size={14} />
              </a>
            ))}
          </div>
        </aside>
      </section>

      <footer id="terms-privacy" className="border-t border-border bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-6 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <Brand tone="light" size="sm" />
          <p>Terms and privacy apply to all SLT-MOBITEL billing portal access.</p>
        </div>
      </footer>
    </main>
  )
}
