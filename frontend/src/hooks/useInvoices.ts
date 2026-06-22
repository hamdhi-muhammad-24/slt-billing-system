import { useQuery } from '@tanstack/react-query'
import { listInvoices } from '../lib/api'

export function useInvoices(accountId: number) {
  return useQuery({
    queryKey: ['invoices', accountId],
    queryFn: () => listInvoices(accountId),
  })
}
