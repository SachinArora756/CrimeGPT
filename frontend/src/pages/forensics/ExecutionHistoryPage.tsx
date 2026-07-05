import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Clock, CheckCircle, XCircle, Loader2,
  ChevronLeft, ChevronRight, History, Filter,
  Search, ArrowUpDown
} from 'lucide-react'
import api from '../../api/client'

interface Execution {
  execution_id: string
  tool_key: string
  status: string
  input_filename: string | null
  confidence_score: number | null
  execution_time_ms: number | null
  created_at: string
  case_id: number | null
}

export default function ExecutionHistoryPage() {
  const navigate = useNavigate()
  const [executions, setExecutions] = useState<Execution[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [toolFilter, setToolFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const perPage = 20

  useEffect(() => {
    fetchExecutions()
  }, [page, toolFilter, statusFilter])

  const fetchExecutions = async () => {
    setLoading(true)
    try {
      const params: Record<string, string | number> = { page, per_page: perPage }
      if (toolFilter) params.tool_key = toolFilter
      if (statusFilter) params.status = statusFilter
      const response = await api.get('/api/forensic-toolkit/executions', { params })
      setExecutions(response.data.items)
      setTotal(response.data.total)
    } catch (error) {
      console.error('Failed to fetch executions:', error)
    } finally {
      setLoading(false)
    }
  }

  const totalPages = Math.ceil(total / perPage)

  const filteredExecutions = searchTerm
    ? executions.filter(e =>
        e.tool_key.includes(searchTerm.toLowerCase()) ||
        e.input_filename?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : executions

  const statusConfig: Record<string, { icon: typeof CheckCircle; color: string; bg: string; border: string }> = {
    completed: { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20' },
    failed: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' },
    running: { icon: Loader2, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' },
    pending: { icon: Clock, color: 'text-dark-400', bg: 'bg-dark-700', border: 'border-dark-600' },
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 blur-lg" />
            <div className="relative w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center shadow-xl shadow-blue-500/20">
              <History className="w-7 h-7 text-white" />
            </div>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Execution History</h1>
            <p className="text-dark-400 text-sm">{total} total forensic executions</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-green-500/10 border border-green-500/20">
            <CheckCircle className="w-3.5 h-3.5 text-green-400" />
            <span className="text-xs text-green-400 font-medium">
              {executions.filter(e => e.status === 'completed').length} completed
            </span>
          </div>
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-red-500/10 border border-red-500/20">
            <XCircle className="w-3.5 h-3.5 text-red-400" />
            <span className="text-xs text-red-400 font-medium">
              {executions.filter(e => e.status === 'failed').length} failed
            </span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search executions..."
            className="w-full bg-dark-800/80 border border-dark-700/50 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-dark-500 outline-none focus:border-primary-500/50 transition-all"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-dark-500" />
          <select
            value={toolFilter}
            onChange={(e) => { setToolFilter(e.target.value); setPage(1) }}
            className="bg-dark-800 border border-dark-700/50 rounded-xl px-3 py-2.5 text-xs text-white outline-none focus:border-primary-500/50 transition-all cursor-pointer"
          >
            <option value="">All Tools</option>
            <option value="image_ocr">Image OCR</option>
            <option value="image_object_detect">Object Detection</option>
            <option value="face_detect">Face Detection</option>
            <option value="face_recognize">Face Recognition</option>
            <option value="fingerprint_match">Fingerprint Match</option>
            <option value="digital_hash">Hash Generation</option>
            <option value="audio_transcribe">Audio Transcribe</option>
            <option value="document_pdf_parse">PDF Parse</option>
            <option value="license_plate_ocr">License Plate</option>
            <option value="vehicle_detect">Vehicle Detection</option>
            <option value="weapon_detect">Weapon Detection</option>
            <option value="crime_scene_analysis">Crime Scene</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
            className="bg-dark-800 border border-dark-700/50 rounded-xl px-3 py-2.5 text-xs text-white outline-none focus:border-primary-500/50 transition-all cursor-pointer"
          >
            <option value="">All Status</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="running">Running</option>
            <option value="pending">Pending</option>
          </select>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="h-14 rounded-xl bg-dark-800/50 animate-pulse" />
          ))}
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="rounded-2xl bg-dark-800/50 border border-dark-700/50 overflow-hidden shadow-xl"
        >
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-dark-700/50">
                  <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-5 py-3.5">Status</th>
                  <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-5 py-3.5">
                    <span className="flex items-center gap-1">Tool <ArrowUpDown className="w-3 h-3" /></span>
                  </th>
                  <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-5 py-3.5">Input File</th>
                  <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-5 py-3.5">Confidence</th>
                  <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-5 py-3.5">Duration</th>
                  <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-5 py-3.5">Case</th>
                  <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-5 py-3.5">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-700/30">
                {filteredExecutions.map((exec, i) => {
                  const st = statusConfig[exec.status] || statusConfig.pending
                  const StatusIcon = st.icon
                  return (
                    <motion.tr
                      key={exec.execution_id}
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.02 }}
                      onClick={() => navigate(`/forensics/execution/${exec.execution_id}`)}
                      className="hover:bg-dark-700/30 cursor-pointer transition-colors group"
                    >
                      <td className="px-5 py-3.5">
                        <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-lg ${st.bg} border ${st.border}`}>
                          <StatusIcon className={`w-3 h-3 ${st.color} ${exec.status === 'running' ? 'animate-spin' : ''}`} />
                          <span className={`text-[10px] font-medium ${st.color} capitalize`}>{exec.status}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="text-sm text-white font-medium capitalize group-hover:text-primary-300 transition-colors">
                          {exec.tool_key.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-xs text-dark-300 truncate max-w-[180px]">
                        {exec.input_filename || <span className="text-dark-600">—</span>}
                      </td>
                      <td className="px-5 py-3.5">
                        {exec.confidence_score != null ? (
                          <div className="flex items-center gap-2">
                            <div className="w-12 h-1.5 bg-dark-700 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${
                                  exec.confidence_score >= 0.8 ? 'bg-green-400' :
                                  exec.confidence_score >= 0.5 ? 'bg-amber-400' : 'bg-red-400'
                                }`}
                                style={{ width: `${exec.confidence_score * 100}%` }}
                              />
                            </div>
                            <span className={`text-xs font-medium ${
                              exec.confidence_score >= 0.8 ? 'text-green-400' :
                              exec.confidence_score >= 0.5 ? 'text-amber-400' : 'text-red-400'
                            }`}>
                              {Math.round(exec.confidence_score * 100)}%
                            </span>
                          </div>
                        ) : <span className="text-dark-600 text-xs">—</span>}
                      </td>
                      <td className="px-5 py-3.5 text-xs text-dark-400">
                        {exec.execution_time_ms ? (
                          <span className="font-mono">{(exec.execution_time_ms / 1000).toFixed(1)}s</span>
                        ) : <span className="text-dark-600">—</span>}
                      </td>
                      <td className="px-5 py-3.5 text-xs text-dark-400">
                        {exec.case_id ? (
                          <span className="px-2 py-0.5 rounded bg-primary-500/10 text-primary-400 border border-primary-500/20 text-[10px]">
                            #{exec.case_id}
                          </span>
                        ) : <span className="text-dark-600">—</span>}
                      </td>
                      <td className="px-5 py-3.5 text-xs text-dark-500">
                        {new Date(exec.created_at).toLocaleDateString()} {new Date(exec.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                    </motion.tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {filteredExecutions.length === 0 && (
            <div className="py-12 text-center">
              <History className="w-10 h-10 text-dark-600 mx-auto mb-3" />
              <p className="text-dark-400 text-sm">No executions found</p>
              <p className="text-dark-500 text-xs mt-1">Try adjusting your filters</p>
            </div>
          )}
        </motion.div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-dark-500">
            Showing <span className="text-dark-300 font-medium">{(page - 1) * perPage + 1}–{Math.min(page * perPage, total)}</span> of {total}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-2.5 rounded-xl bg-dark-800 border border-dark-700/50 hover:bg-dark-700 disabled:opacity-30 text-white transition-all"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const pageNum = page <= 3 ? i + 1 : page + i - 2
                if (pageNum < 1 || pageNum > totalPages) return null
                return (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    className={`w-8 h-8 rounded-lg text-xs font-medium transition-all ${
                      page === pageNum
                        ? 'bg-primary-500/10 text-primary-400 border border-primary-500/20'
                        : 'text-dark-400 hover:text-white hover:bg-dark-800'
                    }`}
                  >
                    {pageNum}
                  </button>
                )
              })}
            </div>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-2.5 rounded-xl bg-dark-800 border border-dark-700/50 hover:bg-dark-700 disabled:opacity-30 text-white transition-all"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
