import { useQuery } from '@tanstack/react-query'
import { listPayments } from '../lib/api'

export function usePayments(accountId: number) {
  return useQuery({
    queryKey: ['payments', accountId],
    queryFn: () => listPayments(accountId),
  })
}
