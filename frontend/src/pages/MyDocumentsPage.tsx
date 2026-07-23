import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  FileText, Download, Search, Filter, Eye, Printer, Calendar, FolderOpen, Hash,
} from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../api/client'

interface MyDocument {
  id: number
  case_id: number
  case_public_id: string
  fir_number: string
  doc_type: string
  output_format: string
  file_path: string
  file_hash: string | null
  generated_by: number
  generated_at: string | null
}

const DOC_TYPE_LABELS: Record<string, string> = {
  fir: 'FIR',
  chargesheet: 'Chargesheet',
  seizure_memo: 'Seizure Memo',
  medical_letter: 'Medical Letter',
  court_letter: 'Court Letter',
  arrest_memo: 'Arrest Memo',
  case_diary: 'Case Diary',
  witness_statement: 'Witness Statement',
  search_memo: 'Search Memo',
  notice: 'Notice',
}

const DOC_TYPE_COLORS: Record<string, string> = {
  fir: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  chargesheet: 'bg-green-500/10 text-green-400 border-green-500/30',
  seizure_memo: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  medical_letter: 'bg-red-500/10 text-red-400 border-red-500/30',
  court_letter: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
  arrest_memo: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
  case_diary: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
  witness_statement: 'bg-pink-500/10 text-pink-400 border-pink-500/30',
  search_memo: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
  notice: 'bg-dark-500/10 text-dark-300 border-dark-500/30',
}

export default function MyDocumentsPage() {
  const [documents, setDocuments] = useState<MyDocument[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')

  useEffect(() => {
    loadDocuments()
  }, [typeFilter])

  const loadDocuments = async () => {
    setLoading(true)
    try {
      const params: Record<string, string> = { limit: '100' }
      if (typeFilter) params.doc_type = typeFilter
      const res = await api.get('/api/documents/mine', { params })
      setDocuments(res.data.documents)
      setTotal(res.data.total)
    } catch {
      toast.error('Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async (docId: number) => {
    try {
      const res = await api.get(`/api/documents/download/${docId}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      const contentDisposition = res.headers['content-disposition']
      const filename = contentDisposition
        ? contentDisposition.split('filename=')[1]?.replace(/"/g, '')
        : `document_${docId}.docx`
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      toast.error('Download failed')
    }
  }

  const filteredDocs = documents.filter(d => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      d.fir_number.toLowerCase().includes(q) ||
      (DOC_TYPE_LABELS[d.doc_type] || d.doc_type).toLowerCase().includes(q)
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
            <div className="w-10 h-10 bg-cyan-600/20 rounded-xl flex items-center justify-center">
              <FileText className="w-5 h-5 text-cyan-400" />
            </div>
            My Documents
          </h1>
          <p className="text-dark-400 text-sm mt-1">{total} documents across your cases</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
          <input
            type="text"
            placeholder="Search by FIR number or type..."
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
            {Object.entries(DOC_TYPE_LABELS).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Document List */}
      {filteredDocs.length === 0 ? (
        <div className="card text-center py-12">
          <FileText className="w-12 h-12 text-dark-600 mx-auto mb-3" />
          <p className="text-dark-400">No documents found</p>
          <p className="text-dark-500 text-sm mt-1">Generate documents from your case pages</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredDocs.map((doc, i) => (
            <motion.div
              key={doc.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              className="card flex items-center justify-between gap-4 hover:border-dark-600 transition-all"
            >
              <div className="flex items-center gap-4 min-w-0 flex-1">
                <div className="w-10 h-10 bg-dark-800 rounded-lg flex items-center justify-center flex-shrink-0">
                  <FileText className="w-5 h-5 text-cyan-400" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${DOC_TYPE_COLORS[doc.doc_type] || 'bg-dark-700 text-dark-300'}`}>
                      {DOC_TYPE_LABELS[doc.doc_type] || doc.doc_type}
                    </span>
                    <span className="text-dark-500 text-xs uppercase">{doc.output_format}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1 text-sm">
                    <Link to={`/cases/${doc.case_public_id}`} className="text-primary-400 hover:text-primary-300 flex items-center gap-1">
                      <FolderOpen className="w-3 h-3" />
                      {doc.fir_number}
                    </Link>
                    {doc.generated_at && (
                      <span className="text-dark-500 flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {new Date(doc.generated_at).toLocaleDateString()}
                      </span>
                    )}
                    {doc.file_hash && (
                      <span className="text-dark-500 flex items-center gap-1 font-mono text-xs">
                        <Hash className="w-3 h-3 text-green-500" />
                        {doc.file_hash.slice(0, 16)}...
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-1 flex-shrink-0">
                <Link
                  to={`/cases/${doc.case_public_id}`}
                  className="p-2 text-dark-400 hover:text-white hover:bg-dark-700 rounded-lg transition-colors"
                  title="View Case"
                >
                  <Eye className="w-4 h-4" />
                </Link>
                <button
                  onClick={() => handleDownload(doc.id)}
                  className="p-2 text-dark-400 hover:text-cyan-400 hover:bg-cyan-500/10 rounded-lg transition-colors"
                  title="Download"
                >
                  <Download className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDownload(doc.id)}
                  className="p-2 text-dark-400 hover:text-green-400 hover:bg-green-500/10 rounded-lg transition-colors"
                  title="Print"
                >
                  <Printer className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
