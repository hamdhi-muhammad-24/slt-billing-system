import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthProvider'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [customerId, setCustomerId] = useState(1)

  function handleAdmin() {
    login({ role: 'admin' })
    navigate('/admin')
  }

  function handleCustomer() {
    login({ role: 'customer', customerId })
    navigate('/app')
  }

  return (
    <div className="flex min-h-svh items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Dev Login</CardTitle>
          <p className="text-sm text-muted-foreground">
            Development shim — not real authentication.
          </p>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          <Button onClick={handleAdmin} className="w-full">
            Continue as Admin
          </Button>

          <div className="flex flex-col gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="customer-id">Customer ID</Label>
              <Input
                id="customer-id"
                type="number"
                min={1}
                value={customerId}
                onChange={(e) => setCustomerId(Number(e.target.value))}
              />
            </div>
            <Button variant="outline" onClick={handleCustomer} className="w-full">
              Continue as Customer
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
