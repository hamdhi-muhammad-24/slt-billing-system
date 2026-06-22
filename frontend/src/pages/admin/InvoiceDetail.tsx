import { useParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useInvoice } from '../../hooks/useInvoice'
import { ErrorState } from '../../components/states'
import { CardSkeleton } from '../../components/ui-kit/Skeletons'
import { PageHeader } from '../../components/ui-kit/PageHeader'
import { ApiError, downloadInvoicePdf } from '../../lib/api'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'
import InvoiceSnapshotCard from '../../components/InvoiceSnapshotCard'

export default function InvoiceDetail() {
  const { id } = useParams<{ id: string }>()
  const invoiceId = Number(id)

  const { data: inv, isPending, error } = useInvoice(invoiceId)

  const download = useMutation({
    mutationFn: () => downloadInvoicePdf(invoiceId),
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.detail : 'PDF download failed.')
    },
  })

  if (isPending) return (
    <>
      <PageHeader title="Invoice" breadcrumbs={[{ label: 'Account' }]} />
      <CardSkeleton />
    </>
  )
  if (error) return <ErrorState detail={error instanceof ApiError ? error.detail : error.message} />

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={`Invoice — ${inv.period}`}
        breadcrumbs={[
          { label: 'Customers', to: '/admin/customers' },
          { label: `Account ${inv.account_id}`, to: `/admin/accounts/${inv.account_id}` },
          { label: inv.period },
        ]}
        actions={
          <Button
            size="sm"
            disabled={download.isPending}
            onClick={() => download.mutate()}
          >
            {download.isPending ? 'Downloading…' : 'Download PDF'}
          </Button>
        }
      />
      <InvoiceSnapshotCard invoice={inv} />
    </div>
  )
}
