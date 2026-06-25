import { useState } from 'react'
import { Wifi } from 'lucide-react'

export default function Brand() {
  const [hasImg, setHasImg] = useState(true)

  return (
    <div className="flex items-center gap-2.5">
      {hasImg ? (
        <img
          src="/slt-logo.png"
          alt="SLT"
          className="h-7 w-auto"
          onError={() => setHasImg(false)}
        />
      ) : (
        <>
          <div className="flex size-7 shrink-0 items-center justify-center rounded-lg gradient-primary shadow-sm">
            <Wifi size={13} className="text-white" />
          </div>
          <span className="font-bold text-sm tracking-tight">SLT e-Bill</span>
        </>
      )}
    </div>
  )
}
