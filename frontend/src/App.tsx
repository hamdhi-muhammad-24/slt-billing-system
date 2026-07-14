import { Route, Routes } from 'react-router-dom'
import { Toaster } from '@/components/ui/sonner'
import RequireRole from './auth/RequireRole'
import AdminLayout from './components/AdminLayout'
import Admin1Layout from './components/Admin1Layout'
import BillAccess from './pages/BillAccess'
import Login from './pages/Login'
import NotFound from './pages/NotFound'
import PayBill from './pages/PayBill'
import PublicPortal from './pages/PublicPortal'
import Dashboard from './pages/admin/Dashboard'
import GmfMonitor from './pages/admin/GmfMonitor'
import InvoicePreview from './pages/admin/InvoicePreview'
import GenerationHub from './pages/admin/GenerationHub'
import OutputArchive from './pages/admin/OutputArchive'
import ActivityLog from './pages/admin/ActivityLog'
import InvoiceTemplates from './pages/admin/InvoiceTemplates'
import ScheduleManager from './pages/admin/ScheduleManager'
import Admin1Dashboard from './pages/admin/Admin1Dashboard'
import UploadCenter from './pages/admin/UploadCenter'

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
            <Route path="gmf-monitor" element={<GmfMonitor />} />
            <Route path="invoice-preview" element={<InvoicePreview />} />
            <Route path="generation-hub" element={<GenerationHub />} />
            <Route path="output-archive" element={<OutputArchive />} />
            <Route path="activity-log" element={<ActivityLog />} />
            <Route path="invoice-templates" element={<InvoiceTemplates />} />
            <Route path="schedule-manager" element={<ScheduleManager />} />
          </Route>
        </Route>

        <Route element={<RequireRole role="admin1" />}>
          <Route path="/admin1" element={<Admin1Layout />}>
            <Route index element={<Admin1Dashboard />} />
            <Route path="gmf-monitor" element={<GmfMonitor />} />
            <Route path="upload-center" element={<UploadCenter />} />
          </Route>
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>

      <Toaster />
    </>
  )
}
