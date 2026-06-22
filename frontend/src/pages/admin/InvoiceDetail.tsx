import { useParams } from 'react-router-dom'
import { useInvoice } from '../../hooks/useInvoice'
import { Loading, ErrorState } from '../../components/states'
import { ApiError } from '../../lib/api'
import InvoiceSnapshotCard from '../../components/InvoiceSnapshotCard'

export default function InvoiceDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: inv, isPending, error } = useInvoice(Number(id))

  if (isPending) return <Loading />
  if (error) return <ErrorState detail={error instanceof ApiError ? error.detail : error.message} />

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Invoice — {inv.period}</h1>
      <InvoiceSnapshotCard invoice={inv} />
    </div>
  )
}
