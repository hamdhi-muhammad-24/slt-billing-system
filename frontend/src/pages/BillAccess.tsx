import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Download,
  FileText,
  LockKeyhole,
  Search,
  ShieldCheck,
  Smartphone,
} from 'lucide-react'
import Brand from '../components/Brand'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

type BillStep = 'lookup' | 'verify' | 'ready'

const journeySteps = [
  {
    icon: Search,
    title: 'Account lookup',
    text: 'Enter your billing account details to start secure bill access.',
  },
  {
    icon: Smartphone,
    title: 'Verification',
    text: 'Confirm access with a one-time verification code.',
  },
  {
    icon: Download,
    title: 'Bill ready',
    text: 'Open the verified bill summary and continue to PDF access.',
  },
]

export default function BillAccess() {
  const [step, setStep] = useState<BillStep>('lookup')
  const [accountNo, setAccountNo] = useState('')
  const [contact, setContact] = useState('')
  const [otp, setOtp] = useState('')

  function handleLookup(e: FormEvent) {
    e.preventDefault()
    setStep('verify')
  }

  function handleVerify(e: FormEvent) {
    e.preventDefault()
    setStep('ready')
  }

  return (
    <main className="min-h-svh overflow-hidden bg-[#F3F8FD] text-[#0B1F33]">
      <header className="relative z-20 border-b border-[#DCE8F2] bg-white/90 shadow-[0_4px_24px_rgba(6,43,85,0.05)] backdrop-blur-xl">
        <div className="mx-auto flex min-h-18 max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
          <Brand tone="light" size="md" />
          <div className="flex items-center gap-2">
            <Button asChild variant="outline" size="sm" className="h-9 border-[#CADAEA] bg-white px-3 text-[#05264A] shadow-sm hover:border-[#0066B3]/35 hover:bg-[#F4F8FB] hover:text-[#0066B3]">
              <Link to="/">
                <ArrowLeft size={14} />
                Portal
              </Link>
            </Button>
            <Button asChild size="sm" className="hidden h-9 bg-[linear-gradient(135deg,#05264A,#0066B3)] px-3 text-white shadow-sm hover:shadow-[0_10px_24px_rgba(0,102,179,0.22)] sm:inline-flex">
              <Link to="/login">
                Sign In
                <ArrowRight size={14} />
              </Link>
            </Button>
          </div>
        </div>
      </header>

      <section className="relative">
        <div className="absolute inset-x-0 top-0 h-80 bg-[linear-gradient(135deg,#05264A_0%,#063B73_52%,#0066B3_100%)]" />
        <div className="absolute inset-x-0 top-0 h-80 bg-[radial-gradient(circle_at_18%_18%,rgba(14,165,233,0.30),transparent_34%),radial-gradient(circle_at_88%_12%,rgba(57,181,74,0.18),transparent_28%)]" />
        <div className="absolute inset-x-0 top-0 h-80 opacity-25 [background-image:linear-gradient(rgba(255,255,255,0.14)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.14)_1px,transparent_1px)] [background-size:42px_42px]" />
        <div className="absolute inset-x-0 top-80 h-56 bg-[linear-gradient(180deg,rgba(243,248,253,0),#F3F8FD_72%)]" />

        <div className="relative mx-auto grid max-w-6xl gap-5 px-4 py-8 sm:px-6 sm:py-10 lg:grid-cols-[minmax(0,1fr)_430px] lg:items-stretch lg:px-8 lg:py-14">
          <section className="relative overflow-hidden rounded-lg border border-white/16 bg-[linear-gradient(145deg,rgba(5,38,74,0.98),rgba(6,59,115,0.96)_48%,rgba(0,102,179,0.90))] p-5 text-white shadow-[0_28px_80px_rgba(6,43,85,0.26)] sm:p-8 lg:min-h-[620px]">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_14%_12%,rgba(14,165,233,0.25),transparent_34%),radial-gradient(circle_at_92%_88%,rgba(57,181,74,0.16),transparent_32%)]" />
            <div className="absolute inset-0 opacity-20 [background-image:linear-gradient(rgba(255,255,255,0.12)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.12)_1px,transparent_1px)] [background-size:38px_38px]" />

            <div className="relative flex h-full flex-col">
              <p className="inline-flex max-w-full items-center gap-2 rounded-md border border-white/18 bg-white/12 px-3 py-1.5 text-sm font-medium text-white/90 shadow-[0_12px_30px_rgba(0,0,0,0.16)] backdrop-blur-md">
                <ShieldCheck size={15} />
                <span>Secure bill verification</span>
              </p>

              <div className="mt-8 max-w-xl sm:mt-10 lg:mt-16">
                <h1 className="text-3xl font-semibold leading-[1.08] sm:text-5xl">
                  View your SLT-MOBITEL bill securely
                </h1>
                <p className="mt-5 text-base leading-7 text-white/76">
                  Start with your account details, verify access, and continue to a protected bill
                  view prepared for PDF statement access.
                </p>
              </div>

              <div className="mt-8 grid gap-3 sm:max-w-lg">
                {journeySteps.map((item, index) => {
                  const Icon = item.icon
                  const isActive =
                    (step === 'lookup' && index === 0) ||
                    (step === 'verify' && index === 1) ||
                    (step === 'ready' && index === 2)
                  return (
                    <div
                      key={item.title}
                      className="flex gap-3 rounded-md border border-white/14 bg-white/10 p-3.5 text-sm text-white/88 shadow-sm backdrop-blur"
                    >
                      <span className={`flex size-10 shrink-0 items-center justify-center rounded-md ${isActive ? 'bg-white text-[#0066B3]' : 'bg-white/10 text-white/75'}`}>
                        <Icon size={18} />
                      </span>
                      <span>
                        <span className="block font-semibold">{item.title}</span>
                        <span className="mt-1 block leading-5 text-white/66">{item.text}</span>
                      </span>
                    </div>
                  )
                })}
              </div>

              <div className="mt-auto hidden pt-10 lg:block">
                <div className="rounded-lg border border-white/14 bg-white/10 p-4 shadow-[0_18px_50px_rgba(0,0,0,0.14)] backdrop-blur">
                  <div className="flex items-center gap-2 text-sm font-semibold text-white">
                    <CheckCircle2 size={16} className="text-[#6FE17D]" />
                    Bill access is protected before customer data is shown
                  </div>
                </div>
              </div>
            </div>
          </section>

          <Card className="rounded-lg border border-[#D8E6F2] bg-white/95 py-0 shadow-[0_28px_80px_rgba(6,43,85,0.16)] backdrop-blur">
            <CardContent className="p-5 sm:p-7">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold uppercase text-[#0066B3]">Bill access</p>
                  <h2 className="mt-2 text-3xl font-semibold text-[#0B1F33]">
                    {step === 'lookup' ? 'Find your bill' : step === 'verify' ? 'Verify access' : 'Bill preview ready'}
                  </h2>
                  <p className="mt-2 text-sm leading-6 text-[#52677A]">
                    {step === 'lookup'
                      ? 'Use your account number and registered contact to begin secure verification.'
                      : step === 'verify'
                        ? 'Enter the one-time code sent to your registered contact.'
                        : 'Your bill access journey is ready for secure PDF viewing.'}
                  </p>
                </div>
                <div className="hidden size-12 shrink-0 items-center justify-center rounded-md bg-[linear-gradient(135deg,#EAF4FF,#EAF8EE)] text-[#0066B3] ring-1 ring-[#0066B3]/10 sm:flex">
                  <FileText size={21} />
                </div>
              </div>

              {step === 'lookup' && (
                <form onSubmit={handleLookup} className="mt-7 grid gap-5">
                  <div className="grid gap-2">
                    <Label htmlFor="accountNo" className="text-sm font-medium text-[#0B1F33]">
                      Billing account number
                    </Label>
                    <Input
                      id="accountNo"
                      required
                      placeholder="Enter account number"
                      value={accountNo}
                      onChange={(e) => setAccountNo(e.target.value)}
                      className="h-11 border-[#CADAEA] bg-white text-[#0B1F33] shadow-sm placeholder:text-[#8CA1B4] focus-visible:border-[#0066B3] focus-visible:ring-[#0EA5E9]/25"
                    />
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="contact" className="text-sm font-medium text-[#0B1F33]">
                      Registered mobile or email
                    </Label>
                    <Input
                      id="contact"
                      required
                      placeholder="07X XXX XXXX or name@example.com"
                      value={contact}
                      onChange={(e) => setContact(e.target.value)}
                      className="h-11 border-[#CADAEA] bg-white text-[#0B1F33] shadow-sm placeholder:text-[#8CA1B4] focus-visible:border-[#0066B3] focus-visible:ring-[#0EA5E9]/25"
                    />
                  </div>

                  <Button type="submit" className="h-11 w-full justify-between bg-[linear-gradient(135deg,#0066B3,#0EA5E9)] px-3 font-semibold text-white shadow-sm hover:shadow-[0_14px_30px_rgba(0,102,179,0.24)]">
                    Request verification
                    <ArrowRight size={15} />
                  </Button>
                </form>
              )}

              {step === 'verify' && (
                <form onSubmit={handleVerify} className="mt-7 grid gap-5">
                  <div className="rounded-lg border border-[#DDE8F1] bg-[linear-gradient(135deg,#F3F8FD,#EAF8EE)] p-4">
                    <div className="flex gap-3">
                      <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-white text-[#248D36] shadow-sm ring-1 ring-[#39B54A]/15">
                        <Smartphone size={18} />
                      </div>
                      <p className="text-sm leading-6 text-[#52677A]">
                        A verification code is prepared for the registered contact linked to
                        account {accountNo || 'your account'}.
                      </p>
                    </div>
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="otp" className="text-sm font-medium text-[#0B1F33]">
                      Verification code
                    </Label>
                    <Input
                      id="otp"
                      required
                      placeholder="Enter 6-digit code"
                      value={otp}
                      onChange={(e) => setOtp(e.target.value)}
                      className="h-11 border-[#CADAEA] bg-white text-[#0B1F33] shadow-sm placeholder:text-[#8CA1B4] focus-visible:border-[#0066B3] focus-visible:ring-[#0EA5E9]/25"
                    />
                  </div>

                  <Button type="submit" className="h-11 w-full justify-between bg-[linear-gradient(135deg,#05264A,#0066B3)] px-3 font-semibold text-white shadow-sm hover:shadow-[0_14px_30px_rgba(0,102,179,0.24)]">
                    Verify and continue
                    <ArrowRight size={15} />
                  </Button>
                </form>
              )}

              {step === 'ready' && (
                <div className="mt-7 grid gap-4">
                  <div className="rounded-lg border border-[#DDE8F1] bg-[linear-gradient(135deg,#FFFFFF,#F3F8FD)] p-4 shadow-sm">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold text-[#0B1F33]">Latest bill</p>
                        <p className="mt-1 text-sm text-[#52677A]">Statement copy and PDF access are ready.</p>
                      </div>
                      <span className="rounded-full bg-[#EAF8EE] px-3 py-1 text-xs font-semibold text-[#248D36]">
                        Verified
                      </span>
                    </div>
                    <div className="mt-4 grid grid-cols-2 gap-2">
                      <div className="rounded-md border border-[#DDE8F1] bg-white p-3">
                        <p className="text-xs text-[#52677A]">Status</p>
                        <p className="mt-1 text-sm font-semibold text-[#0B1F33]">PDF ready</p>
                      </div>
                      <div className="rounded-md border border-[#DDE8F1] bg-white p-3">
                        <p className="text-xs text-[#52677A]">Access</p>
                        <p className="mt-1 text-sm font-semibold text-[#0066B3]">Protected</p>
                      </div>
                    </div>
                  </div>

                  <Button asChild className="h-11 w-full justify-between bg-[linear-gradient(135deg,#05264A,#0066B3)] px-3 font-semibold text-white shadow-sm hover:shadow-[0_14px_30px_rgba(0,102,179,0.24)]">
                    <Link to="/login">
                      Open secure bill workspace
                      <LockKeyhole size={15} />
                    </Link>
                  </Button>
                </div>
              )}

              <div className="mt-6 rounded-lg border border-[#DDE8F1] bg-[#F7FAFD] p-4">
                <div className="flex gap-3">
                  <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-[#EAF8EE] text-[#248D36]">
                    <ShieldCheck size={18} />
                  </div>
                  <p className="text-sm leading-6 text-[#52677A]">
                    Public bill access should be connected to OTP and secure PDF token APIs before
                    displaying real customer billing data.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  )
}
