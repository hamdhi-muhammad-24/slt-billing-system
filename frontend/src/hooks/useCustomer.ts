import { useQuery } from '@tanstack/react-query'
import { getCustomer } from '../lib/api'

export function useCustomer(id: number) {
  return useQuery({
    queryKey: ['customer', id],
    queryFn: () => getCustomer(id),
  })
}
