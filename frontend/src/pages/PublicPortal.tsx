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
} from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import Brand from '../components/Brand'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

const navLinks = [
  { label: 'Portal access', href: '#portal-access' },
  { label: 'Billing help', href: '#billing-help' },
  { label: 'Support', href: '#support' },
]

const actionCards = [
  {
    icon: FileText,
    title: 'View My Bill',
    description: 'Access your latest bills and download statement copies after secure verification.',
    cta: 'View bill',
    to: 'customer' as const,
    iconClass: 'bg-[#EAF4FF] text-[#0057A8] ring-[#0057A8]/15',
    buttonClass: 'bg-[#0057A8] text-white hover:bg-[#004A8F]',
    borderClass: 'hover:border-[#0057A8]/45',
  },
  {
    icon: CreditCard,
    title: 'Pay Bill',
    description: 'Continue to authenticated billing access before making a payment.',
    cta: 'Pay bill',
    to: 'login' as const,
    iconClass: 'bg-[#EAF8EE] text-[#248D36] ring-[#39B54A]/20',
    buttonClass: 'bg-[#39B54A] text-white hover:bg-[#2FA13E]',
    borderClass: 'hover:border-[#39B54A]/45',
  },
  {
    icon: LockKeyhole,
    title: 'Sign In',
    description: 'Enter the customer portal or staff billing console with role-based access.',
    cta: 'Sign in',
    to: 'signin' as const,
    iconClass: 'bg-[#E9EEF5] text-[#062B55] ring-[#062B55]/15',
    buttonClass: 'bg-[#062B55] text-white hover:bg-[#0A3B72]',
    borderClass: 'hover:border-[#062B55]/45',
  },
]

const featureCards = [
  {
    icon: ShieldCheck,
    title: 'Secure access',
    description: 'Private bill data stays behind verified customer and administrator access.',
  },
  {
    icon: ReceiptText,
    title: 'Fast bill viewing',
    description: 'Open recent bills and download statement copies from one clear entry point.',
  },
  {
    icon: Building2,
    title: 'Customer and staff workflows',
    description: 'Role-aware paths guide customers and staff to the right billing workspace.',
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
    <main className="min-h-svh bg-[#F4F8FB] text-[#0B1F33]">
      <header className="sticky top-0 z-40 border-b border-[#DCE8F2] bg-white/95 backdrop-blur">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="flex min-h-18 items-center justify-between gap-3 py-3">
            <Brand tone="light" size="md" />

            <div className="flex items-center gap-3">
              <nav className="hidden items-center gap-7 text-sm font-medium text-[#486276] md:flex">
                {navLinks.map((link) => (
                  <a key={link.label} href={link.href} className="transition-colors hover:text-[#0057A8]">
                    {link.label}
                  </a>
                ))}
              </nav>

              <Button asChild size="sm" className="h-9 bg-[#062B55] px-3 text-white shadow-sm hover:bg-[#0057A8]">
                <Link to={signInPath}>
                  Sign In
                  <ArrowRight size={14} />
                </Link>
              </Button>
            </div>
          </div>

          <nav className="flex gap-4 overflow-x-auto border-t border-[#E4EEF6] py-2 text-xs font-medium text-[#486276] md:hidden">
            {navLinks.map((link) => (
              <a key={link.label} href={link.href} className="shrink-0 transition-colors hover:text-[#0057A8]">
                {link.label}
              </a>
            ))}
          </nav>
        </div>
      </header>

      <section className="relative overflow-hidden bg-[#062B55] text-white">
        <div className="absolute inset-0 bg-gradient-to-br from-[#062B55] via-[#083F78] to-[#0057A8]" />
        <div className="absolute inset-0 opacity-30 [background-image:linear-gradient(rgba(255,255,255,0.12)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.12)_1px,transparent_1px)] [background-size:44px_44px]" />
        <div className="absolute inset-x-0 bottom-0 h-px bg-white/15" />

        <div className="relative mx-auto grid max-w-6xl gap-8 px-4 py-12 sm:px-6 sm:py-16 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-center lg:gap-10 lg:px-8 lg:py-20">
          <div className="max-w-3xl">
            <p className="inline-flex max-w-full items-center gap-2 rounded-md border border-white/20 bg-white/10 px-3 py-1.5 text-sm font-medium text-white/90 shadow-sm">
              <ShieldCheck size={15} />
              <span>Secure billing access for customers and administrators</span>
            </p>
            <h1 className="mt-6 max-w-4xl text-4xl font-semibold leading-[1.08] sm:text-5xl lg:text-6xl">
              Manage your SLT-MOBITEL bills securely
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-white/78 sm:text-lg">
              View bills, continue to payment access, and sign in to manage broadband, voice,
              PeoTV, and bundled service accounts.
            </p>
          </div>

          <aside className="rounded-lg border border-white/18 bg-white/10 p-5 shadow-[0_24px_70px_rgba(0,0,0,0.20)] backdrop-blur">
            <div className="flex items-center gap-3 border-b border-white/15 pb-5">
              <div className="flex size-12 shrink-0 items-center justify-center rounded-md bg-white text-[#0057A8]">
                <ReceiptText size={22} />
              </div>
              <div>
                <h2 className="text-lg font-semibold">Billing gateway</h2>
                <p className="mt-1 text-sm leading-5 text-white/70">Clear access for bill and account tasks.</p>
              </div>
            </div>

            <div className="mt-5 grid gap-3">
              {[
                'Verified customer bill access',
                'Authenticated payment entry',
                'Role-based staff administration',
              ].map((item) => (
                <div key={item} className="flex items-center gap-3 rounded-md bg-white/8 px-3 py-3 text-sm text-white/86">
                  <CheckCircle2 size={16} className="shrink-0 text-[#6FE17D]" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </aside>
        </div>
      </section>

      <section id="portal-access" className="relative z-10 mx-auto -mt-8 max-w-6xl px-4 sm:-mt-10 sm:px-6 lg:px-8">
        <div className="grid gap-4 md:grid-cols-3">
          {actionCards.map((action) => {
            const Icon = action.icon
            return (
              <Card
                key={action.title}
                className={`rounded-lg border border-[#D8E6F2] bg-white py-0 shadow-[0_18px_45px_rgba(6,43,85,0.10)] transition duration-300 hover:-translate-y-1 hover:shadow-[0_22px_55px_rgba(6,43,85,0.15)] ${action.borderClass}`}
              >
                <CardContent className="flex h-full min-h-[250px] flex-col p-5 sm:p-6">
                  <div className={`flex size-13 items-center justify-center rounded-md ring-1 ${action.iconClass}`}>
                    <Icon size={23} />
                  </div>
                  <h2 className="mt-5 text-xl font-semibold text-[#0B1F33]">{action.title}</h2>
                  <p className="mt-3 flex-1 text-sm leading-6 text-[#536B7D]">{action.description}</p>
                  <Button asChild className={`mt-6 h-11 w-full justify-between px-3 font-semibold shadow-sm ${action.buttonClass}`}>
                    <Link to={resolveActionPath(action)}>
                      {action.cta}
                      <ArrowRight size={15} />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </section>

      <section id="billing-help" className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-14 lg:px-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase text-[#0057A8]">Why use this portal?</p>
            <h2 className="mt-2 text-2xl font-semibold text-[#0B1F33] sm:text-3xl">
              Built for modern telecom e-billing
            </h2>
          </div>
          <p className="max-w-xl text-sm leading-6 text-[#536B7D]">
            A focused SLT-MOBITEL gateway for bill viewing, payment access, and billing management
            without exposing private account details on the public page.
          </p>
        </div>

        <div className="mt-7 grid gap-4 md:grid-cols-3">
          {featureCards.map((feature) => {
            const Icon = feature.icon
            return (
              <Card
                key={feature.title}
                className="rounded-lg border border-[#DDE8F1] bg-white py-0 shadow-[0_12px_35px_rgba(6,43,85,0.06)] transition duration-300 hover:border-[#0057A8]/30 hover:shadow-[0_16px_40px_rgba(6,43,85,0.10)]"
              >
                <CardContent className="min-h-[190px] p-5">
                  <div className="flex size-11 items-center justify-center rounded-md bg-[#EEF6FD] text-[#0057A8]">
                    <Icon size={20} />
                  </div>
                  <h3 className="mt-4 text-base font-semibold text-[#0B1F33]">{feature.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-[#536B7D]">{feature.description}</p>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </section>

      <section id="support" className="mx-auto max-w-6xl px-4 pb-12 sm:px-6 lg:px-8">
        <div className="rounded-lg border border-[#D8E6F2] bg-white p-5 shadow-[0_16px_45px_rgba(6,43,85,0.08)] lg:flex lg:items-center lg:justify-between lg:gap-6 lg:p-6">
          <div className="flex items-start gap-4">
            <div className="flex size-12 shrink-0 items-center justify-center rounded-md bg-[#EAF8EE] text-[#248D36]">
              <Headphones size={22} />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-[#0B1F33]">Need help?</h2>
              <p className="mt-2 max-w-lg text-sm leading-6 text-[#536B7D]">
                Get assistance with billing questions, portal access, and privacy information.
              </p>
            </div>
          </div>

          <div className="mt-5 grid gap-2 sm:grid-cols-3 lg:mt-0 lg:min-w-[390px]">
            {supportLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-[#DDE8F1] bg-[#F7FAFD] px-3 text-sm font-medium text-[#0B1F33] transition hover:border-[#0057A8]/35 hover:bg-white hover:text-[#0057A8]"
              >
                <HelpCircle size={15} />
                {link.label}
              </a>
            ))}
          </div>
        </div>
      </section>

      <footer id="terms-privacy" className="border-t border-[#DDE8F1] bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-6 text-sm text-[#536B7D] sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <Brand tone="light" size="sm" />
          <p>Terms and privacy apply to all SLT-MOBITEL Billing Management portal access.</p>
        </div>
      </footer>
    </main>
  )
}
