import { useState } from 'react'
import { Network } from 'lucide-react'
import { cn } from '@/lib/utils'

type BrandTone = 'light' | 'dark'
type BrandSize = 'sm' | 'md' | 'lg'

interface BrandProps {
  tone?: BrandTone
  size?: BrandSize
  showSystemName?: boolean
  className?: string
}

const logoSrc: Record<BrandTone, string> = {
  light: '/sltmobitel-logo-light.png',
  dark: '/sltmobitel-logo-dark.png',
}

const logoClass: Record<BrandSize, string> = {
  sm: 'h-6 max-w-[132px]',
  md: 'h-8 max-w-[172px]',
  lg: 'h-10 max-w-[220px]',
}

export default function Brand({
  tone = 'light',
  size = 'md',
  showSystemName = true,
  className,
}: BrandProps) {
  const [hasImg, setHasImg] = useState(true)

  return (
    <div className={cn('flex min-w-0 items-center gap-3', className)}>
      {hasImg ? (
        <img
          src={logoSrc[tone]}
          alt="SLT-MOBITEL"
          className={cn('w-auto shrink-0 object-contain', logoClass[size])}
          onError={() => setHasImg(false)}
        />
      ) : (
        <>
          <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground shadow-sm">
            <Network size={15} />
          </div>
          <span className="font-semibold text-sm tracking-tight">SLT-MOBITEL</span>
        </>
      )}
      {showSystemName && (
        <span
          className={cn(
            'hidden border-l pl-3 text-xs font-medium leading-tight sm:block',
            tone === 'dark'
              ? 'border-white/20 text-white/75'
              : 'border-border text-muted-foreground',
          )}
        >
          Billing Management
        </span>
      )}
    </div>
  )
}
