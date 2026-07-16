import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Lightbulb, Upload, FileImage, FileAudio, FileText,
  XCircle, Loader2, AlertTriangle,
  Brain, TrendingUp, FileSearch,
  ChevronDown, ChevronRight, Zap,
} from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import api from '../../api/client'
import { useAuthStore } from '../../store/authStore'
import CaseChat from '../../components/forensics/CaseChat'

interface Hypothesis {
  id: string
  title: string
  description: string
  confidence: number
  supporting_evidence: string[]
  contradicting_evidence: string[]
  status: string
}

interface Contradiction {
  id: string
  description: string
  evidence_a: string
  evidence_b: string
  severity: string
  resolution_suggestion?: string
}

interface ConfidenceDashboard {
  overall_confidence: number
  evidence_strength: number
  hypothesis_coverage: number
  contradiction_severity: number
  recommendations: string[]
}

export default function IIDSEPage() {
  const { accessToken } = useAuthStore()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isInvestigating, setIsInvestigating] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<{ name: string; url?: string }[]>([])
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([])
  const [contradictions, setContradictions] = useState<Contradiction[]>([])
  const [confidenceDashboard, setConfidenceDashboard] = useState<ConfidenceDashboard | null>(null)
  const [report, setReport] = useState('')
  const [toolCount, setToolCount] = useState({ completed: 0, total: 0 })
  const [activeTab, setActiveTab] = useState<'hypotheses' | 'contradictions' | 'confidence' | 'report'>('hypotheses')
  const [error, setError] = useState('')
  const [expandedHypothesis, setExpandedHypothesis] = useState<string | null>(null)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (!acceptedFiles.length) return
    setError('')
    setIsUploading(true)
    setUploadedFiles([])
    setHypotheses([])
    setContradictions([])
    setConfidenceDashboard(null)
    setReport('')
    setToolCount({ completed: 0, total: 0 })

    try {
      const title = acceptedFiles.length === 1 ? `IIDSE: ${acceptedFiles[0].name}` : `IIDSE: ${acceptedFiles.length} files`
      const sessionRes = await api.post('/api/ai-investigation/sessions', { title })
      const newSessionId = sessionRes.data.session_id
      setSessionId(newSessionId)

      for (const file of acceptedFiles) {
        const previewUrl = file.type.startsWith('image/') ? URL.createObjectURL(file) : null
        const formData = new FormData()
        formData.append('file', file)
        await api.post(`/api/ai-investigation/sessions/${newSessionId}/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        setUploadedFiles(prev => [...prev, { name: file.name, url: previewUrl || undefined }])
      }

      setIsUploading(false)

      setIsInvestigating(true)
      const investigateForm = new FormData()
      investigateForm.append('message', '')

      const response = await fetch(`/api/ai-investigation/sessions/${newSessionId}/investigate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${accessToken}` },
        body: investigateForm,
      })

      if (!response.ok) throw new Error('Investigation failed')

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let completed = 0
      let total = 0

      while (reader) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''

        for (const part of parts) {
          const lines = part.split('\n')
          let eventName = 'message'
          const dataLines: string[] = []
          for (const line of lines) {
            if (line.startsWith('event: ')) eventName = line.slice(7).trim()
            else if (line.startsWith('data: ')) dataLines.push(line.slice(6))
          }
          const dataStr = dataLines.join('\n')
          if (dataStr) {
            try {
              const data = JSON.parse(dataStr)
              switch (eventName) {
                case 'plan':
                  if (Array.isArray(data.tools_selected)) {
                    total = data.tools_selected.length
                    setToolCount({ completed: 0, total })
                  }
                  break
                case 'tool_complete':
                  completed++
                  setToolCount({ completed, total })
                  break
                case 'hypotheses':
                  setHypotheses(data.hypotheses || [])
                  break
                case 'contradictions':
                  setContradictions(data.contradictions || [])
                  break
                case 'confidence_dashboard':
                  setConfidenceDashboard(data)
                  break
                case 'report_complete':
                  setReport(data.report || '')
                  break
                case 'complete':
                  if (data.hypotheses?.length && !hypotheses.length) setHypotheses(data.hypotheses)
                  break
                case 'error':
                  setError(data.error || 'Investigation pipeline error')
                  break
              }
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

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    disabled: isInvestigating || isUploading,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'],
      'audio/*': ['.wav', '.mp3', '.ogg', '.flac', '.m4a'],
      'video/*': ['.mp4', '.avi', '.mov', '.mkv'],
      'application/pdf': ['.pdf'],
      'text/*': ['.txt', '.csv'],
    },
  })

  const hasResults = hypotheses.length > 0 || contradictions.length > 0 || confidenceDashboard || report

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
          <Lightbulb className="w-5 h-5 text-purple-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">IIDSE Intelligence</h1>
          <p className="text-dark-400 text-sm">Investigation Intelligence & Decision Support Engine — Upload evidence for strategic analysis</p>
        </div>
      </div>

      {/* Uploaded Files Indicator */}
      {uploadedFiles.length > 0 && !isUploading && !isInvestigating && (
        <div className="flex flex-wrap gap-2">
          {uploadedFiles.map((f, idx) => (
            <div key={idx} className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20">
              {f.url ? <FileImage className="w-3.5 h-3.5 text-purple-400" /> : <FileText className="w-3.5 h-3.5 text-purple-400" />}
              <span className="text-xs text-purple-300">{f.name}</span>
            </div>
          ))}
        </div>
      )}

      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className={`relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
          isDragActive ? 'border-purple-400 bg-purple-500/5' :
          isInvestigating ? 'border-dark-700 bg-dark-900/50 cursor-not-allowed' :
          'border-dark-700 hover:border-purple-500/50 hover:bg-dark-900/50'
        }`}
      >
        <input {...getInputProps()} />
        {isUploading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-10 h-10 text-purple-400 animate-spin" />
            <p className="text-dark-300">Uploading evidence...</p>
          </div>
        ) : isInvestigating ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-10 h-10 text-purple-400 animate-spin" />
            <p className="text-dark-300">IIDSE analysis in progress... ({toolCount.completed}/{toolCount.total} tools)</p>
            <p className="text-dark-500 text-xs">Generating hypotheses, detecting contradictions, building confidence model...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className="w-10 h-10 text-dark-500" />
            <p className="text-dark-300 font-medium">Drop evidence files here or click to browse</p>
            <p className="text-dark-500 text-sm">Upload multiple files for hypothesis generation, contradiction detection & decision support</p>
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

      {/* Results Tabs */}
      {hasResults && (
        <>
          <div className="flex gap-1 p-1 bg-dark-900/80 rounded-xl border border-dark-700/50">
            {[
              { key: 'hypotheses' as const, icon: Brain, label: 'Hypotheses', count: hypotheses.length },
              { key: 'contradictions' as const, icon: AlertTriangle, label: 'Contradictions', count: contradictions.length },
              { key: 'confidence' as const, icon: TrendingUp, label: 'Confidence', count: null },
              { key: 'report' as const, icon: FileSearch, label: 'Report', count: null },
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                  activeTab === tab.key
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                    : 'text-dark-400 hover:text-dark-200 hover:bg-dark-800/50'
                }`}
              >
                <tab.icon className="w-3.5 h-3.5" />
                {tab.label}
                {tab.count != null && tab.count > 0 && (
                  <span className="px-1.5 py-0.5 rounded-full text-[9px] bg-purple-500/20 text-purple-400">{tab.count}</span>
                )}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <AnimatePresence mode="wait">
            {activeTab === 'hypotheses' && (
              <motion.div key="hypotheses" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-3">
                {hypotheses.length === 0 ? (
                  <div className="card p-8 text-center text-dark-400">No hypotheses generated yet</div>
                ) : hypotheses.map(h => (
                  <div key={h.id} className="card p-4">
                    <div
                      className="flex items-start gap-3 cursor-pointer"
                      onClick={() => setExpandedHypothesis(expandedHypothesis === h.id ? null : h.id)}
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                        h.confidence >= 0.7 ? 'bg-emerald-500/10' : h.confidence >= 0.4 ? 'bg-amber-500/10' : 'bg-red-500/10'
                      }`}>
                        <Brain className={`w-4 h-4 ${
                          h.confidence >= 0.7 ? 'text-emerald-400' : h.confidence >= 0.4 ? 'text-amber-400' : 'text-red-400'
                        }`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white">{h.title}</p>
                        <p className="text-xs text-dark-400 mt-0.5">{h.description.slice(0, 100)}{h.description.length > 100 ? '...' : ''}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <p className={`text-sm font-bold ${
                          h.confidence >= 0.7 ? 'text-emerald-400' : h.confidence >= 0.4 ? 'text-amber-400' : 'text-red-400'
                        }`}>{(h.confidence * 100).toFixed(0)}%</p>
                        <p className="text-[10px] text-dark-500 capitalize">{h.status}</p>
                      </div>
                      {expandedHypothesis === h.id ? <ChevronDown className="w-4 h-4 text-dark-500" /> : <ChevronRight className="w-4 h-4 text-dark-500" />}
                    </div>
                    <AnimatePresence>
                      {expandedHypothesis === h.id && (
                        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                          <div className="mt-3 pt-3 border-t border-dark-700/50 space-y-2">
                            <p className="text-xs text-dark-300">{h.description}</p>
                            {h.supporting_evidence.length > 0 && (
                              <div>
                                <p className="text-[10px] text-dark-400 uppercase mb-1">Supporting Evidence</p>
                                <div className="flex flex-wrap gap-1">
                                  {h.supporting_evidence.map((e, i) => (
                                    <span key={i} className="px-2 py-0.5 text-[10px] rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">{e}</span>
                                  ))}
                                </div>
                              </div>
                            )}
                            {h.contradicting_evidence.length > 0 && (
                              <div>
                                <p className="text-[10px] text-dark-400 uppercase mb-1">Contradicting Evidence</p>
                                <div className="flex flex-wrap gap-1">
                                  {h.contradicting_evidence.map((e, i) => (
                                    <span key={i} className="px-2 py-0.5 text-[10px] rounded-full bg-red-500/10 text-red-400 border border-red-500/20">{e}</span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                ))}
              </motion.div>
            )}

            {activeTab === 'contradictions' && (
              <motion.div key="contradictions" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-3">
                {contradictions.length === 0 ? (
                  <div className="card p-8 text-center text-dark-400">No contradictions detected</div>
                ) : contradictions.map(c => (
                  <div key={c.id} className="card p-4">
                    <div className="flex items-start gap-3">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                        c.severity === 'high' ? 'bg-red-500/10' : c.severity === 'medium' ? 'bg-amber-500/10' : 'bg-yellow-500/10'
                      }`}>
                        <AlertTriangle className={`w-4 h-4 ${
                          c.severity === 'high' ? 'text-red-400' : c.severity === 'medium' ? 'text-amber-400' : 'text-yellow-400'
                        }`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white">{c.description}</p>
                        <div className="grid grid-cols-2 gap-2 mt-2">
                          <div className="px-2 py-1.5 rounded-lg bg-dark-800/50 border border-dark-700/30">
                            <p className="text-[10px] text-dark-500 uppercase">Evidence A</p>
                            <p className="text-[11px] text-dark-300">{c.evidence_a}</p>
                          </div>
                          <div className="px-2 py-1.5 rounded-lg bg-dark-800/50 border border-dark-700/30">
                            <p className="text-[10px] text-dark-500 uppercase">Evidence B</p>
                            <p className="text-[11px] text-dark-300">{c.evidence_b}</p>
                          </div>
                        </div>
                        {c.resolution_suggestion && (
                          <p className="text-[11px] text-emerald-400 mt-2 flex items-center gap-1">
                            <Zap className="w-3 h-3" /> {c.resolution_suggestion}
                          </p>
                        )}
                      </div>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium shrink-0 ${
                        c.severity === 'high' ? 'bg-red-500/20 text-red-400' : c.severity === 'medium' ? 'bg-amber-500/20 text-amber-400' : 'bg-yellow-500/20 text-yellow-400'
                      }`}>{c.severity}</span>
                    </div>
                  </div>
                ))}
              </motion.div>
            )}

            {activeTab === 'confidence' && (
              <motion.div key="confidence" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                {!confidenceDashboard ? (
                  <div className="card p-8 text-center text-dark-400">Confidence dashboard not available yet</div>
                ) : (
                  <div className="card p-4 space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {[
                        { label: 'Overall Confidence', value: confidenceDashboard.overall_confidence, color: 'purple' },
                        { label: 'Evidence Strength', value: confidenceDashboard.evidence_strength, color: 'emerald' },
                        { label: 'Hypothesis Coverage', value: confidenceDashboard.hypothesis_coverage, color: 'blue' },
                        { label: 'Contradiction Risk', value: 1 - confidenceDashboard.contradiction_severity, color: 'amber' },
                      ].map(m => (
                        <div key={m.label} className="text-center p-3 rounded-xl bg-dark-800/50 border border-dark-700/30">
                          <p className={`text-2xl font-bold ${
                            m.value >= 0.7 ? 'text-emerald-400' : m.value >= 0.4 ? 'text-amber-400' : 'text-red-400'
                          }`}>{(m.value * 100).toFixed(0)}%</p>
                          <p className="text-[10px] text-dark-400 uppercase mt-1">{m.label}</p>
                        </div>
                      ))}
                    </div>
                    {confidenceDashboard.recommendations?.length > 0 && (
                      <div>
                        <p className="text-xs text-dark-400 mb-2">Recommendations</p>
                        <ul className="space-y-1.5">
                          {confidenceDashboard.recommendations.map((r, i) => (
                            <li key={i} className="text-[11px] text-dark-300 flex items-start gap-2">
                              <ChevronRight className="w-3 h-3 text-purple-400 mt-0.5 shrink-0" /> {r}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            )}

            {activeTab === 'report' && (
              <motion.div key="report" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                {!report ? (
                  <div className="card p-8 text-center text-dark-400">Report will appear after analysis completes</div>
                ) : (
                  <div className="card p-4">
                    <div className="prose prose-invert prose-sm max-w-none text-dark-300">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown>
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}

      {/* Case Discussion Chat */}
      <CaseChat sessionId={sessionId} onSessionCreated={setSessionId} disabled={isInvestigating || isUploading} accentColor="purple" />
    </div>
  )
}
