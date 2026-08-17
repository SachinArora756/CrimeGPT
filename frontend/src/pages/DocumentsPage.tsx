import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FileText, Download, Plus, Loader2, Scale, Clock, Hash, Trash2, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../api/client'
import { useEvidenceDocStore, DocumentItem } from '../store/evidenceDocStore'

const DOC_SECTIONS = [
  {
    id: 'investigation',
    label: 'Core Investigation',
    icon: '📋',
    docs: [
      { value: 'fir', label: 'First Information Report (FIR)', description: 'Section 173 BNSS — Official police complaint' },
      { value: 'case_diary', label: 'Case Diary Entry', description: 'Section 192 BNSS — Daily investigation record' },
      { value: 'spot_panchnama', label: 'Spot / Scene Panchnama', description: 'Section 176 BNSS — Scene of crime inspection' },
      { value: 'witness_statement', label: 'Witness Statement', description: 'Section 180/181 BNSS — Recorded testimony' },
      { value: 'chargesheet', label: 'Charge Sheet', description: 'Section 193 BNSS — Final report to court' },
      { value: 'closure_report', label: 'Closure / Untraced Report', description: 'Section 193 BNSS — Case closure final report' },
    ],
  },
  {
    id: 'arrest',
    label: 'Arrest & Custody',
    icon: '🚔',
    docs: [
      { value: 'arrest_memo', label: 'Arrest Memo', description: 'Section 36 BNSS — Record of arrest' },
      { value: 'notice', label: 'Notice u/s 35 BNSS', description: 'Section 35(3) BNSS — Appearance notice' },
      { value: 'remand_request', label: 'Remand Request', description: 'Section 187 BNSS — Police custody remand' },
      { value: 'court_custody', label: 'Court Custody Application', description: 'Section 187(2)-(3) BNSS — Judicial custody' },
    ],
  },
  {
    id: 'search',
    label: 'Search & Seizure',
    icon: '🔍',
    docs: [
      { value: 'search_memo', label: 'Search Memo / Panchnama', description: 'Section 185-190 BNSS — Search proceedings' },
      { value: 'seizure_memo', label: 'Seizure Memo', description: 'Section 185-186 BNSS — Seizure of property' },
      { value: 'seizure_receipt', label: 'Seizure Receipt', description: 'Section 185-186 BNSS — Acknowledgment receipt' },
      { value: 'accused_panchanama', label: 'Accused Panchanama', description: 'Section 53 BNSS — Personal search of accused' },
      { value: 'property_release', label: 'Property Release Order', description: 'Section 451/457 BNSS — Release seized property' },
    ],
  },
  {
    id: 'production',
    label: 'Production & Data Requests',
    icon: '📡',
    docs: [
      { value: 'production_order', label: 'Production Order (§94 BNSS)', description: 'Section 94 BNSS — Summons to produce documents/things' },
      { value: 'cdr_ipdr_request', label: 'CDR / IPDR Request', description: 'Section 94 BNSS — Telecom call/internet records' },
      { value: 'platform_data_req', label: 'Platform Data Request', description: 'Section 94 BNSS r/w IT Act — Social media/ISP data' },
      { value: 'banking_data_req', label: 'Banking Data Request', description: 'Section 94 BNSS — Bank/UPI transaction records' },
    ],
  },
  {
    id: 'cyber',
    label: 'IT Act & Cyber',
    icon: '🌐',
    docs: [
      { value: 'content_removal', label: 'Content Removal Notice', description: 'Section 79(3)(b) IT Act — Notice to intermediary' },
      { value: 'data_preservation', label: 'Data Preservation Request', description: 'Section 67C IT Act — Preserve electronic records' },
      { value: 'content_blocking', label: 'Content Blocking Request', description: 'Section 69A IT Act — Block public access' },
    ],
  },
  {
    id: 'evidence',
    label: 'Evidence & Forensics',
    icon: '🔬',
    docs: [
      { value: 'bsa_63_certificate', label: 'Electronic Evidence Certificate', description: 'Section 63 BSA 2023 — Certificate for e-records' },
      { value: 'fsl_forwarding', label: 'FSL Forwarding Letter', description: 'Section 176/349 BNSS — Forward exhibits to FSL' },
      { value: 'face_identification', label: 'Face Identification (TIP)', description: 'Section 9 BSA — Test identification parade' },
    ],
  },
  {
    id: 'medical',
    label: 'Medical & Court',
    icon: '🏥',
    docs: [
      { value: 'medical_letter', label: 'Medical Examination Letter', description: 'Section 53/54 BNSS — Request for examination' },
      { value: 'medical_treatment_letter', label: 'Medical Treatment Letter', description: 'Section 36 BNSS — Treatment for accused/victim' },
      { value: 'court_letter', label: 'Court Submission Letter', description: 'Section 193/194 BNSS — Forwarding to court' },
    ],
  },
  {
    id: 'special',
    label: 'Special Reports',
    icon: '📑',
    docs: [
      { value: 'inquest_report', label: 'Inquest Report', description: 'Section 194 BNSS — Unnatural death documentation' },
      { value: 'missing_person', label: 'Missing Person Report', description: 'Section 175 BNSS — Missing person documentation' },
    ],
  },
]

export default function DocumentsPage() {
  const { caseId } = useParams()
  const { fetchDocuments, invalidateCase, deleteDocument } = useEvidenceDocStore()
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [generating, setGenerating] = useState(false)
  const [selectedType, setSelectedType] = useState('fir')
  const [activeSection, setActiveSection] = useState('investigation')
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadDocuments() }, [caseId])

  const loadDocuments = async () => {
    try {
      const items = await fetchDocuments(caseId!)
      setDocuments(items)
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
      invalidateCase(caseId!)
      const items = await fetchDocuments(caseId!, true)
      setDocuments(items)
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
      link.setAttribute('download', `${docType}_case_${caseId}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      toast.error('Download failed')
    }
  }

  const handleDeleteDocument = async (docId: number) => {
    if (!confirm('Are you sure you want to delete this document? This action cannot be undone.')) return
    try {
      await deleteDocument(caseId!, docId)
      setDocuments((prev) => prev.filter((d) => d.id !== docId))
      toast.success('Document deleted')
    } catch {
      toast.error('Failed to delete document')
    }
  }

  const currentSection = DOC_SECTIONS.find(s => s.id === activeSection)!
  const allDocs = DOC_SECTIONS.flatMap(s => s.docs)
  const getDocInfo = (type: string) => allDocs.find((d) => d.value === type)

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 bg-cyan-600/20 rounded-xl flex items-center justify-center shrink-0">
              <Scale className="w-5 h-5 text-cyan-400" />
            </div>
            Legal Documents
          </h1>
          <p className="text-dark-400 text-sm mt-1">{documents.length} documents generated</p>
        </div>
        <Link to={`/cases/${caseId}`} className="btn-secondary text-sm whitespace-nowrap">← Back to Case</Link>
      </div>

      {/* Generate Section */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card">
        <h2 className="text-base font-semibold text-white mb-4">Generate Official Document</h2>

        {/* Section Tabs */}
        <div className="flex flex-wrap gap-2 mb-4">
          {DOC_SECTIONS.map((section) => (
            <button
              key={section.id}
              onClick={() => { setActiveSection(section.id); setSelectedType(section.docs[0].value) }}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all border ${
                activeSection === section.id
                  ? 'bg-primary-600/15 border-primary-600/40 text-primary-400'
                  : 'bg-dark-900/60 border-dark-700 text-dark-400 hover:border-dark-600 hover:text-dark-300'
              }`}
            >
              <span>{section.icon}</span>
              {section.label}
            </button>
          ))}
        </div>

        {/* Documents in Active Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 mb-4">
          {currentSection.docs.map((dt) => (
            <button
              key={dt.value}
              onClick={() => setSelectedType(dt.value)}
              className={`p-3 rounded-xl text-left transition-all border ${
                selectedType === dt.value
                  ? 'bg-primary-600/10 border-primary-600/40 ring-1 ring-primary-500/20'
                  : 'bg-dark-900/60 border-dark-700 hover:border-dark-600'
              }`}
            >
              <p className={`text-sm font-medium ${selectedType === dt.value ? 'text-primary-400' : 'text-dark-300'}`}>
                {dt.label}
              </p>
              <p className="text-dark-500 text-[11px] mt-1 leading-tight">{dt.description}</p>
            </button>
          ))}
        </div>

        {/* Generate Button */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-dark-900/40 rounded-xl p-3">
          <div className="min-w-0">
            <p className="text-white text-sm font-medium truncate">{getDocInfo(selectedType)?.label}</p>
            <p className="text-dark-400 text-xs truncate">{getDocInfo(selectedType)?.description}</p>
          </div>
          <button
            onClick={generateDocument}
            disabled={generating}
            className="btn-primary flex items-center gap-2 disabled:opacity-50 whitespace-nowrap shrink-0"
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
            <p className="text-dark-500 text-xs mt-1">Select a section above, pick a document type, and click Generate</p>
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
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-dark-900/60 rounded-xl border border-dark-700/50 hover:border-dark-600 transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className="w-8 h-8 bg-dark-800 rounded-lg flex items-center justify-center shrink-0">
                      <FileText className="w-4 h-4 text-primary-400" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-white text-sm font-medium truncate">{info?.label || doc.doc_type}</p>
                      <p className="text-dark-400 text-xs flex items-center gap-1 mt-0.5">
                        <Clock className="w-3 h-3 shrink-0" />
                        {new Date(doc.generated_at.endsWith('Z') ? doc.generated_at : doc.generated_at + 'Z').toLocaleString()}
                      </p>
                      <div className="flex items-center gap-1 mt-0.5 text-[10px] overflow-hidden">
                        <Hash className="w-3 h-3 text-green-500 shrink-0" />
                        {doc.file_hash ? (
                          <>
                            <span className="font-mono text-dark-200 truncate" title={doc.file_hash}>{doc.file_hash}</span>
                            <CheckCircle className="w-3 h-3 text-green-500 shrink-0" />
                          </>
                        ) : (
                          <span className="text-dark-500 italic">Hash not computed</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => downloadDocument(doc.id, doc.doc_type)}
                      className="flex items-center gap-2 px-3 py-2 bg-dark-800 hover:bg-dark-700 rounded-lg text-dark-300 hover:text-white transition-colors border border-dark-700"
                    >
                      <Download className="w-4 h-4" />
                      <span className="text-xs font-medium">Download</span>
                    </button>
                    <button
                      onClick={() => handleDeleteDocument(doc.id)}
                      className="flex items-center gap-2 px-3 py-2 bg-dark-800 hover:bg-red-900/30 rounded-lg text-dark-300 hover:text-red-400 transition-colors border border-dark-700 hover:border-red-700/50"
                    >
                      <Trash2 className="w-4 h-4" />
                      <span className="text-xs font-medium">Delete</span>
                    </button>
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}
      </motion.div>
    </div>
  )
}
