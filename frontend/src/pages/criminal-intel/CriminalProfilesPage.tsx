import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Search, ChevronLeft, ChevronRight, Skull,
  UserCircle, Plus
} from 'lucide-react'
import api from '../../api/client'
import { INDIA_STATES_DISTRICTS, getDistrictsForState } from '../../data/indiaGeo'

interface CriminalListItem {
  id: number
  criminal_id: string
  full_name: string
  nicknames: string[] | null
  gender: string
  wanted_status: string
  danger_level: string
  gang_name: string | null
  total_arrests: number
  total_firs: number
  crime_categories: string[] | null
  last_known_state: string | null
  last_known_district: string | null
  created_at: string
}

export default function CriminalProfilesPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [criminals, setCriminals] = useState<CriminalListItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [wantedFilter, setWantedFilter] = useState('')
  const [dangerFilter, setDangerFilter] = useState('')
  const [stateFilter, setStateFilter] = useState('')
  const [districtFilter, setDistrictFilter] = useState('')
  const perPage = 20

  useEffect(() => {
    fetchCriminals()
  }, [page, wantedFilter, dangerFilter, stateFilter, districtFilter])

  useEffect(() => {
    const s = searchParams.get('search')
    if (s) {
      setSearch(s)
      fetchCriminals(s)
    }
  }, [searchParams])

  const fetchCriminals = async (searchOverride?: string) => {
    setLoading(true)
    try {
      const params: Record<string, string | number> = { page, per_page: perPage }
      const q = searchOverride ?? search
      if (q) params.search = q
      if (wantedFilter) params.wanted_status = wantedFilter
      if (dangerFilter) params.danger_level = dangerFilter
      if (stateFilter) params.state = stateFilter
      if (districtFilter) params.district = districtFilter
      const response = await api.get('/api/criminal-intelligence/', { params })
      setCriminals(response.data.items)
      setTotal(response.data.total)
    } catch (error) {
      console.error('Failed to fetch criminals:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    fetchCriminals()
  }

  const totalPages = Math.ceil(total / perPage)

  const dangerColors: Record<string, string> = {
    low: 'text-green-400 bg-green-500/10 border-green-500/20',
    medium: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    high: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
    extreme: 'text-red-400 bg-red-500/10 border-red-500/20',
  }

  const wantedBadge: Record<string, string> = {
    not_wanted: 'text-dark-400 bg-dark-700/50',
    wanted: 'text-amber-300 bg-amber-500/10 border border-amber-500/30',
    most_wanted: 'text-red-300 bg-red-500/10 border border-red-500/30',
    surrendered: 'text-blue-300 bg-blue-500/10 border border-blue-500/30',
    arrested: 'text-green-300 bg-green-500/10 border border-green-500/30',
    absconding: 'text-purple-300 bg-purple-500/10 border border-purple-500/30',
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-600 to-emerald-800 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Skull className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Criminal Profiles</h1>
            <p className="text-dark-400 text-sm">{total} criminals in database</p>
          </div>
        </div>
        <button
          onClick={() => navigate('/criminal-intel/profiles/new')}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" /> Add Criminal
        </button>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col md:flex-row gap-3">
        <form onSubmit={handleSearch} className="flex-1 flex items-center gap-2 bg-dark-800/80 border border-dark-700/50 rounded-xl px-4 py-2.5">
          <Search className="w-4 h-4 text-dark-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, ID, gang, alias..."
            className="flex-1 bg-transparent text-white placeholder-dark-400 outline-none text-sm"
          />
          <button type="submit" className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs rounded-lg">
            Search
          </button>
        </form>
        <div className="flex gap-2">
          <select
            value={wantedFilter}
            onChange={(e) => { setWantedFilter(e.target.value); setPage(1) }}
            className="bg-dark-800 border border-dark-700/50 rounded-xl px-3 py-2.5 text-sm text-white outline-none"
          >
            <option value="">All Status</option>
            <option value="wanted">Wanted</option>
            <option value="most_wanted">Most Wanted</option>
            <option value="absconding">Absconding</option>
            <option value="arrested">Arrested</option>
            <option value="surrendered">Surrendered</option>
          </select>
          <select
            value={dangerFilter}
            onChange={(e) => { setDangerFilter(e.target.value); setPage(1) }}
            className="bg-dark-800 border border-dark-700/50 rounded-xl px-3 py-2.5 text-sm text-white outline-none"
          >
            <option value="">All Danger</option>
            <option value="extreme">Extreme</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select
            value={stateFilter}
            onChange={(e) => { setStateFilter(e.target.value); setDistrictFilter(''); setPage(1) }}
            className="bg-dark-800 border border-dark-700/50 rounded-xl px-3 py-2.5 text-sm text-white outline-none"
          >
            <option value="">All States</option>
            {INDIA_STATES_DISTRICTS.map(s => (
              <option key={s.name} value={s.name}>{s.name}</option>
            ))}
          </select>
          <select
            value={districtFilter}
            onChange={(e) => { setDistrictFilter(e.target.value); setPage(1) }}
            disabled={!stateFilter}
            className="bg-dark-800 border border-dark-700/50 rounded-xl px-3 py-2.5 text-sm text-white outline-none disabled:opacity-40"
          >
            <option value="">All Districts</option>
            {stateFilter && getDistrictsForState(stateFilter).map(d => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map(i => <div key={i} className="h-16 skeleton" />)}
        </div>
      ) : criminals.length === 0 ? (
        <div className="text-center py-16">
          <UserCircle className="w-16 h-16 text-dark-600 mx-auto mb-4" />
          <p className="text-dark-400">No criminals found matching your criteria</p>
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="rounded-xl bg-dark-900/80 border border-dark-700/50 overflow-hidden"
        >
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-dark-900/50">
                <tr>
                  <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">Criminal ID</th>
                  <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">Name</th>
                  <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">Aliases</th>
                  <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">Gang</th>
                  <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">Danger</th>
                  <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">Status</th>
                  <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">Arrests</th>
                  <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">FIRs</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-800/50">
                {criminals.map((c) => (
                  <tr
                    key={c.criminal_id}
                    onClick={() => navigate(`/criminal-intel/profiles/${c.criminal_id}`)}
                    className="hover:bg-dark-800/50 cursor-pointer transition-colors"
                  >
                    <td className="px-5 py-3.5 text-sm font-mono text-emerald-400">{c.criminal_id}</td>
                    <td className="px-5 py-3.5">
                      <p className="text-sm text-white font-medium">{c.full_name}</p>
                    </td>
                    <td className="px-5 py-3.5 text-xs text-dark-300">
                      {(c.nicknames ?? []).slice(0, 2).join(', ') || '—'}
                    </td>
                    <td className="px-5 py-3.5 text-xs text-dark-300">{c.gang_name || '—'}</td>
                    <td className="px-5 py-3.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-medium uppercase border ${dangerColors[c.danger_level]}`}>
                        {c.danger_level}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${wantedBadge[c.wanted_status]}`}>
                        {c.wanted_status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-sm text-white text-center">{c.total_arrests}</td>
                    <td className="px-5 py-3.5 text-sm text-white text-center">{c.total_firs}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-1">
          <p className="text-xs text-dark-400">
            Showing {(page - 1) * perPage + 1}–{Math.min(page * perPage, total)} of {total}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-2 rounded-lg bg-dark-800 hover:bg-dark-700 disabled:opacity-30 text-white transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm text-dark-300">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-2 rounded-lg bg-dark-800 hover:bg-dark-700 disabled:opacity-30 text-white transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
