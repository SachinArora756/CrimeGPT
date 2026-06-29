import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { PlusCircle, Search, Filter } from 'lucide-react'
import api from '../api/client'

interface Case {
  id: number
  fir_number: string
  complainant_name: string
  accused_name: string | null
  status: string
  offense_type: string | null
  incident_date: string | null
  created_at: string
}

export default function CasesPage() {
  const [cases, setCases] = useState<Case[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadCases()
  }, [page, statusFilter])

  const loadCases = async () => {
    setLoading(true)
    try {
      const params: Record<string, string | number> = { page, per_page: 15 }
      if (statusFilter) params.status = statusFilter
      if (search) params.search = search
      const response = await api.get('/api/cases/', { params })
      setCases(response.data.cases)
      setTotal(response.data.total)
    } catch {
      setCases([])
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    loadCases()
  }

  const statusColors: Record<string, string> = {
    registered: 'bg-blue-500/20 text-blue-400',
    investigating: 'bg-yellow-500/20 text-yellow-400',
    chargesheet_filed: 'bg-green-500/20 text-green-400',
    closed: 'bg-dark-500/20 text-dark-300',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Cases</h1>
        <Link to="/cases/new" className="btn-primary flex items-center gap-2">
          <PlusCircle className="w-4 h-4" />
          New Case
        </Link>
      </div>

      <div className="flex gap-4">
        <form onSubmit={handleSearch} className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
          <input
            type="text"
            placeholder="Search by name, FIR number..."
            className="input pl-10"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </form>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
          <select
            className="input pl-10 w-48"
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
          >
            <option value="">All Status</option>
            <option value="registered">Registered</option>
            <option value="investigating">Investigating</option>
            <option value="chargesheet_filed">Chargesheet Filed</option>
            <option value="closed">Closed</option>
          </select>
        </div>
      </div>

      <div className="card overflow-hidden p-0">
        <table className="w-full">
          <thead className="bg-dark-900">
            <tr>
              <th className="text-left px-6 py-4 text-sm font-medium text-dark-300">FIR No.</th>
              <th className="text-left px-6 py-4 text-sm font-medium text-dark-300">Complainant</th>
              <th className="text-left px-6 py-4 text-sm font-medium text-dark-300">Accused</th>
              <th className="text-left px-6 py-4 text-sm font-medium text-dark-300">Offense</th>
              <th className="text-left px-6 py-4 text-sm font-medium text-dark-300">Status</th>
              <th className="text-left px-6 py-4 text-sm font-medium text-dark-300">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-700">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-dark-400">Loading...</td>
              </tr>
            ) : cases.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-dark-400">No cases found</td>
              </tr>
            ) : (
              cases.map((c, i) => (
                <motion.tr
                  key={c.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.05 }}
                  className="hover:bg-dark-800/50 cursor-pointer"
                >
                  <td className="px-6 py-4">
                    <Link to={`/cases/${c.id}`} className="text-primary-400 font-medium hover:text-primary-300">
                      {c.fir_number}
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-white">{c.complainant_name}</td>
                  <td className="px-6 py-4 text-dark-300">{c.accused_name || '—'}</td>
                  <td className="px-6 py-4 text-dark-300">{c.offense_type || '—'}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[c.status] || ''}`}>
                      {c.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-dark-400 text-sm">
                    {new Date(c.created_at).toLocaleDateString()}
                  </td>
                </motion.tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {total > 15 && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="btn-secondary disabled:opacity-50"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-dark-300">
            Page {page} of {Math.ceil(total / 15)}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={page * 15 >= total}
            className="btn-secondary disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
