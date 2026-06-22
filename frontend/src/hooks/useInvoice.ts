import { useQuery } from '@tanstack/react-query'
import { getInvoice } from '../lib/api'

export function useInvoice(id: number) {
  return useQuery({
    queryKey: ['invoice', id],
    queryFn: () => getInvoice(id),
  })
}
