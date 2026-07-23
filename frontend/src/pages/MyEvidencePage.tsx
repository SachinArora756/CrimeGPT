import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  HardDrive, Search, Filter, Eye, Calendar, FolderOpen,
  Image, Video, FileText, Mic, Fingerprint, Database, Hash,
} from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../api/client'

interface MyEvidence {
  id: number
  case_id: number
  case_public_id: string
  fir_number: string
  file_path: string
  original_filename: string
  file_type: string
  file_size: number
  file_hash: string | null
  description: string | null
  tags: string[] | null
  uploaded_by: number
  created_at: string | null
}

const FILE_TYPE_ICONS: Record<string, typeof Image> = {
  image: Image,
  video: Video,
  document: FileText,
  audio: Mic,
  forensic: Fingerprint,
  other: Database,
}

const FILE_TYPE_COLORS: Record<string, string> = {
  image: 'bg-green-500/10 text-green-400 border-green-500/30',
  video: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
  document: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  audio: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  forensic: 'bg-red-500/10 text-red-400 border-red-500/30',
  other: 'bg-dark-500/10 text-dark-300 border-dark-500/30',
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function MyEvidencePage() {
  const [evidence, setEvidence] = useState<MyEvidence[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')

  useEffect(() => {
    loadEvidence()
  }, [typeFilter])

  const loadEvidence = async () => {
    setLoading(true)
    try {
      const params: Record<string, string> = { limit: '100' }
      if (typeFilter) params.file_type = typeFilter
      const res = await api.get('/api/evidence/mine', { params })
      setEvidence(res.data.evidence)
      setTotal(res.data.total)
    } catch {
      toast.error('Failed to load evidence')
    } finally {
      setLoading(false)
    }
  }

  const filteredEvidence = evidence.filter(ev => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      ev.original_filename.toLowerCase().includes(q) ||
      ev.fir_number.toLowerCase().includes(q) ||
      (ev.description || '').toLowerCase().includes(q) ||
      (ev.tags || []).some(t => t.toLowerCase().includes(q))
    )
  })

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-10 w-48 skeleton" />
        {[1, 2, 3, 4, 5].map(i => <div key={i} className="card animate-pulse h-16 bg-dark-800/50" />)}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-600/20 rounded-xl flex items-center justify-center">
              <HardDrive className="w-5 h-5 text-purple-400" />
            </div>
            My Evidence
          </h1>
          <p className="text-dark-400 text-sm mt-1">{total} evidence items across your cases</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
          <input
            type="text"
            placeholder="Search by filename, case, or tags..."
            className="input pl-10"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
          <select
            className="input pl-10 pr-8 appearance-none min-w-[160px]"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="">All Types</option>
            <option value="image">Images</option>
            <option value="video">Videos</option>
            <option value="audio">Audio</option>
            <option value="document">Documents</option>
            <option value="forensic">Forensic</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>

      {/* Evidence List */}
      {filteredEvidence.length === 0 ? (
        <div className="card text-center py-12">
          <HardDrive className="w-12 h-12 text-dark-600 mx-auto mb-3" />
          <p className="text-dark-400">No evidence found</p>
          <p className="text-dark-500 text-sm mt-1">Upload evidence from your case pages</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredEvidence.map((ev, i) => {
            const Icon = FILE_TYPE_ICONS[ev.file_type] || HardDrive
            const colorClass = FILE_TYPE_COLORS[ev.file_type] || FILE_TYPE_COLORS.other
            return (
              <motion.div
                key={ev.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }}
                className="card flex items-center justify-between gap-4 hover:border-dark-600 transition-all"
              >
                <div className="flex items-center gap-4 min-w-0 flex-1">
                  <div className="w-10 h-10 bg-dark-800 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Icon className="w-5 h-5 text-purple-400" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-white text-sm font-medium truncate">{ev.original_filename}</p>
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${colorClass}`}>
                        {ev.file_type}
                      </span>
                      <span className="text-dark-500 text-xs">{formatFileSize(ev.file_size)}</span>
                      <Link to={`/cases/${ev.case_public_id}`} className="text-primary-400 hover:text-primary-300 text-xs flex items-center gap-1">
                        <FolderOpen className="w-3 h-3" />
                        {ev.fir_number}
                      </Link>
                      {ev.created_at && (
                        <span className="text-dark-500 text-xs flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {new Date(ev.created_at).toLocaleDateString()}
                        </span>
                      )}
                      {ev.file_hash && (
                        <span className="text-dark-500 text-xs flex items-center gap-1 font-mono">
                          <Hash className="w-3 h-3 text-green-500" />
                          {ev.file_hash.slice(0, 16)}...
                        </span>
                      )}
                    </div>
                    {ev.tags && ev.tags.length > 0 && (
                      <div className="flex gap-1 mt-1 flex-wrap">
                        {ev.tags.slice(0, 5).map(tag => (
                          <span key={tag} className="px-1.5 py-0.5 bg-dark-700 rounded text-[10px] text-dark-300">{tag}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-1 flex-shrink-0">
                  <Link
                    to={`/evidence/${ev.case_public_id}`}
                    className="p-2 text-dark-400 hover:text-white hover:bg-dark-700 rounded-lg transition-colors"
                    title="View in Case"
                  >
                    <Eye className="w-4 h-4" />
                  </Link>
                </div>
              </motion.div>
            )
          })}
        </div>
      )}
    </div>
  )
}
