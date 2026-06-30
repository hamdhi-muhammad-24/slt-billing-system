import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Building2,
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
    description: 'Verify your account, view the latest bill, and continue to protected PDF access.',
    cta: 'View bill',
    helper: 'OTP verification',
    path: '/bill-access',
    accentClass: 'from-[#0EA5E9] to-[#0066B3]',
    iconClass: 'bg-[linear-gradient(135deg,#0EA5E9,#0066B3)] text-white shadow-[0_12px_28px_rgba(0,102,179,0.22)]',
    helperClass: 'bg-[#EAF4FF] text-[#0066B3]',
    buttonClass: 'bg-[linear-gradient(135deg,#0066B3,#0EA5E9)] text-white shadow-sm hover:shadow-[0_12px_26px_rgba(0,102,179,0.22)]',
    borderClass: 'hover:border-[#0057A8]/45',
  },
  {
    icon: CreditCard,
    title: 'Pay Bill',
    description: 'Look up your account and continue through a protected payment journey.',
    cta: 'Pay bill',
    helper: 'Secure payment path',
    path: '/pay-bill',
    accentClass: 'from-[#39B54A] to-[#11A870]',
    iconClass: 'bg-[linear-gradient(135deg,#39B54A,#11A870)] text-white shadow-[0_12px_28px_rgba(57,181,74,0.22)]',
    helperClass: 'bg-[#EAF8EE] text-[#248D36]',
    buttonClass: 'bg-[linear-gradient(135deg,#39B54A,#11A870)] text-white shadow-sm hover:shadow-[0_12px_26px_rgba(57,181,74,0.22)]',
    borderClass: 'hover:border-[#39B54A]/45',
  },
  {
    icon: LockKeyhole,
    title: 'Sign In',
    description: 'Enter the customer portal or staff billing console with your credentials.',
    cta: 'Sign in',
    helper: 'Customer or staff',
    path: 'signin' as const,
    accentClass: 'from-[#05264A] to-[#0066B3]',
    iconClass: 'bg-[linear-gradient(135deg,#05264A,#0066B3)] text-white shadow-[0_12px_28px_rgba(5,38,74,0.22)]',
    helperClass: 'bg-[#E9EEF5] text-[#05264A]',
    buttonClass: 'bg-[linear-gradient(135deg,#05264A,#063B73)] text-white shadow-sm hover:shadow-[0_12px_26px_rgba(5,38,74,0.24)]',
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

const heroHighlights = [
  {
    label: 'Bill access',
    text: 'Verified before viewing',
  },
  {
    label: 'Payments',
    text: 'Secure gateway path',
  },
  {
    label: 'Self-care',
    text: 'Customer and staff ready',
  },
]

const gatewayStatusRows = [
  {
    icon: FileText,
    label: 'Customer bill access',
    text: 'Protected viewing',
  },
  {
    icon: CreditCard,
    label: 'Payment gateway path',
    text: 'Secure entry',
  },
  {
    icon: Building2,
    label: 'Staff billing console',
    text: 'Role-aware access',
  },
]


const supportLinks = [
  { label: 'Contact support', href: 'mailto:support@slt.lk' },
  { label: 'Billing help', href: '#billing-help' },
  { label: 'Terms & privacy', href: '#terms-privacy' },
]

export default function PublicPortal() {
  const { session } = useAuth()
  const signInPath = !session ? '/login' : session.role === 'admin' ? '/admin' : '/app'

  function resolveActionPath(action: (typeof actionCards)[number]): string {
    if (action.path === 'signin') return signInPath
    return action.path
  }

  return (
    <main className="min-h-svh bg-[#F3F8FD] text-[#0B1F33]">
      <header className="sticky top-0 z-40 border-b border-[#DCE8F2] bg-white/95 shadow-[0_4px_24px_rgba(6,43,85,0.06)] backdrop-blur-xl">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="flex min-h-18 items-center justify-between gap-4 py-3">
            <Brand tone="light" size="md" />

            <div className="flex min-w-0 items-center gap-3">
              <nav className="hidden items-center gap-7 text-sm font-medium text-[#486276] md:flex">
                {navLinks.map((link) => (
                  <a
                    key={link.label}
                    href={link.href}
                    className="relative transition-colors after:absolute after:-bottom-2 after:left-0 after:h-0.5 after:w-0 after:rounded-full after:bg-[#0066B3] after:transition-all hover:text-[#0057A8] hover:after:w-full"
                  >
                    {link.label}
                  </a>
                ))}
              </nav>

              <Button asChild size="sm" className="h-10 shrink-0 bg-[linear-gradient(135deg,#05264A,#0066B3)] px-3.5 text-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-[0_10px_24px_rgba(0,102,179,0.22)]">
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

      <section className="relative overflow-hidden bg-[#05264A] text-white">
        <div className="absolute inset-0 bg-[linear-gradient(135deg,#031E3C_0%,#05264A_26%,#063B73_58%,#0066B3_100%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_16%,rgba(14,165,233,0.34),transparent_34%),radial-gradient(circle_at_84%_12%,rgba(57,181,74,0.19),transparent_30%),radial-gradient(circle_at_50%_104%,rgba(255,255,255,0.15),transparent_34%)]" />
        <div className="absolute inset-0 opacity-24 [background-image:linear-gradient(rgba(255,255,255,0.13)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.13)_1px,transparent_1px)] [background-size:44px_44px]" />
        <div className="absolute inset-x-0 bottom-0 h-px bg-white/15" />

        <div className="relative mx-auto grid max-w-6xl gap-8 px-4 py-12 sm:px-6 sm:py-16 lg:grid-cols-[minmax(0,1fr)_390px] lg:items-center lg:gap-12 lg:px-8 lg:py-20">
          <div className="max-w-3xl">
            <p className="inline-flex max-w-full items-center gap-2 rounded-md border border-white/20 bg-white/12 px-3 py-1.5 text-sm font-medium text-white/90 shadow-[0_12px_30px_rgba(0,0,0,0.18)] backdrop-blur-md">
              <ShieldCheck size={15} />
              <span className="min-w-0">Secure billing access for customers and administrators</span>
            </p>
            <h1 className="mt-6 max-w-4xl text-4xl font-semibold leading-[1.08] sm:text-5xl lg:text-6xl">
              Manage bills, payments, and service accounts in one secure place
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-white/78 sm:text-lg">
              View your latest bill, continue to payment access, or sign in to manage broadband,
              voice, PeoTV, and bundled services.
            </p>

            <div className="mt-8 grid max-w-2xl gap-3 sm:grid-cols-3">
              {heroHighlights.map((item) => (
                <div
                  key={item.label}
                  className="rounded-lg border border-white/15 bg-white/10 px-4 py-3 shadow-[0_14px_32px_rgba(0,0,0,0.16)] backdrop-blur-md transition hover:-translate-y-0.5 hover:bg-white/15"
                >
                  <p className="text-sm font-semibold text-white">{item.label}</p>
                  <p className="mt-1 text-xs leading-5 text-white/64">{item.text}</p>
                </div>
              ))}
            </div>
          </div>

          <aside className="relative overflow-hidden rounded-3xl border border-white/18 bg-[linear-gradient(155deg,rgba(255,255,255,0.06)_0%,rgba(255,255,255,0.02)_100%)] p-6 shadow-[0_32px_80px_rgba(0,0,0,0.30),inset_0_1px_0_rgba(255,255,255,0.22)] backdrop-blur-2xl">
            <div className="pointer-events-none absolute inset-x-0 top-0 h-36 bg-[linear-gradient(180deg,rgba(255,255,255,0.09),transparent)]" />
            <div className="pointer-events-none absolute -right-16 -top-16 size-40 rounded-full bg-[radial-gradient(circle,rgba(57,181,74,0.12),transparent_70%)]" />

            <div className="relative">
              <div className="flex items-start justify-between gap-4">
                <div className="flex min-w-0 items-center gap-3.5">
                  <div className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-white/15 text-white shadow-[0_8px_24px_rgba(0,0,0,0.18)] ring-1 ring-white/18">
                    <ReceiptText size={22} />
                  </div>
                  <div className="min-w-0">
                    <h2 className="text-lg font-semibold text-white">Billing gateway</h2>
                    <p className="mt-0.5 text-sm leading-5 text-white/72">
                      Secure access for billing and administration.
                    </p>
                  </div>
                </div>
                <span className="shrink-0 rounded-full border border-[#39B54A]/35 bg-[#39B54A]/18 px-2.5 py-1 text-xs font-semibold text-[#8CF09B]">
                  Secure
                </span>
              </div>

              <div className="mt-6 grid gap-2.5">
                {gatewayStatusRows.map((item) => {
                  const Icon = item.icon
                  return (
                    <div
                      key={item.label}
                      className="flex items-center gap-3.5 rounded-xl border border-white/10 bg-white/[0.08] p-3.5 transition-all duration-200 hover:border-white/20 hover:bg-white/[0.14]"
                    >
                      <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-white/15 text-white ring-1 ring-white/15">
                        <Icon size={16} />
                      </span>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-white">{item.label}</p>
                        <p className="mt-0.5 text-xs leading-4 text-white/72">{item.text}</p>
                      </div>
                    </div>
                  )
                })}
              </div>

              <div className="mt-6 flex items-center gap-2 border-t border-white/12 pt-4">
                <LockKeyhole size={13} className="shrink-0 text-white/70" />
                <p className="text-xs leading-5 text-white/70">Encrypted billing access, verified before viewing.</p>
              </div>
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
                className={`relative overflow-hidden rounded-lg border border-[#D8E6F2] bg-[linear-gradient(180deg,#FFFFFF_0%,#F8FBFE_100%)] py-0 shadow-[0_18px_45px_rgba(6,43,85,0.10)] transition duration-300 hover:-translate-y-1.5 hover:shadow-[0_28px_66px_rgba(6,43,85,0.17)] ${action.borderClass}`}
              >
                <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${action.accentClass}`} />
                <CardContent className="flex h-full min-h-[260px] flex-col p-5 sm:p-6">
                  <div className="flex items-start justify-between gap-3">
                    <div className={`flex size-14 items-center justify-center rounded-md ${action.iconClass}`}>
                      <Icon size={24} />
                    </div>
                    <span className={`whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold ${action.helperClass}`}>
                      {action.helper}
                    </span>
                  </div>
                  <h2 className="mt-5 text-xl font-semibold text-[#0B1F33]">{action.title}</h2>
                  <p className="mt-3 flex-1 text-sm leading-6 text-[#536B7D]">{action.description}</p>
                  <Button asChild className={`mt-6 h-11 w-full justify-between px-3 font-semibold shadow-sm ${action.buttonClass}`}>
                    <Link to={resolveActionPath(action)}>
                      <span className="truncate">{action.cta}</span>
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
        <div className="relative overflow-hidden rounded-lg border border-[#D8E6F2] bg-[linear-gradient(135deg,#FFFFFF_0%,#F3F8FD_60%,#EAF8EE_100%)] p-5 shadow-[0_18px_50px_rgba(6,43,85,0.08)] sm:p-7">
          <div className="absolute inset-0 opacity-45 [background-image:linear-gradient(rgba(0,102,179,0.055)_1px,transparent_1px),linear-gradient(90deg,rgba(0,102,179,0.055)_1px,transparent_1px)] [background-size:36px_36px]" />
          <div className="relative flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase text-[#0066B3]">Why use this portal?</p>
              <h2 className="mt-2 text-2xl font-semibold text-[#0B1F33] sm:text-3xl">
                Modern telecom e-billing made simple
              </h2>
            </div>
            <p className="max-w-xl text-sm leading-6 text-[#52677A]">
              A focused SLT-MOBITEL gateway for bill viewing, payment access, and billing management
              without exposing private account details on the public page.
            </p>
          </div>

          <div className="relative mt-7 grid gap-4 md:grid-cols-3">
            {featureCards.map((feature) => {
              const Icon = feature.icon
              return (
                <Card
                  key={feature.title}
                  className="rounded-lg border border-white/80 bg-white/95 py-0 shadow-[0_12px_35px_rgba(6,43,85,0.07)] backdrop-blur transition duration-300 hover:-translate-y-0.5 hover:border-[#0066B3]/30 hover:bg-white hover:shadow-[0_18px_44px_rgba(6,43,85,0.12)]"
                >
                  <CardContent className="min-h-[180px] p-5">
                    <div className="flex size-11 items-center justify-center rounded-md bg-[linear-gradient(135deg,#EAF4FF,#EAF8EE)] text-[#0066B3] ring-1 ring-[#0066B3]/10">
                      <Icon size={20} />
                    </div>
                    <h3 className="mt-4 text-base font-semibold text-[#0B1F33]">{feature.title}</h3>
                    <p className="mt-2 text-sm leading-6 text-[#52677A]">{feature.description}</p>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      <section id="support" className="mx-auto max-w-6xl px-4 pb-12 sm:px-6 lg:px-8">
        <div className="rounded-lg border border-[#D8E6F2] bg-[linear-gradient(135deg,#FFFFFF,#F3F8FD)] p-5 shadow-[0_16px_45px_rgba(6,43,85,0.08)] lg:flex lg:items-center lg:justify-between lg:gap-6 lg:p-6">
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
                className="inline-flex h-10 items-center justify-center gap-2 whitespace-nowrap rounded-full border border-[#DDE8F1] bg-white/90 px-3 text-sm font-medium text-[#0B1F33] shadow-sm transition hover:-translate-y-0.5 hover:border-[#0066B3]/35 hover:bg-white hover:text-[#0066B3] hover:shadow-[0_10px_24px_rgba(6,43,85,0.10)]"
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
