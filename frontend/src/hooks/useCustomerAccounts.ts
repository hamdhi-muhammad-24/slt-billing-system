import { useQuery } from '@tanstack/react-query'
import { listCustomerAccounts } from '../lib/api'

export function useCustomerAccounts(id: number) {
  return useQuery({
    queryKey: ['customerAccounts', id],
    queryFn: () => listCustomerAccounts(id),
  })
}
