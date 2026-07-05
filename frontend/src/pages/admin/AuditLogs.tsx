import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileText, RefreshCw, Filter, ChevronDown, ChevronUp,
  User, Globe, Monitor, Clock, Shield, Eye, Edit2, Trash2, Plus, Lock,
} from 'lucide-react'
import api from '../../api/client'

interface AuditEntry {
  id: number
  user_id: number | null
  username?: string
  full_name?: string
  action: string
  resource_type: string
  resource_id: string | null
  details: Record<string, unknown> | null
  ip_address: string | null
  user_agent: string | null
  timestamp: string | null
}

const ACTION_ICONS: Record<string, typeof Eye> = {
  create: Plus,
  update: Edit2,
  delete: Trash2,
  view: Eye,
  login: Lock,
  logout: Lock,
}

const ACTION_COLORS: Record<string, string> = {
  create: 'bg-green-500/10 text-green-400 border-green-500/20',
  update: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  delete: 'bg-red-500/10 text-red-400 border-red-500/20',
  view: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  login: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  logout: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
}

function parseBrowser(ua: string | null): { browser: string; os: string } {
  if (!ua) return { browser: 'Unknown', os: 'Unknown' }
  let browser = 'Unknown'
  let os = 'Unknown'
  if (ua.includes('Chrome')) browser = 'Chrome'
  else if (ua.includes('Firefox')) browser = 'Firefox'
  else if (ua.includes('Safari')) browser = 'Safari'
  else if (ua.includes('Edge')) browser = 'Edge'
  if (ua.includes('Windows')) os = 'Windows'
  else if (ua.includes('Mac')) os = 'macOS'
  else if (ua.includes('Linux')) os = 'Linux'
  else if (ua.includes('Android')) os = 'Android'
  else if (ua.includes('iPhone') || ua.includes('iPad')) os = 'iOS'
  return { browser, os }
}

export default function AuditLogs() {
  const [logs, setLogs] = useState<AuditEntry[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [filterAction, setFilterAction] = useState('')
  const [filterResource, setFilterResource] = useState('')

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const params: Record<string, string | number> = { page, per_page: 30 }
      if (filterAction) params.action = filterAction
      if (filterResource) params.resource_type = filterResource
      const res = await api.get('/api/admin/audit-logs', { params })
      setLogs(res.data.logs)
      setTotal(res.data.total)
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchLogs() }, [page, filterAction, filterResource])

  const totalPages = Math.ceil(total / 30)

  const getActionColor = (action: string) => {
    const key = Object.keys(ACTION_COLORS).find(k => action.toLowerCase().includes(k))
    return key ? ACTION_COLORS[key] : 'bg-dark-700/50 text-dark-300 border-dark-600'
  }

  const getActionIcon = (action: string) => {
    const key = Object.keys(ACTION_ICONS).find(k => action.toLowerCase().includes(k))
    return key ? ACTION_ICONS[key] : Shield
  }

  const sanitizeDetail = (val: unknown): string => {
    if (typeof val === 'string') {
      if (/^\/(data|uploads|tmp|var|storage|mnt|app|home|root)\//.test(val)) {
        return `[secured]`
      }
      return val
    }
    if (typeof val === 'object' && val !== null) {
      const cleaned: Record<string, unknown> = {}
      for (const [k, v] of Object.entries(val as Record<string, unknown>)) {
        if (k === 'file_path' || k === 'image_path' || k === 'output_path') {
          cleaned[k] = '[secured]'
        } else {
          cleaned[k] = typeof v === 'string' && /^\/(data|uploads|tmp|var|storage|mnt|app)\//.test(v) ? '[secured]' : v
        }
      }
      return JSON.stringify(cleaned, null, 2)
    }
    return String(val)
  }

  const renderDetails = (details: Record<string, unknown> | null) => {
    if (!details || Object.keys(details).length === 0) return null
    return (
      <div className="mt-3 space-y-2">
        {Object.entries(details).map(([key, value]) => (
          <div key={key} className="flex items-start gap-2">
            <span className="text-dark-500 text-xs font-mono min-w-[100px]">{key}:</span>
            <span className="text-dark-300 text-xs font-mono break-all">
              {sanitizeDetail(value)}
            </span>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-600/20 rounded-xl flex items-center justify-center">
              <FileText className="w-5 h-5 text-purple-400" />
            </div>
            Audit Trail
          </h1>
          <p className="text-dark-400 text-sm mt-1">{total} total log entries</p>
        </div>
        <button onClick={fetchLogs} className="btn-secondary flex items-center gap-2">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-dark-400 text-sm">
          <Filter className="w-4 h-4" />
          <span>Filter:</span>
        </div>
        <select
          value={filterAction}
          onChange={(e) => { setFilterAction(e.target.value); setPage(1) }}
          className="bg-dark-800 border border-dark-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-primary-500/50"
        >
          <option value="">All Actions</option>
          <option value="create">Create</option>
          <option value="update">Update</option>
          <option value="delete">Delete</option>
          <option value="login">Login</option>
          <option value="view">View</option>
        </select>
        <select
          value={filterResource}
          onChange={(e) => { setFilterResource(e.target.value); setPage(1) }}
          className="bg-dark-800 border border-dark-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-primary-500/50"
        >
          <option value="">All Resources</option>
          <option value="case">Cases</option>
          <option value="evidence">Evidence</option>
          <option value="document">Documents</option>
          <option value="user">Users</option>
          <option value="auth">Authentication</option>
        </select>
      </div>

      {/* Log Entries */}
      <div className="space-y-2">
        {loading ? (
          <div className="space-y-2">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
              <div key={i} className="card animate-pulse h-16 bg-dark-800/50" />
            ))}
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-16 bg-dark-900/40 rounded-xl border border-dark-700/50">
            <FileText className="w-14 h-14 text-dark-600 mx-auto mb-3" />
            <p className="text-dark-400 text-lg">No audit logs found</p>
            <p className="text-dark-500 text-sm mt-1">Activity will appear here as users interact with the system</p>
          </div>
        ) : (
          logs.map((log) => {
            const ActionIcon = getActionIcon(log.action)
            const { browser, os } = parseBrowser(log.user_agent)
            const isExpanded = expandedId === log.id

            return (
              <motion.div
                key={log.id}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-dark-900/80 border border-dark-700/50 rounded-xl overflow-hidden hover:border-dark-600 transition-all"
              >
                <button
                  onClick={() => setExpandedId(isExpanded ? null : log.id)}
                  className="w-full flex items-center justify-between p-4 text-left"
                >
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <div className={`w-9 h-9 rounded-lg flex items-center justify-center border ${getActionColor(log.action)}`}>
                      <ActionIcon className="w-4 h-4" />
                    </div>

                    <div className="flex items-center gap-2 min-w-[140px]">
                      <User className="w-3.5 h-3.5 text-dark-500" />
                      <div>
                        <p className="text-white text-sm font-medium truncate">
                          {log.full_name || `User #${log.user_id}`}
                        </p>
                        {log.username && (
                          <p className="text-dark-500 text-[10px]">@{log.username}</p>
                        )}
                      </div>
                    </div>

                    <div className="flex-1 min-w-0">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase border ${getActionColor(log.action)}`}>
                        {log.action}
                      </span>
                      <span className="ml-2 text-dark-300 text-sm">
                        {log.resource_type}
                        {log.resource_id && <span className="text-dark-500"> #{log.resource_id}</span>}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 text-dark-400 text-xs min-w-[150px]">
                      <Clock className="w-3 h-3" />
                      {log.timestamp ? new Date(log.timestamp).toLocaleString() : '—'}
                    </div>

                    <div className="flex items-center gap-1.5 text-dark-500 text-xs min-w-[110px]">
                      <Globe className="w-3 h-3" />
                      {log.ip_address || '—'}
                    </div>
                  </div>

                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-dark-400 ml-2" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-dark-400 ml-2" />
                  )}
                </button>

                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="px-4 pb-4 border-t border-dark-800 pt-3">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                          <div className="bg-dark-800/50 rounded-lg p-3">
                            <p className="text-dark-500 mb-1 flex items-center gap-1">
                              <User className="w-3 h-3" /> User
                            </p>
                            <p className="text-white font-medium">{log.full_name || '—'}</p>
                            <p className="text-dark-400">ID: {log.user_id || '—'}</p>
                          </div>
                          <div className="bg-dark-800/50 rounded-lg p-3">
                            <p className="text-dark-500 mb-1 flex items-center gap-1">
                              <Globe className="w-3 h-3" /> IP Address
                            </p>
                            <p className="text-white font-medium font-mono">{log.ip_address || '—'}</p>
                          </div>
                          <div className="bg-dark-800/50 rounded-lg p-3">
                            <p className="text-dark-500 mb-1 flex items-center gap-1">
                              <Monitor className="w-3 h-3" /> Browser
                            </p>
                            <p className="text-white font-medium">{browser}</p>
                            <p className="text-dark-400">{os}</p>
                          </div>
                          <div className="bg-dark-800/50 rounded-lg p-3">
                            <p className="text-dark-500 mb-1 flex items-center gap-1">
                              <Clock className="w-3 h-3" /> Timestamp
                            </p>
                            <p className="text-white font-medium">
                              {log.timestamp ? new Date(log.timestamp).toLocaleString() : '—'}
                            </p>
                          </div>
                        </div>

                        {log.details && Object.keys(log.details).length > 0 && (
                          <div className="mt-3 bg-dark-800/30 rounded-lg p-3 border border-dark-700/50">
                            <p className="text-dark-500 text-[10px] uppercase tracking-wider mb-2 font-semibold">
                              Change Details
                            </p>
                            {renderDetails(log.details)}
                          </div>
                        )}

                        {log.user_agent && (
                          <div className="mt-2 text-[10px] text-dark-600 font-mono truncate">
                            {log.user_agent}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )
          })
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-dark-400 text-sm">
            Showing {(page - 1) * 30 + 1}–{Math.min(page * 30, total)} of {total}
          </p>
          <div className="flex gap-1">
            <button
              onClick={() => setPage(1)}
              disabled={page === 1}
              className="px-3 py-1.5 text-xs bg-dark-800 border border-dark-700 rounded-lg text-dark-300 hover:text-white disabled:opacity-40 transition-colors"
            >
              First
            </button>
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 text-xs bg-dark-800 border border-dark-700 rounded-lg text-dark-300 hover:text-white disabled:opacity-40 transition-colors"
            >
              Prev
            </button>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const start = Math.max(1, Math.min(page - 2, totalPages - 4))
              const p = start + i
              if (p > totalPages) return null
              return (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${
                    p === page
                      ? 'bg-primary-600/20 border-primary-500/30 text-primary-400'
                      : 'bg-dark-800 border-dark-700 text-dark-300 hover:text-white'
                  }`}
                >
                  {p}
                </button>
              )
            })}
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1.5 text-xs bg-dark-800 border border-dark-700 rounded-lg text-dark-300 hover:text-white disabled:opacity-40 transition-colors"
            >
              Next
            </button>
            <button
              onClick={() => setPage(totalPages)}
              disabled={page >= totalPages}
              className="px-3 py-1.5 text-xs bg-dark-800 border border-dark-700 rounded-lg text-dark-300 hover:text-white disabled:opacity-40 transition-colors"
            >
              Last
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
