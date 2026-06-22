import { useQuery } from '@tanstack/react-query'
import { getAccount } from '../lib/api'

export function useAccount(id: number) {
  return useQuery({
    queryKey: ['account', id],
    queryFn: () => getAccount(id),
  })
}
