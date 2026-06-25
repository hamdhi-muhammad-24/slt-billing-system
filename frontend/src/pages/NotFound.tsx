import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthProvider'
import Brand from '../components/Brand'
import { Button } from '@/components/ui/button'

export default function NotFound() {
  const { session } = useAuth()
  const home = !session ? '/' : session.role === 'admin' ? '/admin' : '/app'

  return (
    <div className="min-h-svh flex flex-col items-center justify-center gap-6 text-center p-6">
      <Brand />
      <div className="flex flex-col gap-2">
        <p className="text-6xl font-bold text-primary">404</p>
        <p className="text-xl font-semibold">Page not found</p>
        <p className="text-muted-foreground text-sm max-w-xs mx-auto">
          The page you're looking for doesn't exist or may have been moved.
        </p>
      </div>
      <Button asChild>
        <Link to={home}>Go home</Link>
      </Button>
    </div>
  )
}
