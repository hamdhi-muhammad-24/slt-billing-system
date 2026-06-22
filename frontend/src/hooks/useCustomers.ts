import { useQuery } from '@tanstack/react-query'
import { listCustomers } from '../lib/api'

export function useCustomers(limit = 50, offset = 0) {
  return useQuery({
    queryKey: ['customers', limit, offset],
    queryFn: () => listCustomers({ limit, offset }),
  })
}
