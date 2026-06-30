import { Route, Routes } from 'react-router-dom'
import { Toaster } from '@/components/ui/sonner'
import RequireRole from './auth/RequireRole'
import AdminLayout from './components/AdminLayout'
import CustomerLayout from './components/CustomerLayout'
import BillAccess from './pages/BillAccess'
import Login from './pages/Login'
import NotFound from './pages/NotFound'
import PayBill from './pages/PayBill'
import PublicPortal from './pages/PublicPortal'
import Dashboard from './pages/admin/Dashboard'
import Customers from './pages/admin/Customers'
import CustomerDetail from './pages/admin/CustomerDetail'
import AccountDetail from './pages/admin/AccountDetail'
import InvoiceDetail from './pages/admin/InvoiceDetail'
import Billing from './pages/admin/Billing'
import MyAccounts from './pages/customer/MyAccounts'
import CustomerAccountDetail from './pages/customer/CustomerAccountDetail'
import CustomerInvoiceDetail from './pages/customer/CustomerInvoiceDetail'

export default function App() {
  return (
    <>
      <Routes>
        <Route index element={<PublicPortal />} />
        <Route path="/bill-access" element={<BillAccess />} />
        <Route path="/login" element={<Login />} />
        <Route path="/pay-bill" element={<PayBill />} />

        <Route element={<RequireRole role="admin" />}>
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="customers" element={<Customers />} />
            <Route path="customers/:id" element={<CustomerDetail />} />
            <Route path="accounts/:id" element={<AccountDetail />} />
            <Route path="invoices/:id" element={<InvoiceDetail />} />
            <Route path="billing" element={<Billing />} />
          </Route>
        </Route>

        <Route element={<RequireRole role="customer" />}>
          <Route path="/app" element={<CustomerLayout />}>
            <Route index element={<MyAccounts />} />
            <Route path="accounts/:id" element={<CustomerAccountDetail />} />
            <Route path="invoices/:id" element={<CustomerInvoiceDetail />} />
          </Route>
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>

      <Toaster />
    </>
  )
}
