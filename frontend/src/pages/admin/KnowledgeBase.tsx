import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import {
  Database, RefreshCw, Upload, FileText, Search, Trash2, Plus, Eye,
  Loader2, CheckCircle, XCircle, Zap, FolderOpen, MessageSquare,
  Activity, Filter, ChevronDown, ChevronUp, X, AlertTriangle, BarChart3,
} from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../../api/client'

const CATEGORIES = [
  'BNS', 'BNSS', 'BSA', 'IPC', 'CrPC', 'Evidence Act',
  'Police SOPs', 'Investigation Manual', 'Court Judgements',
  'Cybercrime', 'Forensics', 'Traffic', 'Finance', 'Drugs',
  'Terrorism', 'Fraud', 'Internal Documents', 'Custom',
]

interface DocEntry {
  id: number
  filename: string
  original_filename: string
  file_hash: string
  chunk_count: number
  file_size: number
  collection_name: string
  category: string
  status: string
  uploaded_by: number | null
  version: number
  mime_type: string | null
  page_count: number | null
  embedding_model: string
  ingested_at: string | null
}

interface CollectionEntry {
  name: string
  vectors_count: number
  points_count?: number
  status: string
  config?: { size: number; distance: string }
}

interface ActivityEntry {
  id: number
  user_id: number | null
  username: string | null
  action: string
  document_name: string | null
  collection_name: string | null
  details: Record<string, unknown> | null
  created_at: string | null
}

interface Stats {
  total_documents: number
  total_chunks: number
  total_vectors: number
  collections_count: number
  embedding_model: string
  latest_upload: string | null
  failed_count: number
  avg_chunk_size: number
}

interface QueryResult {
  text: string
  score: number
  source_file?: string
  section_number?: string
  act?: string
  category?: string
}

type Tab = 'documents' | 'upload' | 'collections' | 'test' | 'activity'

export default function KnowledgeBase() {
  const [activeTab, setActiveTab] = useState<Tab>('documents')
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { fetchStats() }, [])

  const fetchStats = async () => {
    try {
      const res = await api.get('/api/knowledge-base/stats')
      setStats(res.data)
    } catch { /* silent */ }
    finally { setLoading(false) }
  }

  const tabs: { key: Tab; label: string; icon: typeof Database }[] = [
    { key: 'documents', label: 'Documents', icon: FileText },
    { key: 'upload', label: 'Upload', icon: Upload },
    { key: 'collections', label: 'Collections', icon: FolderOpen },
    { key: 'test', label: 'Test Query', icon: MessageSquare },
    { key: 'activity', label: 'Activity Log', icon: Activity },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-600/20 rounded-xl flex items-center justify-center">
              <Database className="w-5 h-5 text-purple-400" />
            </div>
            Knowledge Base Management
          </h1>
          <p className="text-dark-400 text-sm mt-1">Manage RAG documents, collections, and vector embeddings</p>
        </div>
        <button onClick={fetchStats} className="btn-secondary flex items-center gap-2 text-sm">
          <RefreshCw className="w-4 h-4" /> Refresh Stats
        </button>
      </div>

      {/* Stats Bar */}
      {loading && !stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
          {[1,2,3,4,5,6,7].map(i => <div key={i} className="h-20 bg-dark-800/50 rounded-xl animate-pulse" />)}
        </div>
      )}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
          <StatCard label="Documents" value={stats.total_documents} icon={FileText} color="blue" />
          <StatCard label="Chunks" value={stats.total_chunks.toLocaleString()} icon={BarChart3} color="purple" />
          <StatCard label="Vectors" value={stats.total_vectors.toLocaleString()} icon={Zap} color="cyan" />
          <StatCard label="Collections" value={stats.collections_count} icon={FolderOpen} color="green" />
          <StatCard label="Model" value="bge-small" icon={Database} color="orange" small />
          <StatCard label="Latest" value={stats.latest_upload ? new Date(stats.latest_upload).toLocaleDateString() : 'Never'} icon={CheckCircle} color="emerald" small />
          <StatCard label="Failed" value={stats.failed_count} icon={XCircle} color="red" />
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-dark-900/60 rounded-xl border border-dark-700/50">
        {tabs.map(tab => {
          const Icon = tab.icon
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.key
                  ? 'bg-primary-600/20 text-primary-400 border border-primary-500/30'
                  : 'text-dark-400 hover:text-white hover:bg-dark-800/50'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
        >
          {activeTab === 'documents' && <DocumentsTab onRefresh={fetchStats} />}
          {activeTab === 'upload' && <UploadTab onRefresh={fetchStats} />}
          {activeTab === 'collections' && <CollectionsTab onRefresh={fetchStats} />}
          {activeTab === 'test' && <TestQueryTab />}
          {activeTab === 'activity' && <ActivityLogTab />}
        </motion.div>
      </AnimatePresence>
    </div>
  )
}

const STAT_COLORS: Record<string, { bg: string; text: string }> = {
  blue: { bg: 'bg-blue-500/10', text: 'text-blue-400' },
  purple: { bg: 'bg-purple-500/10', text: 'text-purple-400' },
  cyan: { bg: 'bg-cyan-500/10', text: 'text-cyan-400' },
  green: { bg: 'bg-green-500/10', text: 'text-green-400' },
  orange: { bg: 'bg-orange-500/10', text: 'text-orange-400' },
  emerald: { bg: 'bg-emerald-500/10', text: 'text-emerald-400' },
  red: { bg: 'bg-red-500/10', text: 'text-red-400' },
}

function StatCard({ label, value, icon: Icon, color, small }: {
  label: string; value: string | number; icon: typeof Database; color: string; small?: boolean
}) {
  const colors = STAT_COLORS[color] || STAT_COLORS.blue
  return (
    <div className="bg-dark-900/80 border border-dark-700/50 rounded-xl p-3">
      <div className="flex items-center gap-2 mb-1">
        <div className={`w-6 h-6 rounded-md flex items-center justify-center ${colors.bg}`}>
          <Icon className={`w-3.5 h-3.5 ${colors.text}`} />
        </div>
        <span className="text-dark-500 text-[10px] uppercase tracking-wider">{label}</span>
      </div>
      <p className={`text-white font-bold ${small ? 'text-sm' : 'text-lg'} truncate`}>{value}</p>
    </div>
  )
}

// ─── Documents Tab ───────────────────────────────────────────────────────────

function DocumentsTab({ onRefresh }: { onRefresh: () => void }) {
  const [docs, setDocs] = useState<DocEntry[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [viewDoc, setViewDoc] = useState<DocEntry | null>(null)
  const [previewContent, setPreviewContent] = useState<string | null>(null)
  const [reingestId, setReingestId] = useState<number | null>(null)
  const [actionLoading, setActionLoading] = useState(false)

  const fetchDocs = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, string | number> = { page, per_page: 20 }
      if (search) params.search = search
      if (categoryFilter) params.category = categoryFilter
      const res = await api.get('/api/knowledge-base/documents', { params })
      setDocs(res.data.documents)
      setTotal(res.data.total)
    } catch { toast.error('Failed to load documents') }
    finally { setLoading(false) }
  }, [page, search, categoryFilter])

  useEffect(() => { fetchDocs() }, [fetchDocs])

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this document and all its vectors?')) return
    try {
      await api.delete(`/api/knowledge-base/documents/${id}`)
      toast.success('Document deleted')
      fetchDocs()
      onRefresh()
    } catch { toast.error('Delete failed') }
  }

  const handleBulkDelete = async () => {
    if (selected.size === 0) return
    if (!confirm(`Delete ${selected.size} documents and all their vectors?`)) return
    try {
      await api.post('/api/knowledge-base/documents/bulk-delete', Array.from(selected))
      toast.success(`Deleted ${selected.size} documents`)
      setSelected(new Set())
      fetchDocs()
      onRefresh()
    } catch { toast.error('Bulk delete failed') }
  }

  const handleReingest = async () => {
    if (!reingestId) return
    setActionLoading(true)
    try {
      const res = await api.post(`/api/knowledge-base/documents/${reingestId}/reingest`)
      toast.success(`Re-ingested: ${res.data.chunk_count} chunks`)
      setReingestId(null)
      fetchDocs()
      onRefresh()
    } catch { toast.error('Re-ingestion failed') }
    finally { setActionLoading(false) }
  }

  const handlePreview = async (doc: DocEntry) => {
    setViewDoc(doc)
    try {
      const res = await api.get(`/api/knowledge-base/documents/${doc.id}/preview`)
      if (res.data.type === 'text') {
        setPreviewContent(res.data.content)
      } else {
        setPreviewContent(null)
      }
    } catch { setPreviewContent('Unable to load preview') }
  }

  const toggleSelect = (id: number) => {
    const next = new Set(selected)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setSelected(next)
  }

  const totalPages = Math.ceil(total / 20)

  return (
    <div className="space-y-4">
      {/* Search & Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            placeholder="Search documents..."
            className="w-full pl-10 pr-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-sm text-white placeholder:text-dark-500 focus:outline-none focus:border-primary-500/50"
          />
        </div>
        <select
          value={categoryFilter}
          onChange={(e) => { setCategoryFilter(e.target.value); setPage(1) }}
          className="bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500/50"
        >
          <option value="">All Categories</option>
          {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        {selected.size > 0 && (
          <button onClick={handleBulkDelete} className="flex items-center gap-2 px-3 py-2 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm hover:bg-red-500/20 transition-colors">
            <Trash2 className="w-4 h-4" /> Delete {selected.size}
          </button>
        )}
      </div>

      {/* Table */}
      {loading ? (
        <div className="space-y-2">{[1,2,3,4,5].map(i => <div key={i} className="card animate-pulse h-14 bg-dark-800/50" />)}</div>
      ) : docs.length === 0 ? (
        <div className="text-center py-16 bg-dark-900/40 rounded-xl border border-dark-700/50">
          <FileText className="w-14 h-14 text-dark-600 mx-auto mb-3" />
          <p className="text-dark-400 text-lg">No documents found</p>
          <p className="text-dark-500 text-sm mt-1">Upload documents in the Upload tab to get started</p>
        </div>
      ) : (
        <div className="bg-dark-900/60 border border-dark-700/50 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-700/50">
                <th className="w-10 px-3 py-3"><input type="checkbox" className="rounded" onChange={(e) => {
                  if (e.target.checked) setSelected(new Set(docs.map(d => d.id)))
                  else setSelected(new Set())
                }} checked={selected.size === docs.length && docs.length > 0} /></th>
                <th className="text-left text-dark-400 text-xs font-medium px-3 py-3">Document</th>
                <th className="text-left text-dark-400 text-xs font-medium px-3 py-3">Category</th>
                <th className="text-left text-dark-400 text-xs font-medium px-3 py-3">Chunks</th>
                <th className="text-left text-dark-400 text-xs font-medium px-3 py-3">Size</th>
                <th className="text-left text-dark-400 text-xs font-medium px-3 py-3">Status</th>
                <th className="text-left text-dark-400 text-xs font-medium px-3 py-3">Ingested</th>
                <th className="text-left text-dark-400 text-xs font-medium px-3 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-800/50">
              {docs.map(doc => (
                <tr key={doc.id} className="hover:bg-dark-800/30 transition-colors">
                  <td className="px-3 py-2.5">
                    <input type="checkbox" className="rounded" checked={selected.has(doc.id)} onChange={() => toggleSelect(doc.id)} />
                  </td>
                  <td className="px-3 py-2.5">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-dark-500 flex-shrink-0" />
                      <span className="text-white text-sm truncate max-w-[200px]">{doc.original_filename || doc.filename}</span>
                      {doc.version > 1 && <span className="text-[10px] px-1.5 py-0.5 bg-blue-500/10 text-blue-400 rounded">v{doc.version}</span>}
                    </div>
                  </td>
                  <td className="px-3 py-2.5">
                    <span className="text-xs px-2 py-0.5 bg-purple-500/10 text-purple-400 rounded-md">{doc.category}</span>
                  </td>
                  <td className="px-3 py-2.5 text-dark-300 text-sm">{doc.chunk_count}</td>
                  <td className="px-3 py-2.5 text-dark-300 text-sm">{(doc.file_size / 1024).toFixed(1)} KB</td>
                  <td className="px-3 py-2.5">
                    <span className={`text-[10px] px-2 py-0.5 rounded-md font-medium ${
                      doc.status === 'active' ? 'bg-green-500/10 text-green-400' :
                      doc.status === 'failed' ? 'bg-red-500/10 text-red-400' :
                      'bg-dark-700 text-dark-400'
                    }`}>{doc.status}</span>
                  </td>
                  <td className="px-3 py-2.5 text-dark-400 text-xs">{doc.ingested_at ? new Date(doc.ingested_at).toLocaleDateString() : '—'}</td>
                  <td className="px-3 py-2.5">
                    <div className="flex items-center gap-1">
                      <button onClick={() => handlePreview(doc)} className="p-1.5 text-dark-400 hover:text-cyan-400 hover:bg-cyan-500/10 rounded-lg transition-colors" title="Preview">
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={() => setReingestId(doc.id)} className="p-1.5 text-dark-400 hover:text-yellow-400 hover:bg-yellow-500/10 rounded-lg transition-colors" title="Re-ingest">
                        <RefreshCw className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={() => handleDelete(doc.id)} className="p-1.5 text-dark-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors" title="Delete">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-dark-400 text-sm">Showing {(page-1)*20+1}–{Math.min(page*20, total)} of {total}</p>
          <div className="flex gap-1">
            <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1} className="px-3 py-1.5 text-xs bg-dark-800 border border-dark-700 rounded-lg text-dark-300 hover:text-white disabled:opacity-40">Prev</button>
            <button onClick={() => setPage(p => Math.min(totalPages, p+1))} disabled={page >= totalPages} className="px-3 py-1.5 text-xs bg-dark-800 border border-dark-700 rounded-lg text-dark-300 hover:text-white disabled:opacity-40">Next</button>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      <AnimatePresence>
        {viewDoc && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50" onClick={() => { setViewDoc(null); setPreviewContent(null) }}>
            <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} exit={{ scale: 0.95 }} className="bg-dark-900 border border-dark-700 rounded-2xl max-w-3xl w-full max-h-[85vh] overflow-hidden" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between p-4 border-b border-dark-700">
                <div>
                  <h3 className="text-white font-semibold">{viewDoc.original_filename || viewDoc.filename}</h3>
                  <p className="text-dark-400 text-xs mt-0.5">{viewDoc.category} &bull; {viewDoc.chunk_count} chunks &bull; {(viewDoc.file_size/1024).toFixed(1)} KB</p>
                </div>
                <button onClick={() => { setViewDoc(null); setPreviewContent(null) }} className="p-2 text-dark-400 hover:text-white rounded-lg hover:bg-dark-800"><X className="w-5 h-5" /></button>
              </div>
              <div className="p-4 overflow-y-auto max-h-[65vh]">
                {previewContent ? (
                  <pre className="text-dark-300 text-xs font-mono whitespace-pre-wrap bg-dark-800/50 p-4 rounded-xl border border-dark-700/50">{previewContent}</pre>
                ) : (
                  <div className="text-center py-10">
                    <FileText className="w-10 h-10 text-dark-600 mx-auto mb-2" />
                    <p className="text-dark-400">Preview not available for this file type</p>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Re-ingest Confirmation Modal */}
      <AnimatePresence>
        {reingestId && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50" onClick={() => setReingestId(null)}>
            <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} exit={{ scale: 0.95 }} className="bg-dark-900 border border-dark-700 rounded-2xl max-w-md w-full p-6" onClick={e => e.stopPropagation()}>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-yellow-500/10 rounded-xl flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-yellow-400" />
                </div>
                <div>
                  <h3 className="text-white font-semibold">Re-ingest Document</h3>
                  <p className="text-dark-400 text-xs">This will delete existing vectors and re-process the file</p>
                </div>
              </div>
              <p className="text-dark-300 text-sm mb-4">The document will be re-extracted, re-chunked, and re-embedded. Existing vectors will be replaced.</p>
              <div className="flex gap-2 justify-end">
                <button onClick={() => setReingestId(null)} className="btn-secondary text-sm">Cancel</button>
                <button onClick={handleReingest} disabled={actionLoading} className="btn-primary text-sm flex items-center gap-2">
                  {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                  Re-ingest
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ─── Upload Tab ──────────────────────────────────────────────────────────────

function UploadTab({ onRefresh }: { onRefresh: () => void }) {
  const [category, setCategory] = useState('')
  const [collection, setCollection] = useState('')
  const [collections, setCollections] = useState<CollectionEntry[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadResults, setUploadResults] = useState<Array<{ filename: string; status: string; message?: string; chunk_count?: number }>>([])

  useEffect(() => {
    api.get('/api/knowledge-base/collections').then(res => setCollections(res.data.collections)).catch(() => {})
  }, [])

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return
    setUploading(true)
    setUploadResults([])

    const formData = new FormData()
    acceptedFiles.forEach(file => formData.append('files', file))
    if (category) formData.append('category', category)
    if (collection) formData.append('collection', collection)

    try {
      const res = await api.post('/api/knowledge-base/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000,
      })
      setUploadResults(res.data.results)
      const successCount = res.data.results.filter((r: any) => r.status === 'success').length
      if (successCount > 0) toast.success(`${successCount} file(s) uploaded & ingested`)
      const dupeCount = res.data.results.filter((r: any) => r.status === 'duplicate').length
      if (dupeCount > 0) toast.error(`${dupeCount} file(s) rejected as duplicates`)
      onRefresh()
    } catch {
      toast.error('Upload failed')
    } finally {
      setUploading(false)
    }
  }, [category, collection, onRefresh])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'text/csv': ['.csv'],
      'text/html': ['.html'],
      'application/json': ['.json'],
      'application/xml': ['.xml'],
      'application/rtf': ['.rtf'],
    },
    disabled: uploading,
  })

  return (
    <div className="space-y-6">
      {/* Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-dark-400 text-xs font-medium uppercase tracking-wider mb-1.5 block">Category</label>
          <select value={category} onChange={e => setCategory(e.target.value)} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500/50">
            <option value="">Auto-detect</option>
            {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label className="text-dark-400 text-xs font-medium uppercase tracking-wider mb-1.5 block">Collection</label>
          <select value={collection} onChange={e => setCollection(e.target.value)} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500/50">
            <option value="">legal_provisions (default)</option>
            {collections.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
          </select>
        </div>
      </div>

      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`relative overflow-hidden rounded-2xl border-2 border-dashed cursor-pointer transition-all ${
          isDragActive ? 'border-primary-500 bg-primary-500/5 scale-[1.01]' :
          uploading ? 'border-dark-600 opacity-60 cursor-not-allowed' :
          'border-dark-600 hover:border-dark-500 hover:bg-dark-900/50'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center py-14">
          {uploading ? (
            <Loader2 className="w-14 h-14 text-primary-400 animate-spin" />
          ) : (
            <div className="w-16 h-16 bg-primary-500/10 rounded-2xl flex items-center justify-center mb-3">
              <Upload className="w-8 h-8 text-primary-400" />
            </div>
          )}
          <p className="text-white font-medium mt-2">
            {isDragActive ? 'Drop files here' : uploading ? 'Uploading & Ingesting...' : 'Drag & drop documents, or click to browse'}
          </p>
          <p className="text-dark-400 text-sm mt-1">PDF, DOCX, TXT, MD, CSV, HTML, JSON, XML, RTF</p>
          <div className="flex gap-2 mt-4 flex-wrap justify-center">
            {['PDF', 'DOCX', 'TXT', 'MD', 'CSV', 'HTML', 'JSON', 'XML', 'RTF'].map(ext => (
              <span key={ext} className="px-2 py-0.5 bg-dark-800 rounded text-[10px] text-dark-400 font-mono">{ext}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Upload Results */}
      {uploadResults.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-white font-medium text-sm">Upload Results</h3>
          {uploadResults.map((r, i) => (
            <div key={i} className={`flex items-center gap-3 p-3 rounded-xl border ${
              r.status === 'success' ? 'bg-green-500/5 border-green-500/20' :
              r.status === 'duplicate' ? 'bg-yellow-500/5 border-yellow-500/20' :
              'bg-red-500/5 border-red-500/20'
            }`}>
              {r.status === 'success' ? <CheckCircle className="w-4 h-4 text-green-400" /> :
               r.status === 'duplicate' ? <AlertTriangle className="w-4 h-4 text-yellow-400" /> :
               <XCircle className="w-4 h-4 text-red-400" />}
              <div className="flex-1 min-w-0">
                <p className="text-white text-sm truncate">{r.filename}</p>
                {r.message && <p className="text-dark-400 text-xs">{r.message}</p>}
              </div>
              {r.chunk_count !== undefined && (
                <span className="text-dark-400 text-xs">{r.chunk_count} chunks</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Collections Tab ─────────────────────────────────────────────────────────

function CollectionsTab({ onRefresh }: { onRefresh: () => void }) {
  const [collections, setCollections] = useState<CollectionEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDim, setNewDim] = useState(384)
  const [creating, setCreating] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const [confirmName, setConfirmName] = useState('')

  const fetchCollections = async () => {
    setLoading(true)
    try {
      const res = await api.get('/api/knowledge-base/collections')
      setCollections(res.data.collections)
    } catch { toast.error('Failed to load collections') }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchCollections() }, [])

  const handleCreate = async () => {
    if (!newName.trim()) return
    setCreating(true)
    try {
      const formData = new FormData()
      formData.append('name', newName.trim())
      formData.append('dimension', String(newDim))
      await api.post('/api/knowledge-base/collections', formData)
      toast.success(`Collection "${newName}" created`)
      setShowCreate(false)
      setNewName('')
      fetchCollections()
      onRefresh()
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to create collection')
    } finally { setCreating(false) }
  }

  const handleDelete = async () => {
    if (!deleteTarget || confirmName !== deleteTarget) return
    try {
      await api.delete(`/api/knowledge-base/collections/${deleteTarget}`, { params: { confirm_name: confirmName } })
      toast.success(`Collection "${deleteTarget}" deleted`)
      setDeleteTarget(null)
      setConfirmName('')
      fetchCollections()
      onRefresh()
    } catch { toast.error('Failed to delete collection') }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-white font-medium">Qdrant Collections</h3>
        <button onClick={() => setShowCreate(true)} className="btn-primary text-sm flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Collection
        </button>
      </div>

      {loading ? (
        <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="card animate-pulse h-16 bg-dark-800/50" />)}</div>
      ) : collections.length === 0 ? (
        <div className="text-center py-12 bg-dark-900/40 rounded-xl border border-dark-700/50">
          <FolderOpen className="w-12 h-12 text-dark-600 mx-auto mb-2" />
          <p className="text-dark-400">No collections found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {collections.map(col => (
            <div key={col.name} className="bg-dark-900/80 border border-dark-700/50 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-white font-medium text-sm">{col.name}</h4>
                <button onClick={() => setDeleteTarget(col.name)} className="p-1.5 text-dark-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <p className="text-dark-500 text-[10px] uppercase">Vectors</p>
                  <p className="text-white text-sm font-medium">{(col.vectors_count || 0).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-dark-500 text-[10px] uppercase">Dimension</p>
                  <p className="text-white text-sm font-medium">{col.config?.size || '—'}</p>
                </div>
                <div>
                  <p className="text-dark-500 text-[10px] uppercase">Distance</p>
                  <p className="text-white text-sm font-medium">{col.config?.distance || '—'}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <AnimatePresence>
        {showCreate && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50" onClick={() => setShowCreate(false)}>
            <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} exit={{ scale: 0.95 }} className="bg-dark-900 border border-dark-700 rounded-2xl max-w-md w-full p-6" onClick={e => e.stopPropagation()}>
              <h3 className="text-white font-semibold mb-4">Create New Collection</h3>
              <div className="space-y-3">
                <div>
                  <label className="text-dark-400 text-xs block mb-1">Collection Name</label>
                  <input value={newName} onChange={e => setNewName(e.target.value)} placeholder="e.g. custom_documents" className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500/50" />
                </div>
                <div>
                  <label className="text-dark-400 text-xs block mb-1">Vector Dimension</label>
                  <input type="number" value={newDim} onChange={e => setNewDim(parseInt(e.target.value) || 384)} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500/50" />
                </div>
              </div>
              <div className="flex gap-2 justify-end mt-4">
                <button onClick={() => setShowCreate(false)} className="btn-secondary text-sm">Cancel</button>
                <button onClick={handleCreate} disabled={creating || !newName.trim()} className="btn-primary text-sm flex items-center gap-2">
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />} Create
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {deleteTarget && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50" onClick={() => { setDeleteTarget(null); setConfirmName('') }}>
            <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} exit={{ scale: 0.95 }} className="bg-dark-900 border border-dark-700 rounded-2xl max-w-md w-full p-6" onClick={e => e.stopPropagation()}>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-red-500/10 rounded-xl flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                </div>
                <div>
                  <h3 className="text-white font-semibold">Delete Collection</h3>
                  <p className="text-dark-400 text-xs">This action cannot be undone</p>
                </div>
              </div>
              <p className="text-dark-300 text-sm mb-3">Type <span className="text-red-400 font-mono">{deleteTarget}</span> to confirm deletion of all vectors in this collection.</p>
              <input value={confirmName} onChange={e => setConfirmName(e.target.value)} placeholder="Type collection name..." className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500/50 mb-4" />
              <div className="flex gap-2 justify-end">
                <button onClick={() => { setDeleteTarget(null); setConfirmName('') }} className="btn-secondary text-sm">Cancel</button>
                <button onClick={handleDelete} disabled={confirmName !== deleteTarget} className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg font-medium disabled:opacity-40 hover:bg-red-700 transition-colors">Delete Collection</button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ─── Test Query Tab ──────────────────────────────────────────────────────────

function TestQueryTab() {
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(5)
  const [categoryFilter, setCategoryFilter] = useState('')
  const [results, setResults] = useState<QueryResult[]>([])
  const [searching, setSearching] = useState(false)
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null)

  const handleSearch = async () => {
    if (!query.trim()) return
    setSearching(true)
    setResults([])
    try {
      const formData = new FormData()
      formData.append('query', query)
      formData.append('top_k', String(topK))
      if (categoryFilter) formData.append('category_filter', categoryFilter)
      const res = await api.post('/api/knowledge-base/test-query', formData)
      setResults(res.data.results || [])
      if (res.data.results?.length === 0) toast('No results found', { icon: '🔍' })
    } catch { toast.error('Query failed') }
    finally { setSearching(false) }
  }

  return (
    <div className="space-y-4">
      <div className="bg-dark-900/80 border border-dark-700/50 rounded-xl p-4 space-y-4">
        <div>
          <label className="text-dark-400 text-xs font-medium uppercase tracking-wider block mb-1.5">Query</label>
          <textarea
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Enter a legal question to test RAG retrieval..."
            rows={3}
            className="w-full bg-dark-800 border border-dark-700 rounded-lg px-4 py-3 text-sm text-white placeholder:text-dark-500 focus:outline-none focus:border-primary-500/50 resize-none"
            onKeyDown={e => { if (e.key === 'Enter' && e.ctrlKey) handleSearch() }}
          />
        </div>
        <div className="flex items-end gap-4">
          <div className="flex-1">
            <label className="text-dark-400 text-xs block mb-1">Top K: {topK}</label>
            <input type="range" min={1} max={20} value={topK} onChange={e => setTopK(parseInt(e.target.value))} className="w-full accent-primary-500" />
          </div>
          <div className="flex-1">
            <label className="text-dark-400 text-xs block mb-1">Category Filter</label>
            <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)} className="w-full bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500/50">
              <option value="">All</option>
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <button onClick={handleSearch} disabled={searching || !query.trim()} className="btn-primary text-sm flex items-center gap-2 h-[38px]">
            {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Search
          </button>
        </div>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-white font-medium text-sm">Results ({results.length})</h3>
          {results.map((r, i) => (
            <div key={i} className="bg-dark-900/80 border border-dark-700/50 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] px-2 py-0.5 bg-cyan-500/10 text-cyan-400 rounded-md font-mono">
                    Score: {(r.score * 100).toFixed(1)}%
                  </span>
                  {r.source_file && <span className="text-dark-500 text-xs">{r.source_file}</span>}
                  {r.section_number && <span className="text-dark-500 text-xs">§{r.section_number}</span>}
                  {r.act && <span className="text-xs px-2 py-0.5 bg-purple-500/10 text-purple-400 rounded-md">{r.act}</span>}
                </div>
                <button onClick={() => setExpandedIdx(expandedIdx === i ? null : i)} className="p-1 text-dark-400 hover:text-white">
                  {expandedIdx === i ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>
              </div>
              {/* Score bar */}
              <div className="w-full h-1 bg-dark-800 rounded-full mb-2 overflow-hidden">
                <div className="h-full bg-gradient-to-r from-cyan-500 to-primary-500 rounded-full" style={{ width: `${r.score * 100}%` }} />
              </div>
              <p className="text-dark-300 text-xs leading-relaxed">
                {expandedIdx === i ? r.text : r.text.slice(0, 200) + (r.text.length > 200 ? '...' : '')}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Activity Log Tab ────────────────────────────────────────────────────────

function ActivityLogTab() {
  const [logs, setLogs] = useState<ActivityEntry[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [actionFilter, setActionFilter] = useState('')

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const params: Record<string, string | number> = { page, per_page: 20 }
      if (actionFilter) params.action = actionFilter
      const res = await api.get('/api/knowledge-base/activity-log', { params })
      setLogs(res.data.logs)
      setTotal(res.data.total)
    } catch { /* silent */ }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchLogs() }, [page, actionFilter])

  const actionColors: Record<string, string> = {
    upload: 'bg-green-500/10 text-green-400',
    delete: 'bg-red-500/10 text-red-400',
    bulk_delete: 'bg-red-500/10 text-red-400',
    reingest: 'bg-yellow-500/10 text-yellow-400',
    create_collection: 'bg-blue-500/10 text-blue-400',
    delete_collection: 'bg-red-500/10 text-red-400',
  }

  const totalPages = Math.ceil(total / 20)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Filter className="w-4 h-4 text-dark-500" />
        <select value={actionFilter} onChange={e => { setActionFilter(e.target.value); setPage(1) }} className="bg-dark-800 border border-dark-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-primary-500/50">
          <option value="">All Actions</option>
          <option value="upload">Upload</option>
          <option value="delete">Delete</option>
          <option value="bulk_delete">Bulk Delete</option>
          <option value="reingest">Re-ingest</option>
          <option value="create_collection">Create Collection</option>
          <option value="delete_collection">Delete Collection</option>
        </select>
      </div>

      {loading ? (
        <div className="space-y-2">{[1,2,3,4,5].map(i => <div key={i} className="card animate-pulse h-12 bg-dark-800/50" />)}</div>
      ) : logs.length === 0 ? (
        <div className="text-center py-12 bg-dark-900/40 rounded-xl border border-dark-700/50">
          <Activity className="w-12 h-12 text-dark-600 mx-auto mb-2" />
          <p className="text-dark-400">No activity logged yet</p>
        </div>
      ) : (
        <div className="space-y-2">
          {logs.map(log => (
            <div key={log.id} className="bg-dark-900/80 border border-dark-700/50 rounded-xl p-3 flex items-center gap-4">
              <div className="text-dark-500 text-xs min-w-[130px]">
                {log.created_at ? new Date(log.created_at).toLocaleString() : '—'}
              </div>
              <span className={`text-[10px] px-2 py-0.5 rounded-md font-semibold uppercase ${actionColors[log.action] || 'bg-dark-700 text-dark-300'}`}>
                {log.action}
              </span>
              <div className="flex-1 min-w-0">
                {log.document_name && <span className="text-white text-sm">{log.document_name}</span>}
                {log.collection_name && !log.document_name && <span className="text-white text-sm">{log.collection_name}</span>}
              </div>
              <span className="text-dark-500 text-xs">{log.username || `User #${log.user_id}`}</span>
            </div>
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-dark-400 text-sm">Showing {(page-1)*20+1}–{Math.min(page*20, total)} of {total}</p>
          <div className="flex gap-1">
            <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1} className="px-3 py-1.5 text-xs bg-dark-800 border border-dark-700 rounded-lg text-dark-300 hover:text-white disabled:opacity-40">Prev</button>
            <button onClick={() => setPage(p => Math.min(totalPages, p+1))} disabled={page >= totalPages} className="px-3 py-1.5 text-xs bg-dark-800 border border-dark-700 rounded-lg text-dark-300 hover:text-white disabled:opacity-40">Next</button>
          </div>
        </div>
      )}
    </div>
  )
}
