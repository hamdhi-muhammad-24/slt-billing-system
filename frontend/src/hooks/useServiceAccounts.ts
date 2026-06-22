import { useQuery } from '@tanstack/react-query'
import { listServiceAccounts } from '../lib/api'

export function useServiceAccounts(id: number) {
  return useQuery({
    queryKey: ['serviceAccounts', id],
    queryFn: () => listServiceAccounts(id),
  })
}
