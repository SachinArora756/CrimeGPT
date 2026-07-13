import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  PlusCircle, Search, Filter, Calendar, MapPin, User, Shield,
  ChevronLeft, ChevronRight, Edit2, X, Check,
} from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../api/client'
import { useAuthStore } from '../store/authStore'
import { useCaseStore } from '../store/caseStore'

export default function CasesPage() {
  const {
    cases, total, page, search, statusFilter, loading,
    fetchCases, setPage: setStorePage, setSearch: setStoreSearch, setStatusFilter: setStoreStatusFilter,
    updateCaseInStore,
  } = useCaseStore()
  const [editingCase, setEditingCase] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [localSearch, setLocalSearch] = useState(search)
  const { hasMinRole } = useAuthStore()

  const perPage = 15

  useEffect(() => {
    fetchCases({ page, status: statusFilter })
  }, [page, statusFilter])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setStoreSearch(localSearch)
    setStorePage(1)
    fetchCases({ page: 1, search: localSearch, status: statusFilter, force: true })
  }

  const saveTitle = async (publicId: string) => {
    try {
      await api.put(`/api/cases/${publicId}`, { title: editTitle })
      toast.success('Title updated')
      setEditingCase(null)
      updateCaseInStore(publicId, { title: editTitle })
    } catch {
      toast.error('Failed to update title')
    }
  }

  const priorityColors: Record<string, string> = {
    critical: 'text-red-400 bg-red-500/10 border-red-500/30',
    high: 'text-orange-400 bg-orange-500/10 border-orange-500/30',
    medium: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
    low: 'text-green-400 bg-green-500/10 border-green-500/30',
  }

  const statusColors: Record<string, string> = {
    registered: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    investigating: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    chargesheet_filed: 'bg-green-500/20 text-green-400 border-green-500/30',
    closed: 'bg-dark-500/20 text-dark-300 border-dark-500/30',
  }

  const totalPages = Math.ceil(total / perPage)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Cases</h1>
          <p className="text-dark-400 text-sm mt-1">{total} total cases</p>
        </div>
        <Link to="/cases/new" className="btn-primary flex items-center gap-2">
          <PlusCircle className="w-4 h-4" />
          New Case
        </Link>
      </div>

      {/* Search & Filter */}
      <div className="flex gap-3">
        <form onSubmit={handleSearch} className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
          <input
            type="text"
            placeholder="Search by name, FIR number, offense..."
            className="input pl-10"
            value={localSearch}
            onChange={(e) => setLocalSearch(e.target.value)}
          />
        </form>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
          <select
            className="input pl-10 w-48"
            value={statusFilter}
            onChange={(e) => { setStoreStatusFilter(e.target.value); setStorePage(1) }}
          >
            <option value="">All Status</option>
            <option value="registered">Registered</option>
            <option value="investigating">Investigating</option>
            <option value="chargesheet_filed">Chargesheet Filed</option>
            <option value="closed">Closed</option>
          </select>
        </div>
      </div>

      {/* Case Cards */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="card animate-pulse h-48 bg-dark-800/50" />
          ))}
        </div>
      ) : cases.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-dark-400 text-lg">No cases found</p>
          <Link to="/cases/new" className="btn-primary mt-4 inline-flex items-center gap-2">
            <PlusCircle className="w-4 h-4" /> Create First Case
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {cases.map((c, i) => (
            <motion.div
              key={c.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              className="group relative rounded-xl bg-dark-900/80 border border-dark-700 hover:border-primary-600/40 transition-all hover:shadow-lg hover:shadow-primary-500/5 overflow-hidden"
            >
              {/* Priority indicator */}
              <div className={`absolute top-0 left-0 right-0 h-0.5 ${
                c.priority === 'critical' ? 'bg-red-500' :
                c.priority === 'high' ? 'bg-orange-500' :
                c.priority === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
              }`} />

              <Link to={`/cases/${c.public_id}`} className="block p-4">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    {editingCase === c.public_id ? (
                      <div className="flex items-center gap-1" onClick={(e) => e.preventDefault()}>
                        <input
                          type="text"
                          className="input py-0.5 px-2 text-sm w-full"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onKeyDown={(e) => { if (e.key === 'Enter') saveTitle(c.public_id); if (e.key === 'Escape') setEditingCase(null) }}
                          autoFocus
                        />
                        <button onClick={(e) => { e.preventDefault(); saveTitle(c.public_id) }} className="p-1 text-green-400 hover:text-green-300"><Check className="w-3 h-3" /></button>
                        <button onClick={(e) => { e.preventDefault(); setEditingCase(null) }} className="p-1 text-dark-400 hover:text-white"><X className="w-3 h-3" /></button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1">
                        <h3 className="text-white font-semibold text-sm truncate">
                          {c.title || c.fir_number}
                        </h3>
                        {hasMinRole('sho') && (
                          <button
                            onClick={(e) => { e.preventDefault(); setEditingCase(c.public_id); setEditTitle(c.title || c.fir_number) }}
                            className="opacity-0 group-hover:opacity-100 p-1 text-dark-400 hover:text-white transition-opacity"
                          >
                            <Edit2 className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    )}
                    <p className="text-dark-400 text-xs mt-0.5">{c.fir_number}</p>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {c.priority && (
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase border ${priorityColors[c.priority] || priorityColors.medium}`}>
                        {c.priority}
                      </span>
                    )}
                  </div>
                </div>

                {/* Details */}
                <div className="space-y-2 mb-3">
                  <div className="flex items-center gap-2 text-xs">
                    <User className="w-3 h-3 text-dark-500" />
                    <span className="text-dark-300 truncate">Complainant: {c.complainant_name}</span>
                  </div>
                  {c.accused_name && c.accused_name !== '0' && (
                    <div className="flex items-center gap-2 text-xs">
                      <Shield className="w-3 h-3 text-dark-500" />
                      <span className="text-dark-300 truncate">Accused: {c.accused_name}</span>
                    </div>
                  )}
                  {c.offense_type && (
                    <div className="flex items-center gap-2 text-xs">
                      <MapPin className="w-3 h-3 text-dark-500" />
                      <span className="text-dark-300 truncate">{c.offense_type}</span>
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between pt-3 border-t border-dark-800">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${statusColors[c.status] || ''}`}>
                    {c.status.replace('_', ' ').toUpperCase()}
                  </span>
                  <div className="flex items-center gap-1 text-dark-500">
                    <Calendar className="w-3 h-3" />
                    <span className="text-[10px]">{new Date(c.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setStorePage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="p-2 rounded-lg bg-dark-800 text-dark-300 hover:text-white hover:bg-dark-700 disabled:opacity-30 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
            const pageNum = page <= 3 ? i + 1 : page + i - 2
            if (pageNum < 1 || pageNum > totalPages) return null
            return (
              <button
                key={pageNum}
                onClick={() => setStorePage(pageNum)}
                className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${
                  page === pageNum
                    ? 'bg-primary-600 text-white'
                    : 'bg-dark-800 text-dark-300 hover:text-white hover:bg-dark-700'
                }`}
              >
                {pageNum}
              </button>
            )
          })}
          <button
            onClick={() => setStorePage(Math.min(totalPages, page + 1))}
            disabled={page >= totalPages}
            className="p-2 rounded-lg bg-dark-800 text-dark-300 hover:text-white hover:bg-dark-700 disabled:opacity-30 transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  )
}
