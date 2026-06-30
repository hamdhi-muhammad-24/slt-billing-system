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
      <header className="sticky top-0 z-40 border-b border-[#DCE8F2] bg-white/90 shadow-[0_4px_24px_rgba(6,43,85,0.05)] backdrop-blur-xl">
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

              <Button asChild size="sm" className="h-9 bg-[linear-gradient(135deg,#05264A,#0066B3)] px-3 text-white shadow-sm hover:shadow-[0_10px_24px_rgba(0,102,179,0.22)]">
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
        <div className="absolute inset-0 bg-[linear-gradient(135deg,#05264A_0%,#063B73_48%,#0066B3_100%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_16%,rgba(14,165,233,0.32),transparent_34%),radial-gradient(circle_at_84%_12%,rgba(57,181,74,0.20),transparent_30%),radial-gradient(circle_at_52%_100%,rgba(255,255,255,0.13),transparent_34%)]" />
        <div className="absolute inset-0 opacity-25 [background-image:linear-gradient(rgba(255,255,255,0.12)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.12)_1px,transparent_1px)] [background-size:44px_44px]" />
        <div className="absolute inset-x-0 bottom-0 h-px bg-white/15" />

        <div className="relative mx-auto grid max-w-6xl gap-8 px-4 py-12 sm:px-6 sm:py-16 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-center lg:gap-10 lg:px-8 lg:py-20">
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
          </div>

          <aside className="rounded-lg border border-white/18 bg-white/12 p-5 shadow-[0_28px_80px_rgba(0,0,0,0.24)] backdrop-blur-xl">
            <div className="flex items-center gap-3 border-b border-white/15 pb-5">
              <div className="flex size-12 shrink-0 items-center justify-center rounded-md bg-white text-[#0066B3] shadow-[0_12px_28px_rgba(255,255,255,0.16)]">
                <ReceiptText size={22} />
              </div>
              <div>
                <h2 className="text-lg font-semibold">Billing gateway</h2>
                <p className="mt-1 text-sm leading-5 text-white/72">
                  Secure access preview for bill and account tasks.
                </p>
              </div>
            </div>

            <div className="mt-5 grid gap-2.5">
              {[
                'Verified customer bill access',
                'Authenticated payment entry',
                'Role-based staff administration',
              ].map((item) => (
                <div key={item} className="flex items-center gap-3 rounded-md border border-white/10 bg-white/8 px-3 py-3 text-sm text-white/86 shadow-sm">
                  <CheckCircle2 size={16} className="shrink-0 text-[#6FE17D]" />
                  <span>{item}</span>
                </div>
              ))}
            </div>

            <div className="mt-5 rounded-lg border border-white/14 bg-white/10 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-medium uppercase text-white/55">Secure workflow</p>
                  <p className="mt-1 text-xl font-semibold">Billing data protected</p>
                </div>
                <span className="rounded-full bg-[#39B54A]/18 px-3 py-1 text-xs font-semibold text-[#8CF09B]">
                  Protected
                </span>
              </div>

              <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-3">
                <div className="rounded-md border border-white/10 bg-white/8 p-3">
                  <p className="text-xs text-white/55">Verification</p>
                  <p className="mt-1 text-sm font-semibold">Required</p>
                </div>
                <div className="rounded-md border border-white/10 bg-white/8 p-3">
                  <p className="text-xs text-white/55">PDF access</p>
                  <p className="mt-1 text-sm font-semibold">After sign in</p>
                </div>
                <div className="rounded-md border border-white/10 bg-white/8 p-3">
                  <p className="text-xs text-white/55">Payment path</p>
                  <p className="mt-1 text-sm font-semibold text-[#8CF09B]">Secure</p>
                </div>
              </div>

              <div className="mt-4 h-2 rounded-full bg-white/12">
                <div className="h-2 w-3/4 rounded-full bg-[linear-gradient(90deg,#39B54A,#0EA5E9)]" />
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
                className={`relative overflow-hidden rounded-lg border border-[#D8E6F2] bg-white py-0 shadow-[0_18px_45px_rgba(6,43,85,0.10)] transition duration-300 hover:-translate-y-1 hover:shadow-[0_26px_62px_rgba(6,43,85,0.16)] ${action.borderClass}`}
              >
                <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${action.accentClass}`} />
                <CardContent className="flex h-full min-h-[250px] flex-col p-5 sm:p-6">
                  <div className="flex items-start justify-between gap-3">
                    <div className={`flex size-14 items-center justify-center rounded-md ${action.iconClass}`}>
                      <Icon size={24} />
                    </div>
                    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${action.helperClass}`}>
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
        <div className="relative overflow-hidden rounded-xl border border-[#D8E6F2] bg-[linear-gradient(135deg,#FFFFFF_0%,#F3F8FD_54%,#EAF8EE_100%)] p-5 shadow-[0_18px_50px_rgba(6,43,85,0.08)] sm:p-7">
          <div className="absolute inset-0 opacity-50 [background-image:linear-gradient(rgba(0,102,179,0.06)_1px,transparent_1px),linear-gradient(90deg,rgba(0,102,179,0.06)_1px,transparent_1px)] [background-size:36px_36px]" />
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
                  className="rounded-lg border border-white/80 bg-white/90 py-0 shadow-[0_12px_35px_rgba(6,43,85,0.07)] backdrop-blur transition duration-300 hover:-translate-y-0.5 hover:border-[#0066B3]/30 hover:shadow-[0_18px_44px_rgba(6,43,85,0.12)]"
                >
                  <CardContent className="min-h-[190px] p-5">
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
