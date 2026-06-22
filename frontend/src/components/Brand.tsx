// Drop the real SLT logo at frontend/public/slt-logo.png to replace the wordmark.
import { useState } from 'react'

export default function Brand() {
  const [hasImg, setHasImg] = useState(true)

  return (
    <div className="flex items-center gap-2">
      {hasImg
        ? (
          <img
            src="/slt-logo.png"
            alt="SLT"
            className="h-7 w-auto"
            onError={() => setHasImg(false)}
          />
        )
        : <span className="font-bold text-sm tracking-tight">SLT e-Bill</span>}
    </div>
  )
}
