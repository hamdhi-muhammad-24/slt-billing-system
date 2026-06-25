import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Building2,
  CheckCircle2,
  CreditCard,
  FileText,
  Headphones,
  LockKeyhole,
  ReceiptText,
  ShieldCheck,
  Smartphone,
  Wifi,
} from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import Brand from '../components/Brand'
import { Button } from '@/components/ui/button'

const customerServices = [
  {
    icon: ReceiptText,
    title: 'View monthly bills',
    text: 'Open the latest account bill, review billing periods, and download official PDF copies.',
  },
  {
    icon: CreditCard,
    title: 'Track payments',
    text: 'See payment references, recent settlement records, and outstanding balances in one place.',
  },
  {
    icon: Smartphone,
    title: 'Self-care access',
    text: 'Use one secure login for broadband, voice, PeoTV, and bundled SLT-MOBITEL services.',
  },
]

const operations = [
  'Customer account management',
  'Billing run monitoring',
  'Invoice generation',
  'PDF-ready bill records',
]

export default function PublicPortal() {
  const { session } = useAuth()
  const dashboardPath = !session ? '/login' : session.role === 'admin' ? '/admin' : '/app'

  return (
    <main className="min-h-svh bg-background text-foreground">
      <section className="relative overflow-hidden bg-[#092b57] text-white">
        <div className="network-grid absolute inset-0 opacity-70" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_22%_18%,rgba(75,180,255,0.26),transparent_34%),radial-gradient(circle_at_76%_16%,rgba(87,190,84,0.20),transparent_32%)]" />
        <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-background to-transparent" />

        <header className="relative z-10 mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-5 sm:px-6 lg:px-8">
          <Brand tone="dark" size="lg" />
          <div className="flex items-center gap-2">
            <Button
              asChild
              variant="secondary"
              size="sm"
              className="hidden border-white/15 bg-white/10 text-white hover:bg-white/15 sm:inline-flex"
            >
              <Link to="/login">Sign in</Link>
            </Button>
            <Button asChild size="sm" className="bg-white text-[#092b57] hover:bg-white/90">
              <Link to={dashboardPath}>
                Portal
                <ArrowRight size={14} />
              </Link>
            </Button>
          </div>
        </header>

        <div className="relative z-10 mx-auto flex min-h-[76svh] max-w-7xl flex-col justify-center gap-10 px-4 pb-20 pt-8 sm:px-6 lg:px-8">
          <div className="max-w-4xl">
            <p className="mb-4 inline-flex items-center gap-2 rounded-md border border-white/15 bg-white/10 px-3 py-1.5 text-sm font-medium text-white/85">
              <ShieldCheck size={15} />
              Secure SLT-MOBITEL billing portal
            </p>
            <h1 className="max-w-4xl text-4xl font-semibold leading-[1.08] text-white sm:text-5xl lg:text-6xl">
              Manage bills, payments, and service accounts with confidence.
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-white/75 sm:text-lg">
              A modern entry point for customers and billing teams, designed around fast bill access,
              clear account status, PDF statements, and reliable SLT-MOBITEL service operations.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button asChild size="lg" className="bg-white text-[#092b57] hover:bg-white/90">
                <Link to={dashboardPath}>
                  Open customer portal
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
                  Staff billing console
                  <Building2 size={16} />
                </Link>
              </Button>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg border border-white/20 bg-white/[0.08] p-4 backdrop-blur">
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-md bg-white/10 text-white">
                  <FileText size={18} />
                </div>
                <div>
                  <p className="text-sm text-white/65">Bill access</p>
                  <p className="text-lg font-semibold">PDF statements</p>
                </div>
              </div>
            </div>
            <div className="rounded-lg border border-white/20 bg-white/[0.08] p-4 backdrop-blur">
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-md bg-white/10 text-white">
                  <Wifi size={18} />
                </div>
                <div>
                  <p className="text-sm text-white/65">Services</p>
                  <p className="text-lg font-semibold">Voice, fibre, PeoTV</p>
                </div>
              </div>
            </div>
            <div className="rounded-lg border border-white/20 bg-white/[0.08] p-4 backdrop-blur">
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-md bg-white/10 text-white">
                  <LockKeyhole size={18} />
                </div>
                <div>
                  <p className="text-sm text-white/65">Access</p>
                  <p className="text-lg font-semibold">Role based login</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-5 px-4 py-12 sm:px-6 lg:grid-cols-[1.2fr_0.8fr] lg:px-8">
        <div className="grid gap-4 md:grid-cols-3">
          {customerServices.map((item) => (
            <article key={item.title} className="surface-card p-5">
              <div className="mb-5 flex size-11 items-center justify-center rounded-md bg-primary/10 text-primary">
                <item.icon size={20} />
              </div>
              <h2 className="text-base font-semibold">{item.title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.text}</p>
            </article>
          ))}
        </div>

        <aside className="surface-section p-5">
          <div className="flex items-center gap-3 border-b border-border pb-4">
            <div className="flex size-11 items-center justify-center rounded-md bg-success/10 text-success">
              <Headphones size={20} />
            </div>
            <div>
              <h2 className="font-semibold">Billing operations ready</h2>
              <p className="text-sm text-muted-foreground">For SLT-MOBITEL internal teams</p>
            </div>
          </div>
          <div className="mt-4 grid gap-3">
            {operations.map((item) => (
              <div key={item} className="flex items-center gap-3 text-sm">
                <CheckCircle2 size={16} className="text-success" />
                <span>{item}</span>
              </div>
            ))}
          </div>
          <Button asChild className="mt-6 w-full justify-between">
            <Link to="/login">
              Continue to secure login
              <ArrowRight size={15} />
            </Link>
          </Button>
        </aside>
      </section>

      <footer className="border-t border-border bg-card">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-6 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <Brand tone="light" size="sm" />
          <p>SLT-MOBITEL billing management system</p>
        </div>
      </footer>
    </main>
  )
}
