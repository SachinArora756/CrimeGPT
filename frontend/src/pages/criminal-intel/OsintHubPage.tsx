import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Globe, Phone, Mail, User, Car, Wifi, UserSearch,
  Search, Loader2, CheckCircle2, XCircle, MessageSquare,
  Link2, Clock, Shield
} from 'lucide-react'
import api from '../../api/client'
import toast from 'react-hot-toast'

interface OsintInvestigation {
  id: number
  identifier_type: string
  identifier_value: string
  findings: Record<string, any>
  officer_notes: string | null
  overall_status: string
  finding_statuses: Record<string, string> | null
  linked_criminal_id: number | null
  searched_by: number
  ai_model_used: string | null
  ai_generation_time_ms: number | null
  created_at: string
  updated_at: string
}

interface ListItem {
  id: number
  identifier_type: string
  identifier_value: string
  overall_status: string
  linked_criminal_id: number | null
  searched_by: number
  created_at: string
}

const IDENTIFIER_TYPES = [
  { key: 'phone', label: 'Phone', icon: Phone, placeholder: '+91 9876543210' },
  { key: 'email', label: 'Email', icon: Mail, placeholder: 'suspect@example.com' },
  { key: 'username', label: 'Username', icon: User, placeholder: '@username or handle' },
  { key: 'vehicle_plate', label: 'Vehicle', icon: Car, placeholder: 'HR26AB1234' },
  { key: 'ip_domain', label: 'IP/Domain', icon: Wifi, placeholder: '192.168.1.1 or example.com' },
  { key: 'person_name', label: 'Person', icon: UserSearch, placeholder: 'Full name of person' },
]

const statusColors: Record<string, string> = {
  unverified: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  verified: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
  rejected: 'text-red-400 bg-red-500/10 border-red-500/30',
}

export default function OsintHubPage() {
  const [selectedType, setSelectedType] = useState('phone')
  const [searchValue, setSearchValue] = useState('')
  const [searching, setSearching] = useState(false)
  const [currentInvestigation, setCurrentInvestigation] = useState<OsintInvestigation | null>(null)
  const [history, setHistory] = useState<ListItem[]>([])
  const [officerNotes, setOfficerNotes] = useState('')
  const [savingNotes, setSavingNotes] = useState(false)

  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    try {
      const res = await api.get('/api/criminal-intelligence/osint', { params: { per_page: 15 } })
      setHistory(res.data.items)
    } catch {
      // silent
    }
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchValue.trim()) return

    setSearching(true)
    setCurrentInvestigation(null)
    try {
      const res = await api.post('/api/criminal-intelligence/osint/search', {
        identifier_type: selectedType,
        identifier_value: searchValue.trim(),
      })
      setCurrentInvestigation(res.data)
      setOfficerNotes(res.data.officer_notes || '')
      toast.success(`OSINT analysis complete (${res.data.ai_generation_time_ms}ms)`)
      fetchHistory()
    } catch (err: unknown) {
      const error = err as { response?: { status?: number; data?: { detail?: string } } }
      if (error.response?.status === 429) {
        toast.error('Rate limit reached. Please wait before searching again.')
      } else {
        toast.error(error.response?.data?.detail || 'Search failed')
      }
    } finally {
      setSearching(false)
    }
  }

  const updateFindingStatus = async (findingKey: string, status: string) => {
    if (!currentInvestigation) return
    try {
      const res = await api.patch(`/api/criminal-intelligence/osint/${currentInvestigation.id}`, {
        finding_statuses: { [findingKey]: status },
      })
      setCurrentInvestigation(res.data)
    } catch {
      toast.error('Failed to update status')
    }
  }

  const saveNotes = async () => {
    if (!currentInvestigation) return
    setSavingNotes(true)
    try {
      const res = await api.patch(`/api/criminal-intelligence/osint/${currentInvestigation.id}`, {
        officer_notes: officerNotes,
      })
      setCurrentInvestigation(res.data)
      toast.success('Notes saved')
    } catch {
      toast.error('Failed to save notes')
    } finally {
      setSavingNotes(false)
    }
  }

  const setOverallStatus = async (status: string) => {
    if (!currentInvestigation) return
    try {
      const res = await api.patch(`/api/criminal-intelligence/osint/${currentInvestigation.id}`, {
        overall_status: status,
      })
      setCurrentInvestigation(res.data)
      fetchHistory()
      toast.success(`Marked as ${status}`)
    } catch {
      toast.error('Failed to update status')
    }
  }

  const loadInvestigation = async (id: number) => {
    try {
      const res = await api.get(`/api/criminal-intelligence/osint/${id}`)
      setCurrentInvestigation(res.data)
      setOfficerNotes(res.data.officer_notes || '')
      setSelectedType(res.data.identifier_type)
      setSearchValue(res.data.identifier_value)
    } catch {
      toast.error('Failed to load investigation')
    }
  }

  const renderFindings = () => {
    if (!currentInvestigation) return null
    const { findings, finding_statuses } = currentInvestigation
    const statuses = finding_statuses || {}

    const excludeKeys = ['summary', 'disclaimer', 'recommended_actions', 'raw_response']
    const findingKeys = Object.keys(findings).filter(k => !excludeKeys.includes(k))

    return (
      <div className="space-y-4">
        {/* Summary */}
        {findings.summary && (
          <div className="bg-dark-800/60 border border-dark-700/50 rounded-xl p-4">
            <p className="text-sm text-dark-200">{findings.summary}</p>
          </div>
        )}

        {/* Disclaimer */}
        <div className="flex items-center gap-2 px-3 py-2 bg-amber-500/5 border border-amber-500/20 rounded-lg">
          <Shield className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <p className="text-xs text-amber-300">AI-generated intelligence requires officer verification before use in any official capacity.</p>
        </div>

        {/* Finding Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {findingKeys.map((key) => {
            const value = findings[key]
            const findingStatus = statuses[key] || 'unverified'
            return (
              <motion.div
                key={key}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-dark-800/80 border border-dark-700/50 rounded-xl p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-xs font-semibold text-purple-300 uppercase tracking-wider">
                    {key.replace(/_/g, ' ')}
                  </h4>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => updateFindingStatus(key, 'verified')}
                      className={`p-1 rounded transition-colors ${findingStatus === 'verified' ? 'bg-emerald-500/20 text-emerald-400' : 'text-dark-500 hover:text-emerald-400'}`}
                      title="Verify"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => updateFindingStatus(key, 'rejected')}
                      className={`p-1 rounded transition-colors ${findingStatus === 'rejected' ? 'bg-red-500/20 text-red-400' : 'text-dark-500 hover:text-red-400'}`}
                      title="Reject"
                    >
                      <XCircle className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div className="text-xs text-dark-300 max-h-40 overflow-y-auto">
                  {typeof value === 'string' ? (
                    <p>{value}</p>
                  ) : Array.isArray(value) ? (
                    <ul className="space-y-1">
                      {(value as unknown[]).slice(0, 8).map((item, i) => (
                        <li key={i} className="text-dark-300">
                          {typeof item === 'object' && item !== null
                            ? Object.entries(item as Record<string, unknown>).map(([k, v]) => `${k}: ${v}`).join(' | ')
                            : String(item)}
                        </li>
                      ))}
                      {(value as unknown[]).length > 8 && <li className="text-dark-500">+{(value as unknown[]).length - 8} more</li>}
                    </ul>
                  ) : typeof value === 'object' && value !== null ? (
                    <div className="space-y-1">
                      {Object.entries(value as Record<string, unknown>).map(([k, v]) => (
                        <p key={k}><span className="text-dark-400">{k}:</span> {String(v)}</p>
                      ))}
                    </div>
                  ) : (
                    <p>{String(value)}</p>
                  )}
                </div>
                {findingStatus !== 'unverified' && (
                  <span className={`inline-block mt-2 px-2 py-0.5 rounded text-[10px] font-medium border ${statusColors[findingStatus]}`}>
                    {findingStatus}
                  </span>
                )}
              </motion.div>
            )
          })}
        </div>

        {/* Recommended Actions */}
        {findings.recommended_actions && Array.isArray(findings.recommended_actions) && (
          <div className="bg-dark-800/60 border border-blue-500/20 rounded-xl p-4">
            <h4 className="text-xs font-semibold text-blue-300 mb-2">Recommended Actions</h4>
            <ul className="space-y-1">
              {(findings.recommended_actions as string[]).map((action, i) => (
                <li key={i} className="text-xs text-dark-300 flex items-start gap-2">
                  <span className="text-blue-400 mt-0.5">-</span> {action}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Officer Notes */}
        <div className="bg-dark-800/60 border border-dark-700/50 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <MessageSquare className="w-4 h-4 text-purple-400" />
            <h4 className="text-xs font-semibold text-purple-300">Officer Notes</h4>
          </div>
          <textarea
            value={officerNotes}
            onChange={(e) => setOfficerNotes(e.target.value)}
            placeholder="Add your observations, cross-references, or follow-up notes..."
            className="w-full bg-dark-900/50 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white placeholder-dark-500 focus:border-purple-500 focus:outline-none resize-none h-20"
          />
          <div className="flex items-center justify-between mt-2">
            <div className="flex gap-2">
              <button
                onClick={() => setOverallStatus('verified')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1 transition-colors ${
                  currentInvestigation.overall_status === 'verified'
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-dark-700 text-dark-300 hover:text-emerald-400'
                }`}
              >
                <CheckCircle2 className="w-3 h-3" /> Verify All
              </button>
              <button
                onClick={() => setOverallStatus('rejected')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1 transition-colors ${
                  currentInvestigation.overall_status === 'rejected'
                    ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                    : 'bg-dark-700 text-dark-300 hover:text-red-400'
                }`}
              >
                <XCircle className="w-3 h-3" /> Reject All
              </button>
            </div>
            <button
              onClick={saveNotes}
              disabled={savingNotes}
              className="px-4 py-1.5 bg-purple-600 hover:bg-purple-500 text-white text-xs rounded-lg font-medium disabled:opacity-50"
            >
              {savingNotes ? 'Saving...' : 'Save Notes'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  const currentType = IDENTIFIER_TYPES.find(t => t.key === selectedType)!

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-600 to-blue-800 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Globe className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">OSINT Investigation Hub</h1>
          <p className="text-dark-400 text-sm">AI-powered open source intelligence gathering</p>
        </div>
      </div>

      {/* Type Pills */}
      <div className="flex flex-wrap gap-2">
        {IDENTIFIER_TYPES.map((type) => {
          const Icon = type.icon
          return (
            <button
              key={type.key}
              onClick={() => { setSelectedType(type.key); setCurrentInvestigation(null) }}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                selectedType === type.key
                  ? 'bg-cyan-600/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-500/10'
                  : 'bg-dark-800/80 text-dark-400 border border-dark-700/50 hover:text-white hover:border-dark-600'
              }`}
            >
              <Icon className="w-4 h-4" />
              {type.label}
            </button>
          )
        })}
      </div>

      {/* Search Input */}
      <form onSubmit={handleSearch} className="flex items-center gap-3">
        <div className="flex-1 flex items-center gap-3 bg-dark-800/80 border border-dark-700/50 rounded-xl px-4 py-3">
          <Search className="w-5 h-5 text-dark-400" />
          <input
            type="text"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder={currentType.placeholder}
            className="flex-1 bg-transparent text-white placeholder-dark-500 outline-none text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={searching || !searchValue.trim()}
          className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium rounded-xl flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          {searching ? 'Analyzing...' : 'Investigate'}
        </button>
      </form>

      {/* Loading State */}
      {searching && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center py-12"
        >
          <Loader2 className="w-10 h-10 text-cyan-400 animate-spin mb-4" />
          <p className="text-dark-300 text-sm">AI is analyzing open sources...</p>
          <p className="text-dark-500 text-xs mt-1">This may take 5-15 seconds</p>
        </motion.div>
      )}

      {/* Results */}
      {currentInvestigation && !searching && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-semibold text-white">Investigation Results</h2>
              <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${statusColors[currentInvestigation.overall_status]}`}>
                {currentInvestigation.overall_status}
              </span>
            </div>
            {currentInvestigation.ai_generation_time_ms && (
              <span className="text-xs text-dark-500 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {currentInvestigation.ai_generation_time_ms}ms | {currentInvestigation.ai_model_used}
              </span>
            )}
          </div>
          {renderFindings()}
        </motion.div>
      )}

      {/* History Table */}
      {history.length > 0 && (
        <div className="mt-8">
          <h3 className="text-sm font-semibold text-dark-300 mb-3 flex items-center gap-2">
            <Clock className="w-4 h-4" /> Recent Investigations
          </h3>
          <div className="rounded-xl bg-dark-900/80 border border-dark-700/50 overflow-hidden">
            <table className="w-full">
              <thead className="bg-dark-900/50">
                <tr>
                  <th className="text-left text-dark-400 text-xs font-medium px-4 py-2.5">Type</th>
                  <th className="text-left text-dark-400 text-xs font-medium px-4 py-2.5">Identifier</th>
                  <th className="text-left text-dark-400 text-xs font-medium px-4 py-2.5">Status</th>
                  <th className="text-left text-dark-400 text-xs font-medium px-4 py-2.5">Linked</th>
                  <th className="text-left text-dark-400 text-xs font-medium px-4 py-2.5">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-800/50">
                {history.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => loadInvestigation(item.id)}
                    className="hover:bg-dark-800/50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-2.5 text-xs text-cyan-400 font-medium uppercase">{item.identifier_type.replace('_', ' ')}</td>
                    <td className="px-4 py-2.5 text-sm text-white font-mono">{item.identifier_value}</td>
                    <td className="px-4 py-2.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${statusColors[item.overall_status]}`}>
                        {item.overall_status}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      {item.linked_criminal_id ? (
                        <Link2 className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <span className="text-dark-600">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-xs text-dark-400">
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
