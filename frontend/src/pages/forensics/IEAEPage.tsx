import { useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Shield, Upload, FileImage, FileAudio, FileText, File,
  CheckCircle, XCircle, Loader2, Clock, AlertTriangle,
  Camera, Fingerprint, Car, FileSearch, Hash, Mic, Eye, Target,
  Skull, Dna, CreditCard, ScanLine, Brain, Image,
  Crosshair, Zap, ChevronDown, ChevronRight,
} from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import api from '../../api/client'
import { useAuthStore } from '../../store/authStore'

interface Classification {
  type: string
  mime_type: string
  confidence: number
  ai_enhanced?: boolean
  description?: string
  detected_elements?: string[]
}

interface ChecklistItem {
  category: string
  state: 'completed' | 'not_found' | 'needs_manual_review' | 'not_applicable'
  findings_count: number
  confidence: number
  details: string
}

interface CompletenessData {
  scores: {
    evidence_collection_score: number
    evidence_analysis_score: number
    evidence_verification_score: number
    overall_completeness: number
  }
  missing_analyses: string[]
  recommendations: string[]
}

interface CorrelationItem {
  source_evidence_id: number
  target_evidence_id: number
  correlation_type: string
  confidence: number
  source_filename?: string
  target_filename?: string
  details?: any
}

interface PassResult {
  pass_number: number
  pass_name: string
  tool_key: string
  status: string
  confidence: number | null
  findings_summary: string
  execution_time_ms: number
}

interface ToolProgress {
  tool_key: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  confidence?: number
  execution_time_ms?: number
  output?: any
}

const TOOL_META: Record<string, { icon: any; label: string; color: string; bgColor: string }> = {
  image_ocr: { icon: FileSearch, label: 'OCR Analysis', color: 'text-blue-400', bgColor: 'bg-blue-500/10' },
  image_object_detect: { icon: Target, label: 'Object Detection', color: 'text-amber-400', bgColor: 'bg-amber-500/10' },
  image_exif: { icon: Camera, label: 'EXIF Metadata', color: 'text-cyan-400', bgColor: 'bg-cyan-500/10' },
  audio_transcribe: { icon: Mic, label: 'Audio Transcription', color: 'text-violet-400', bgColor: 'bg-violet-500/10' },
  document_ocr: { icon: FileText, label: 'Document OCR', color: 'text-blue-400', bgColor: 'bg-blue-500/10' },
  document_pdf_parse: { icon: File, label: 'PDF Analysis', color: 'text-orange-400', bgColor: 'bg-orange-500/10' },
  digital_hash: { icon: Hash, label: 'Evidence Integrity', color: 'text-emerald-400', bgColor: 'bg-emerald-500/10' },
  digital_metadata: { icon: FileSearch, label: 'File Metadata', color: 'text-slate-400', bgColor: 'bg-slate-500/10' },
  digital_file_identify: { icon: ScanLine, label: 'File Identification', color: 'text-teal-400', bgColor: 'bg-teal-500/10' },
  document_summarize: { icon: Brain, label: 'AI Summary', color: 'text-purple-400', bgColor: 'bg-purple-500/10' },
  face_detect: { icon: Eye, label: 'Face Detection', color: 'text-pink-400', bgColor: 'bg-pink-500/10' },
  fingerprint_match: { icon: Fingerprint, label: 'Fingerprint Match', color: 'text-purple-400', bgColor: 'bg-purple-500/10' },
  dna_search: { icon: Dna, label: 'DNA Analysis', color: 'text-green-400', bgColor: 'bg-green-500/10' },
  vehicle_detect: { icon: Car, label: 'Vehicle Detection', color: 'text-sky-400', bgColor: 'bg-sky-500/10' },
  license_plate_ocr: { icon: CreditCard, label: 'License Plate', color: 'text-yellow-400', bgColor: 'bg-yellow-500/10' },
  weapon_detect: { icon: Crosshair, label: 'Weapon Detection', color: 'text-red-400', bgColor: 'bg-red-500/10' },
  image_similarity: { icon: Image, label: 'Image Similarity', color: 'text-indigo-400', bgColor: 'bg-indigo-500/10' },
  crime_scene_analysis: { icon: Skull, label: 'Crime Scene AI', color: 'text-red-400', bgColor: 'bg-red-500/10' },
}

function getToolMeta(toolKey: string) {
  return TOOL_META[toolKey] || { icon: Zap, label: toolKey.replace(/_/g, ' '), color: 'text-dark-400', bgColor: 'bg-dark-700' }
}

export default function IEAEPage() {
  const { accessToken } = useAuthStore()
  const [isInvestigating, setIsInvestigating] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<{ name: string; classification?: Classification; url?: string } | null>(null)
  const [toolProgress, setToolProgress] = useState<ToolProgress[]>([])
  const [checklist, setChecklist] = useState<{ items: ChecklistItem[]; completed_count: number; needs_review_count: number } | null>(null)
  const [completeness, setCompleteness] = useState<CompletenessData | null>(null)
  const [correlations, setCorrelations] = useState<CorrelationItem[]>([])
  const [passResults, setPassResults] = useState<PassResult[]>([])
  const [aiPlanReasoning, setAiPlanReasoning] = useState('')
  const [report, setReport] = useState('')
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set())
  const [error, setError] = useState('')
  const filePreviewRef = useRef<string | null>(null)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (!acceptedFiles.length) return
    const file = acceptedFiles[0]
    setError('')
    setIsUploading(true)
    setUploadedFile(null)
    setToolProgress([])
    setChecklist(null)
    setCompleteness(null)
    setCorrelations([])
    setPassResults([])
    setAiPlanReasoning('')
    setReport('')

    const previewUrl = file.type.startsWith('image/') ? URL.createObjectURL(file) : null
    filePreviewRef.current = previewUrl

    try {
      const sessionRes = await api.post('/api/ai-investigation/sessions', { title: `IEAE: ${file.name}` })
      const sessionId = sessionRes.data.session_id

      const formData = new FormData()
      formData.append('file', file)
      const uploadRes = await api.post(`/api/ai-investigation/sessions/${sessionId}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      setUploadedFile({
        name: uploadRes.data.original_filename,
        classification: uploadRes.data.classification,
        url: previewUrl || undefined,
      })
      setIsUploading(false)

      setIsInvestigating(true)
      const investigateForm = new FormData()
      investigateForm.append('message', '')

      const response = await fetch(`/api/ai-investigation/sessions/${sessionId}/investigate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${accessToken}` },
        body: investigateForm,
      })

      if (!response.ok) throw new Error('Investigation failed')

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (reader) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''

        for (const part of parts) {
          const lines = part.split('\n')
          let eventName = 'message'
          let dataStr = ''
          for (const line of lines) {
            if (line.startsWith('event: ')) eventName = line.slice(7).trim()
            else if (line.startsWith('data: ')) dataStr = line.slice(6)
          }
          if (dataStr) {
            try {
              const data = JSON.parse(dataStr)
              handleSSE(eventName, data)
            } catch {}
          }
        }
      }
    } catch (e: any) {
      setError(e.message || 'Analysis failed')
    } finally {
      setIsUploading(false)
      setIsInvestigating(false)
    }
  }, [accessToken])

  const handleSSE = (event: string, data: any) => {
    switch (event) {
      case 'classification':
      case 'ai_classification':
        setUploadedFile(prev => prev ? { ...prev, classification: data } : null)
        break
      case 'plan':
        if (Array.isArray(data.tools_selected)) {
          setToolProgress(data.tools_selected.map((t: string) => ({ tool_key: t, status: 'pending' as const })))
        }
        if (data.ai_reasoning) setAiPlanReasoning(data.ai_reasoning)
        break
      case 'tool_start':
        setToolProgress(prev => prev.map(t => t.tool_key === data.tool_key ? { ...t, status: 'running' as const } : t))
        break
      case 'tool_complete':
        setToolProgress(prev => prev.map(t => t.tool_key === data.tool_key ? {
          ...t,
          status: data.status === 'completed' ? 'completed' as const : 'failed' as const,
          confidence: data.confidence,
          execution_time_ms: data.execution_time_ms,
          output: data.output,
        } : t))
        break
      case 'pass_complete':
        setPassResults(prev => [...prev, data as PassResult])
        break
      case 'checklist':
        setChecklist(data)
        break
      case 'completeness':
        setCompleteness(data)
        break
      case 'correlations':
        setCorrelations(data.correlations || [])
        break
      case 'report_complete':
        setReport(data.report || '')
        break
      case 'complete':
        if (data.checklist && !checklist) setChecklist(data.checklist)
        if (data.completeness && !completeness) setCompleteness(data.completeness)
        if (data.correlations?.length) setCorrelations(data.correlations)
        break
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    disabled: isInvestigating || isUploading,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'],
      'audio/*': ['.wav', '.mp3', '.ogg', '.flac', '.m4a'],
      'video/*': ['.mp4', '.avi', '.mov', '.mkv'],
      'application/pdf': ['.pdf'],
      'text/*': ['.txt', '.csv'],
    },
  })

  const toggleTool = (key: string) => {
    setExpandedTools(prev => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })
  }

  const completedCount = toolProgress.filter(t => t.status === 'completed').length
  const totalTools = toolProgress.length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
          <Shield className="w-5 h-5 text-emerald-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">IEAE Engine</h1>
          <p className="text-dark-400 text-sm">Intelligent Evidence Assurance Engine — Upload evidence for comprehensive forensic analysis</p>
        </div>
      </div>

      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className={`relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
          isDragActive ? 'border-emerald-400 bg-emerald-500/5' :
          isInvestigating ? 'border-dark-700 bg-dark-900/50 cursor-not-allowed' :
          'border-dark-700 hover:border-emerald-500/50 hover:bg-dark-900/50'
        }`}
      >
        <input {...getInputProps()} />
        {isUploading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-dark-300">Uploading and classifying evidence...</p>
          </div>
        ) : isInvestigating ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-dark-300">IEAE analysis in progress... ({completedCount}/{totalTools} tools)</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className="w-10 h-10 text-dark-500" />
            <p className="text-dark-300 font-medium">Drop evidence files here or click to browse</p>
            <p className="text-dark-500 text-sm">Images, audio, video, PDF, text — sensitive forensic content supported</p>
            <div className="flex gap-2 mt-2">
              <span className="px-2 py-1 rounded-full text-[10px] bg-dark-800 text-dark-400"><FileImage className="w-3 h-3 inline mr-1" />Images</span>
              <span className="px-2 py-1 rounded-full text-[10px] bg-dark-800 text-dark-400"><FileAudio className="w-3 h-3 inline mr-1" />Audio</span>
              <span className="px-2 py-1 rounded-full text-[10px] bg-dark-800 text-dark-400"><FileText className="w-3 h-3 inline mr-1" />Documents</span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center gap-3">
          <XCircle className="w-5 h-5 text-red-400 shrink-0" />
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      )}

      {/* Classification */}
      {uploadedFile?.classification && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Camera className="w-4 h-4 text-cyan-400" /> Evidence Classification
          </h3>
          <div className="flex items-start gap-4">
            {uploadedFile.url && (
              <img src={uploadedFile.url} alt="Evidence" className="w-20 h-20 object-cover rounded-lg border border-dark-700" />
            )}
            <div className="flex-1 space-y-1">
              <p className="text-white text-sm font-medium">{uploadedFile.name}</p>
              <p className="text-dark-400 text-xs">Type: <span className="text-emerald-400">{uploadedFile.classification.type}</span></p>
              <p className="text-dark-400 text-xs">Confidence: <span className="text-emerald-400">{(uploadedFile.classification.confidence * 100).toFixed(0)}%</span></p>
              {uploadedFile.classification.description && (
                <p className="text-dark-400 text-xs mt-1">{uploadedFile.classification.description}</p>
              )}
              {uploadedFile.classification.detected_elements?.length ? (
                <div className="flex flex-wrap gap-1 mt-2">
                  {uploadedFile.classification.detected_elements.map((el, i) => (
                    <span key={i} className="px-2 py-0.5 rounded-full text-[10px] bg-dark-800 text-dark-300 border border-dark-700">{el}</span>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        </motion.div>
      )}

      {/* AI Plan Reasoning */}
      {aiPlanReasoning && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card p-4">
          <h3 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
            <Brain className="w-4 h-4 text-purple-400" /> AI Analysis Plan
          </h3>
          <p className="text-dark-300 text-sm leading-relaxed">{aiPlanReasoning}</p>
        </motion.div>
      )}

      {/* Tool Progress */}
      {toolProgress.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-400" /> Analysis Pipeline ({completedCount}/{totalTools})
          </h3>
          <div className="space-y-2">
            {toolProgress.map((tool) => {
              const meta = getToolMeta(tool.tool_key)
              const Icon = meta.icon
              const isExpanded = expandedTools.has(tool.tool_key)
              return (
                <div key={tool.tool_key} className="rounded-lg border border-dark-700/50 overflow-hidden">
                  <div
                    className="flex items-center gap-3 px-3 py-2 cursor-pointer hover:bg-dark-800/30"
                    onClick={() => tool.output && toggleTool(tool.tool_key)}
                  >
                    <div className={`w-7 h-7 rounded-lg ${meta.bgColor} flex items-center justify-center shrink-0`}>
                      <Icon className={`w-3.5 h-3.5 ${meta.color}`} />
                    </div>
                    <span className="text-sm text-dark-200 flex-1">{meta.label}</span>
                    {tool.status === 'pending' && <Clock className="w-4 h-4 text-dark-500" />}
                    {tool.status === 'running' && <Loader2 className="w-4 h-4 text-amber-400 animate-spin" />}
                    {tool.status === 'completed' && <CheckCircle className="w-4 h-4 text-emerald-400" />}
                    {tool.status === 'failed' && <XCircle className="w-4 h-4 text-red-400" />}
                    {tool.confidence != null && (
                      <span className="text-[10px] text-dark-400 ml-1">{(tool.confidence * 100).toFixed(0)}%</span>
                    )}
                    {tool.execution_time_ms != null && (
                      <span className="text-[10px] text-dark-500 ml-1">{(tool.execution_time_ms / 1000).toFixed(1)}s</span>
                    )}
                    {tool.output && (isExpanded ? <ChevronDown className="w-3.5 h-3.5 text-dark-500" /> : <ChevronRight className="w-3.5 h-3.5 text-dark-500" />)}
                  </div>
                  <AnimatePresence>
                    {isExpanded && tool.output && (
                      <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden">
                        <div className="px-3 pb-3 pt-1 border-t border-dark-800">
                          <pre className="text-[11px] text-dark-300 whitespace-pre-wrap max-h-48 overflow-y-auto">
                            {typeof tool.output === 'string' ? tool.output : JSON.stringify(tool.output, null, 2)}
                          </pre>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )
            })}
          </div>
        </motion.div>
      )}

      {/* Multi-Pass Results */}
      {passResults.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Target className="w-4 h-4 text-blue-400" /> Multi-Pass Analysis
          </h3>
          <div className="space-y-2">
            {passResults.map((pass) => (
              <div key={pass.pass_number} className="flex items-start gap-3 px-3 py-2 rounded-lg bg-dark-800/30 border border-dark-700/30">
                <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center shrink-0 mt-0.5">
                  <span className="text-[10px] font-bold text-blue-400">{pass.pass_number}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-white">{pass.pass_name}</p>
                  <p className="text-[11px] text-dark-400 mt-0.5">{pass.findings_summary}</p>
                </div>
                <div className="text-right shrink-0">
                  {pass.confidence != null && <p className="text-[10px] text-emerald-400">{(pass.confidence * 100).toFixed(0)}%</p>}
                  <p className="text-[10px] text-dark-500">{(pass.execution_time_ms / 1000).toFixed(1)}s</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Evidence Checklist */}
      {checklist && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400" /> Evidence Checklist
            <span className="ml-auto text-[10px] text-dark-400">
              {checklist.completed_count} complete • {checklist.needs_review_count} need review
            </span>
          </h3>
          <div className="space-y-1.5">
            {checklist.items.map((item, i) => (
              <div key={i} className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dark-800/20">
                {item.state === 'completed' && <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />}
                {item.state === 'not_found' && <XCircle className="w-3.5 h-3.5 text-red-400 shrink-0" />}
                {item.state === 'needs_manual_review' && <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />}
                {item.state === 'not_applicable' && <div className="w-3.5 h-3.5 rounded-full bg-dark-600 shrink-0" />}
                <span className="text-xs text-dark-200 flex-1">{item.category}</span>
                <span className="text-[10px] text-dark-500">{item.findings_count} findings</span>
                <span className="text-[10px] text-dark-500">{(item.confidence * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Completeness Score */}
      {completeness && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Shield className="w-4 h-4 text-emerald-400" /> Completeness Assessment
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            {[
              { label: 'Overall', value: completeness.scores.overall_completeness },
              { label: 'Collection', value: completeness.scores.evidence_collection_score },
              { label: 'Analysis', value: completeness.scores.evidence_analysis_score },
              { label: 'Verification', value: completeness.scores.evidence_verification_score },
            ].map(s => (
              <div key={s.label} className="text-center p-3 rounded-xl bg-dark-800/50 border border-dark-700/30">
                <p className={`text-xl font-bold ${s.value >= 70 ? 'text-emerald-400' : s.value >= 40 ? 'text-amber-400' : 'text-red-400'}`}>
                  {s.value.toFixed(0)}%
                </p>
                <p className="text-[10px] text-dark-400 uppercase mt-1">{s.label}</p>
              </div>
            ))}
          </div>
          {completeness.missing_analyses.length > 0 && (
            <div className="mb-3">
              <p className="text-xs text-dark-400 mb-1.5">Missing Analyses:</p>
              <div className="flex flex-wrap gap-1.5">
                {completeness.missing_analyses.map((m, i) => (
                  <span key={i} className="px-2 py-0.5 rounded-full text-[10px] bg-red-500/10 text-red-400 border border-red-500/20">{m}</span>
                ))}
              </div>
            </div>
          )}
          {completeness.recommendations.length > 0 && (
            <div>
              <p className="text-xs text-dark-400 mb-1.5">Recommendations:</p>
              <ul className="space-y-1">
                {completeness.recommendations.map((r, i) => (
                  <li key={i} className="text-[11px] text-dark-300 flex items-start gap-1.5">
                    <ChevronRight className="w-3 h-3 text-emerald-400 mt-0.5 shrink-0" /> {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}

      {/* Cross-Evidence Correlations */}
      {correlations.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Fingerprint className="w-4 h-4 text-purple-400" /> Cross-Evidence Correlations
          </h3>
          <div className="space-y-2">
            {correlations.map((c, i) => (
              <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-dark-800/30 border border-dark-700/30">
                <span className="text-xs text-dark-300 flex-1">
                  {c.source_filename || `Evidence #${c.source_evidence_id}`} ↔ {c.target_filename || `Evidence #${c.target_evidence_id}`}
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400">{c.correlation_type}</span>
                <span className="text-[10px] text-dark-400">{(c.confidence * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Report */}
      {report && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-400" /> Investigation Report
          </h3>
          <div className="prose prose-invert prose-sm max-w-none text-dark-300">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown>
          </div>
        </motion.div>
      )}
    </div>
  )
}
