import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FileText, Download, Plus, Loader2, Scale, Stamp, Clock } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../api/client'

interface DocumentItem {
  id: number
  case_id: number
  doc_type: string
  file_path: string
  generated_by: number
  generated_at: string
}

const DOC_TYPES = [
  { value: 'fir', label: 'First Information Report (FIR)', icon: '📋', description: 'Official police complaint document' },
  { value: 'chargesheet', label: 'Charge Sheet', icon: '⚖️', description: 'Court submission with evidence summary' },
  { value: 'seizure_memo', label: 'Seizure Memo', icon: '🔒', description: 'Record of seized property/evidence' },
  { value: 'medical_letter', label: 'Medical Examination Letter', icon: '🏥', description: 'Request for medical examination' },
  { value: 'court_letter', label: 'Court Submission Letter', icon: '🏛️', description: 'Official court correspondence' },
  { value: 'arrest_memo', label: 'Arrest Memo', icon: '🚔', description: 'Record of arrest details' },
  { value: 'witness_statement', label: 'Witness Statement', icon: '👤', description: 'Recorded witness testimony' },
  { value: 'notice', label: 'Notice u/s 41A CrPC', icon: '📜', description: 'Appearance notice to accused' },
  { value: 'summons', label: 'Summons', icon: '📨', description: 'Court summons document' },
  { value: 'case_diary', label: 'Case Diary Entry', icon: '📖', description: 'Daily investigation record' },
]

export default function DocumentsPage() {
  const { caseId } = useParams()
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [generating, setGenerating] = useState(false)
  const [selectedType, setSelectedType] = useState('fir')
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadDocuments() }, [caseId])

  const loadDocuments = async () => {
    try {
      const response = await api.get(`/api/documents/case/${caseId}`)
      setDocuments(Array.isArray(response.data) ? response.data : response.data.documents || [])
    } catch {
      toast.error('Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  const generateDocument = async () => {
    setGenerating(true)
    try {
      await api.post(`/api/documents/generate/${caseId}`, { doc_type: selectedType })
      toast.success('Document generated successfully')
      loadDocuments()
    } catch {
      toast.error('Document generation failed')
    } finally {
      setGenerating(false)
    }
  }

  const downloadDocument = async (docId: number, docType: string) => {
    try {
      const response = await api.get(`/api/documents/download/${docId}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${docType}_case_${caseId}.docx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      toast.error('Download failed')
    }
  }

  const getDocInfo = (type: string) => DOC_TYPES.find((d) => d.value === type)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 bg-cyan-600/20 rounded-xl flex items-center justify-center">
              <Scale className="w-5 h-5 text-cyan-400" />
            </div>
            Legal Documents
          </h1>
          <p className="text-dark-400 text-sm mt-1">{documents.length} documents generated</p>
        </div>
        <Link to={`/cases/${caseId}`} className="btn-secondary text-sm">← Back to Case</Link>
      </div>

      {/* Generate Section */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card">
        <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
          <Stamp className="w-4 h-4 text-primary-400" />
          Generate Official Document
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-4">
          {DOC_TYPES.map((dt) => (
            <button
              key={dt.value}
              onClick={() => setSelectedType(dt.value)}
              className={`p-3 rounded-xl text-left transition-all border ${
                selectedType === dt.value
                  ? 'bg-primary-600/10 border-primary-600/40 ring-1 ring-primary-500/20'
                  : 'bg-dark-900/60 border-dark-700 hover:border-dark-600'
              }`}
            >
              <span className="text-lg">{dt.icon}</span>
              <p className={`text-xs font-medium mt-1 ${selectedType === dt.value ? 'text-primary-400' : 'text-dark-300'}`}>
                {dt.label.split('(')[0].trim()}
              </p>
            </button>
          ))}
        </div>
        <div className="flex items-center justify-between bg-dark-900/40 rounded-xl p-3">
          <div>
            <p className="text-white text-sm font-medium">{getDocInfo(selectedType)?.label}</p>
            <p className="text-dark-400 text-xs">{getDocInfo(selectedType)?.description}</p>
          </div>
          <button
            onClick={generateDocument}
            disabled={generating}
            className="btn-primary flex items-center gap-2 disabled:opacity-50 whitespace-nowrap"
          >
            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            {generating ? 'Generating...' : 'Generate'}
          </button>
        </div>
      </motion.div>

      {/* Generated Documents */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
          <FileText className="w-4 h-4 text-green-400" />
          Generated Documents
        </h2>
        {loading ? (
          <div className="space-y-3">
            {[1,2,3].map(i => <div key={i} className="card animate-pulse h-16 bg-dark-800/50" />)}
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-12 bg-dark-900/40 rounded-xl border border-dark-700/50">
            <FileText className="w-12 h-12 text-dark-600 mx-auto mb-3" />
            <p className="text-dark-400">No documents generated yet</p>
            <p className="text-dark-500 text-xs mt-1">Select a document type above and click Generate</p>
          </div>
        ) : (
          <div className="space-y-2">
            {documents.map((doc, i) => {
              const info = getDocInfo(doc.doc_type)
              return (
                <motion.div
                  key={doc.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-center justify-between p-4 bg-dark-900/60 rounded-xl border border-dark-700/50 hover:border-dark-600 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{info?.icon || '📄'}</span>
                    <div>
                      <p className="text-white text-sm font-medium">{info?.label || doc.doc_type}</p>
                      <p className="text-dark-400 text-xs flex items-center gap-1 mt-0.5">
                        <Clock className="w-3 h-3" />
                        {new Date(doc.generated_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => downloadDocument(doc.id, doc.doc_type)}
                    className="flex items-center gap-2 px-3 py-2 bg-dark-800 hover:bg-dark-700 rounded-lg text-dark-300 hover:text-white transition-colors border border-dark-700"
                  >
                    <Download className="w-4 h-4" />
                    <span className="text-xs font-medium">Download</span>
                  </button>
                </motion.div>
              )
            })}
          </div>
        )}
      </motion.div>
    </div>
  )
}
