import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FileText, Download, Plus, Loader2 } from 'lucide-react'
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
  { value: 'fir', label: 'First Information Report (FIR)' },
  { value: 'chargesheet', label: 'Charge Sheet' },
  { value: 'seizure_memo', label: 'Seizure Memo' },
  { value: 'medical_letter', label: 'Medical Examination Letter' },
  { value: 'court_letter', label: 'Court Letter' },
  { value: 'arrest_memo', label: 'Arrest Memo' },
]

export default function DocumentsPage() {
  const { caseId } = useParams()
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [generating, setGenerating] = useState(false)
  const [selectedType, setSelectedType] = useState('fir')

  useEffect(() => {
    loadDocuments()
  }, [caseId])

  const loadDocuments = async () => {
    try {
      const response = await api.get(`/api/documents/case/${caseId}`)
      setDocuments(response.data)
    } catch {
      toast.error('Failed to load documents')
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

  const getDocLabel = (type: string) => {
    return DOC_TYPES.find((d) => d.value === type)?.label || type
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-white">Documents — Case #{caseId}</h1>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card"
      >
        <h2 className="text-lg font-semibold text-white mb-4">Generate Document</h2>
        <div className="flex gap-4">
          <select
            className="input flex-1"
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
          >
            {DOC_TYPES.map((dt) => (
              <option key={dt.value} value={dt.value}>{dt.label}</option>
            ))}
          </select>
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

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card"
      >
        <h2 className="text-lg font-semibold text-white mb-4">Generated Documents</h2>
        {documents.length === 0 ? (
          <p className="text-dark-400 text-center py-8">No documents generated yet</p>
        ) : (
          <div className="space-y-3">
            {documents.map((doc, i) => (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-center justify-between p-4 bg-dark-900 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-primary-400" />
                  <div>
                    <p className="text-white font-medium">{getDocLabel(doc.doc_type)}</p>
                    <p className="text-dark-400 text-sm">
                      Generated on {new Date(doc.generated_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => downloadDocument(doc.id, doc.doc_type)}
                  className="flex items-center gap-2 px-3 py-2 bg-dark-700 hover:bg-dark-600 rounded-lg text-dark-300 hover:text-white transition-colors"
                >
                  <Download className="w-4 h-4" />
                  <span className="text-sm">Download</span>
                </button>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  )
}
