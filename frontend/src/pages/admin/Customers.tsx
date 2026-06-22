import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useCustomers } from '../../hooks/useCustomers'
import { Loading, ErrorState, Empty } from '../../components/states'
import { ApiError } from '../../lib/api'

const PAGE_SIZE = 50

export default function Customers() {
  const [offset, setOffset] = useState(0)
  const { data, isPending, error } = useCustomers(PAGE_SIZE, offset)

  if (isPending) return <Loading />
  if (error) return <ErrorState detail={error instanceof ApiError ? error.detail : error.message} />
  if (data.items.length === 0) return <Empty label="No customers found." />

  const totalPages = Math.ceil(data.total / PAGE_SIZE)
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold">Customers</h1>
      <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-2 text-left font-medium">ID</th>
              <th className="px-4 py-2 text-left font-medium">Name</th>
              <th className="px-4 py-2 text-left font-medium">NIC</th>
              <th className="px-4 py-2 text-left font-medium">Email</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((c) => (
              <tr key={c.id} className="border-t border-foreground/5 hover:bg-muted/30">
                <td className="px-4 py-2">{c.id}</td>
                <td className="px-4 py-2">
                  <Link to={`/admin/customers/${c.id}`} className="underline">
                    {c.name}
                  </Link>
                </td>
                <td className="px-4 py-2">{c.nic}</td>
                <td className="px-4 py-2">{c.email}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="flex items-center gap-4 text-sm">
          <button
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            disabled={offset === 0}
            className="underline disabled:opacity-40"
          >
            Previous
          </button>
          <span>Page {currentPage} of {totalPages}</span>
          <button
            onClick={() => setOffset(offset + PAGE_SIZE)}
            disabled={currentPage >= totalPages}
            className="underline disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
