import { useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Scale, CheckCircle, XCircle, AlertTriangle, Loader2, BookOpen, Shield,
  ThumbsUp, ThumbsDown, MessageSquare, Send, Sparkles, Gavel, FileWarning,
  ChevronDown, ChevronUp, Zap, Clock, ArrowLeft,
} from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../api/client'

interface SectionRec {
  section: string
  act: string
  title: string
  explanation: string
  supporting_evidence: string[]
  confidence: number
  punishment_range: string
  is_primary: boolean
}

interface Recommendation {
  id: number
  case_id: number
  recommendations: SectionRec[]
  procedural_notes: string[]
  evidence_gaps: string[]
  overall_confidence: number
  status: string
  approved_sections: string[] | null
  officer_notes: string | null
  created_at: string
}

interface LegalChatMsg {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

function ConfidenceRing({ value, size = 80 }: { value: number; size?: number }) {
  const percentage = Math.round(value * 100)
  const radius = (size - 8) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (value * circumference)
  const color = percentage >= 80 ? '#10b981' : percentage >= 60 ? '#f59e0b' : '#ef4444'

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="currentColor" strokeWidth="6"
          className="text-dark-800"
        />
        <motion.circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke={color} strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-lg font-bold text-white">{percentage}%</span>
      </div>
    </div>
  )
}

function ConfidenceBar({ value }: { value: number }) {
  const percentage = Math.round(value * 100)
  const color = percentage >= 80 ? 'from-green-500 to-emerald-400' : percentage >= 60 ? 'from-yellow-500 to-amber-400' : 'from-red-500 to-orange-400'

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-dark-800 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full bg-gradient-to-r ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        />
      </div>
      <span className="text-xs font-semibold text-dark-300 w-9 text-right">{percentage}%</span>
    </div>
  )
}

export default function LegalRecommendationsPage() {
  const { caseId } = useParams()
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [approving, setApproving] = useState(false)
  const [selectedSections, setSelectedSections] = useState<string[]>([])
  const [notes, setNotes] = useState('')
  const [chatMessages, setChatMessages] = useState<LegalChatMsg[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [expandedCharge, setExpandedCharge] = useState<number | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => { fetchRecommendation(); loadChatHistory() }, [caseId])
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [chatMessages])

  const fetchRecommendation = async () => {
    try {
      const res = await api.get(`/api/legal/recommend/${caseId}`)
      setRecommendation(res.data)
      if (res.data?.approved_sections) {
        setSelectedSections(res.data.approved_sections)
      }
    } catch {
      setRecommendation(null)
    } finally {
      setLoading(false)
    }
  }

  const loadChatHistory = async () => {
    try {
      const res = await api.get(`/api/legal/recommend/${caseId}/chat`)
      setChatMessages(res.data)
    } catch {
      setChatMessages([])
    }
  }

  const sendChatMessage = async () => {
    if (!chatInput.trim() || chatLoading) return
    const msg = chatInput.trim()
    setChatInput('')
    setChatMessages(prev => [...prev, { id: Date.now(), role: 'user', content: msg, created_at: new Date().toISOString() }])
    setChatLoading(true)
    try {
      const res = await api.post(`/api/legal/recommend/${caseId}/chat`, { message: msg })
      setChatMessages(prev => [...prev, res.data])
    } catch {
      setChatMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', content: 'Failed to get a response. Please try again.', created_at: new Date().toISOString() }])
    } finally {
      setChatLoading(false)
    }
  }

  const generateRecommendation = async () => {
    setGenerating(true)
    try {
      const res = await api.post(`/api/legal/recommend/${caseId}`, { focus_area: null })
      setRecommendation(res.data)
      toast.success('Legal recommendations generated')
    } catch {
      toast.error('Failed to generate recommendations')
    } finally {
      setGenerating(false)
    }
  }

  const handleApproval = async (status: 'approved' | 'partially_approved' | 'rejected') => {
    setApproving(true)
    try {
      const sections = status === 'approved'
        ? recommendation!.recommendations.map(r => r.section)
        : status === 'rejected'
        ? []
        : selectedSections
      await api.put(`/api/legal/recommend/${caseId}/approve`, {
        approved_sections: sections,
        notes: notes || null,
      })
      toast.success(`Recommendation ${status.replace('_', ' ')}`)
      fetchRecommendation()
    } catch {
      toast.error('Failed to update recommendation')
    } finally {
      setApproving(false)
    }
  }

  const toggleSection = (section: string) => {
    setSelectedSections(prev =>
      prev.includes(section) ? prev.filter(s => s !== section) : [...prev, section]
    )
  }

  const primaryCharges = recommendation?.recommendations.filter(r => r.is_primary) ?? []
  const alternativeCharges = recommendation?.recommendations.filter(r => !r.is_primary) ?? []

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-32 rounded-2xl animate-pulse bg-dark-800/50" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map(i => <div key={i} className="h-24 rounded-xl animate-pulse bg-dark-800/50" />)}
        </div>
        <div className="h-64 rounded-2xl animate-pulse bg-dark-800/50" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Hero Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl bg-dark-900/80 border border-dark-700 p-6"
      >
        <div className="absolute inset-0 bg-gradient-to-r from-indigo-600/10 via-purple-600/5 to-transparent" />
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/4" />

        <div className="relative flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Scale className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Legal AI Assistant</h1>
              <p className="text-dark-400 text-sm mt-0.5 flex items-center gap-2">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                RAG-powered section analysis for Case #{caseId}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link to={`/cases/${caseId}`} className="btn-secondary flex items-center gap-2 text-sm">
              <ArrowLeft className="w-4 h-4" /> Back
            </Link>
            <button
              onClick={generateRecommendation}
              disabled={generating}
              className="relative flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-sm font-medium transition-all disabled:opacity-50 shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30"
            >
              {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              {generating ? 'Analyzing...' : recommendation ? 'Regenerate' : 'Generate Analysis'}
            </button>
          </div>
        </div>
      </motion.div>

      {!recommendation ? (
        /* Empty State */
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="relative overflow-hidden rounded-2xl bg-dark-900/60 border border-dark-700/50 text-center py-20"
        >
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-indigo-600/5 via-transparent to-transparent" />
          <div className="relative">
            <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto mb-6">
              <Gavel className="w-12 h-12 text-indigo-400/60" />
            </div>
            <h2 className="text-white text-xl font-bold mb-2">No Legal Analysis Yet</h2>
            <p className="text-dark-400 text-sm mb-8 max-w-md mx-auto">
              Generate AI-powered legal recommendations using our RAG pipeline trained on BNS, CrPC, and special acts.
            </p>
            <button
              onClick={generateRecommendation}
              disabled={generating}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl font-medium transition-all disabled:opacity-50 shadow-lg shadow-indigo-500/20"
            >
              {generating ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
              {generating ? 'Analyzing Case...' : 'Generate Legal Analysis'}
            </button>
            <div className="flex items-center justify-center gap-6 mt-8 text-xs text-dark-500">
              <span className="flex items-center gap-1"><Shield className="w-3.5 h-3.5" /> BNS Sections</span>
              <span className="flex items-center gap-1"><BookOpen className="w-3.5 h-3.5" /> Special Acts</span>
              <span className="flex items-center gap-1"><Scale className="w-3.5 h-3.5" /> Precedent Analysis</span>
            </div>
          </div>
        </motion.div>
      ) : (
        <div className="space-y-6">
          {/* Summary Stats */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-2 lg:grid-cols-4 gap-4"
          >
            {/* Confidence Ring */}
            <div className="rounded-2xl bg-dark-900/80 border border-dark-700/50 p-5 flex items-center gap-4">
              <ConfidenceRing value={recommendation.overall_confidence} />
              <div>
                <p className="text-dark-400 text-xs uppercase tracking-wide">Confidence</p>
                <p className="text-white font-semibold mt-0.5">
                  {recommendation.overall_confidence >= 0.8 ? 'High' : recommendation.overall_confidence >= 0.6 ? 'Moderate' : 'Low'}
                </p>
              </div>
            </div>

            {/* Stats Cards */}
            <div className="rounded-2xl bg-dark-900/80 border border-dark-700/50 p-5">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-lg bg-green-500/10 flex items-center justify-center">
                  <Shield className="w-4 h-4 text-green-400" />
                </div>
                <span className="text-dark-400 text-xs">Primary</span>
              </div>
              <p className="text-2xl font-bold text-white">{primaryCharges.length}</p>
              <p className="text-dark-500 text-xs mt-0.5">charges identified</p>
            </div>

            <div className="rounded-2xl bg-dark-900/80 border border-dark-700/50 p-5">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-lg bg-yellow-500/10 flex items-center justify-center">
                  <BookOpen className="w-4 h-4 text-yellow-400" />
                </div>
                <span className="text-dark-400 text-xs">Alternative</span>
              </div>
              <p className="text-2xl font-bold text-white">{alternativeCharges.length}</p>
              <p className="text-dark-500 text-xs mt-0.5">possible charges</p>
            </div>

            <div className="rounded-2xl bg-dark-900/80 border border-dark-700/50 p-5">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center">
                  <FileWarning className="w-4 h-4 text-red-400" />
                </div>
                <span className="text-dark-400 text-xs">Gaps</span>
              </div>
              <p className="text-2xl font-bold text-white">{recommendation.evidence_gaps.length}</p>
              <p className="text-dark-500 text-xs mt-0.5">evidence gaps</p>
            </div>
          </motion.div>

          {/* Status Banner */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className={`flex items-center justify-between rounded-xl px-5 py-3 border ${
              recommendation.status === 'approved' ? 'bg-green-500/5 border-green-500/20' :
              recommendation.status === 'rejected' ? 'bg-red-500/5 border-red-500/20' :
              recommendation.status === 'partially_approved' ? 'bg-yellow-500/5 border-yellow-500/20' :
              'bg-indigo-500/5 border-indigo-500/20'
            }`}
          >
            <div className="flex items-center gap-3">
              {recommendation.status === 'approved' && <CheckCircle className="w-5 h-5 text-green-400" />}
              {recommendation.status === 'rejected' && <XCircle className="w-5 h-5 text-red-400" />}
              {recommendation.status === 'partially_approved' && <AlertTriangle className="w-5 h-5 text-yellow-400" />}
              {recommendation.status === 'pending_approval' && <Clock className="w-5 h-5 text-indigo-400" />}
              <span className="text-sm font-medium text-white">
                Status: {recommendation.status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </span>
            </div>
            <span className="text-dark-400 text-xs flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {new Date(recommendation.created_at).toLocaleString()}
            </span>
          </motion.div>

          {/* Primary Charges */}
          {primaryCharges.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="rounded-2xl bg-dark-900/80 border border-dark-700/50 overflow-hidden"
            >
              <div className="px-6 py-4 border-b border-dark-700/50 bg-gradient-to-r from-green-500/5 to-transparent">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-green-500/10 flex items-center justify-center">
                    <Shield className="w-4 h-4 text-green-400" />
                  </div>
                  Primary Charges
                  <span className="ml-2 px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 text-xs font-medium">
                    {primaryCharges.length}
                  </span>
                </h3>
              </div>
              <div className="p-4 space-y-3">
                {primaryCharges.map((charge, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -5 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 + i * 0.05 }}
                    className={`rounded-xl border transition-all ${
                      selectedSections.includes(charge.section)
                        ? 'bg-green-500/5 border-green-500/30'
                        : 'bg-dark-800/40 border-dark-700/50 hover:border-dark-600'
                    }`}
                  >
                    <div className="p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-3 flex-1">
                          <button
                            onClick={() => toggleSection(charge.section)}
                            className={`w-5 h-5 rounded-md border flex-shrink-0 mt-0.5 flex items-center justify-center transition-all ${
                              selectedSections.includes(charge.section)
                                ? 'bg-green-500 border-green-500 shadow-sm shadow-green-500/30'
                                : 'border-dark-600 hover:border-green-400'
                            }`}
                          >
                            {selectedSections.includes(charge.section) && <CheckCircle className="w-3.5 h-3.5 text-white" />}
                          </button>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-400 text-xs font-mono font-medium">
                                {charge.section}
                              </span>
                              <span className="text-dark-400 text-xs">{charge.act}</span>
                            </div>
                            <p className="text-white font-medium text-sm mt-1.5">{charge.title}</p>
                            <div className="mt-2">
                              <ConfidenceBar value={charge.confidence} />
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={() => setExpandedCharge(expandedCharge === i ? null : i)}
                          className="p-1.5 rounded-lg text-dark-400 hover:text-white hover:bg-dark-700 transition-colors"
                        >
                          {expandedCharge === i ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </button>
                      </div>

                      <AnimatePresence>
                        {expandedCharge === i && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="overflow-hidden"
                          >
                            <div className="mt-3 ml-8 space-y-3 pt-3 border-t border-dark-700/50">
                              {charge.explanation && (
                                <div>
                                  <p className="text-dark-500 text-[10px] uppercase tracking-wide mb-1">Explanation</p>
                                  <p className="text-dark-300 text-xs leading-relaxed">{charge.explanation}</p>
                                </div>
                              )}
                              {charge.punishment_range && (
                                <div>
                                  <p className="text-dark-500 text-[10px] uppercase tracking-wide mb-1">Punishment Range</p>
                                  <p className="text-dark-300 text-xs flex items-center gap-1.5">
                                    <Gavel className="w-3 h-3 text-orange-400" />
                                    {charge.punishment_range}
                                  </p>
                                </div>
                              )}
                              {charge.supporting_evidence.length > 0 && (
                                <div>
                                  <p className="text-dark-500 text-[10px] uppercase tracking-wide mb-1.5">Supporting Evidence</p>
                                  <div className="flex flex-wrap gap-1.5">
                                    {charge.supporting_evidence.map((ref, j) => (
                                      <span key={j} className="px-2 py-1 bg-dark-800 text-dark-300 rounded-lg text-[11px] border border-dark-700/50">
                                        {ref}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Alternative Charges */}
          {alternativeCharges.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="rounded-2xl bg-dark-900/80 border border-dark-700/50 overflow-hidden"
            >
              <div className="px-6 py-4 border-b border-dark-700/50 bg-gradient-to-r from-yellow-500/5 to-transparent">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-yellow-500/10 flex items-center justify-center">
                    <BookOpen className="w-4 h-4 text-yellow-400" />
                  </div>
                  Alternative Charges
                  <span className="ml-2 px-2 py-0.5 rounded-full bg-yellow-500/10 text-yellow-400 text-xs font-medium">
                    {alternativeCharges.length}
                  </span>
                </h3>
              </div>
              <div className="p-4 space-y-2">
                {alternativeCharges.map((charge, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -5 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 + i * 0.04 }}
                    className={`flex items-center justify-between p-3.5 rounded-xl border transition-all ${
                      selectedSections.includes(charge.section)
                        ? 'bg-yellow-500/5 border-yellow-500/30'
                        : 'bg-dark-800/40 border-dark-700/50 hover:border-dark-600'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => toggleSection(charge.section)}
                        className={`w-5 h-5 rounded-md border flex-shrink-0 flex items-center justify-center transition-all ${
                          selectedSections.includes(charge.section)
                            ? 'bg-yellow-500 border-yellow-500 shadow-sm shadow-yellow-500/30'
                            : 'border-dark-600 hover:border-yellow-400'
                        }`}
                      >
                        {selectedSections.includes(charge.section) && <CheckCircle className="w-3.5 h-3.5 text-white" />}
                      </button>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded-md bg-dark-700 text-dark-300 text-xs font-mono font-medium">
                            {charge.section}
                          </span>
                          <span className="text-dark-500 text-xs">{charge.act}</span>
                        </div>
                        <p className="text-dark-200 text-sm mt-1">{charge.title}</p>
                      </div>
                    </div>
                    <div className="w-24">
                      <ConfidenceBar value={charge.confidence} />
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Evidence Gaps & Procedural Notes Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Evidence Gaps */}
            {recommendation.evidence_gaps.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="rounded-2xl bg-dark-900/80 border border-dark-700/50 overflow-hidden"
              >
                <div className="px-5 py-3.5 border-b border-dark-700/50 bg-gradient-to-r from-red-500/5 to-transparent">
                  <h3 className="text-white font-semibold text-sm flex items-center gap-2">
                    <div className="w-6 h-6 rounded-lg bg-red-500/10 flex items-center justify-center">
                      <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
                    </div>
                    Evidence Gaps
                  </h3>
                </div>
                <div className="p-4 space-y-2">
                  {recommendation.evidence_gaps.map((gap, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.3 + i * 0.05 }}
                      className="flex items-start gap-2.5 p-3 bg-red-500/5 rounded-xl border border-red-500/10"
                    >
                      <XCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                      <p className="text-dark-300 text-sm leading-relaxed">{gap}</p>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Procedural Notes */}
            {recommendation.procedural_notes.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="rounded-2xl bg-dark-900/80 border border-dark-700/50 overflow-hidden"
              >
                <div className="px-5 py-3.5 border-b border-dark-700/50 bg-gradient-to-r from-blue-500/5 to-transparent">
                  <h3 className="text-white font-semibold text-sm flex items-center gap-2">
                    <div className="w-6 h-6 rounded-lg bg-blue-500/10 flex items-center justify-center">
                      <BookOpen className="w-3.5 h-3.5 text-blue-400" />
                    </div>
                    Procedural Notes
                  </h3>
                </div>
                <div className="p-4 space-y-2">
                  {recommendation.procedural_notes.map((note, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.4 + i * 0.05 }}
                      className="flex items-start gap-2.5 p-3 bg-blue-500/5 rounded-xl border border-blue-500/10"
                    >
                      <CheckCircle className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                      <p className="text-dark-300 text-sm leading-relaxed">{note}</p>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}
          </div>

          {/* Approval Section */}
          {recommendation.status === 'pending_approval' && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="rounded-2xl bg-dark-900/80 border border-indigo-500/20 overflow-hidden"
            >
              <div className="px-6 py-4 border-b border-dark-700/50 bg-gradient-to-r from-indigo-500/5 to-transparent">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  <Gavel className="w-5 h-5 text-indigo-400" />
                  Officer Review & Decision
                </h3>
                <p className="text-dark-400 text-xs mt-1">Select sections to approve or reject the analysis</p>
              </div>
              <div className="p-6">
                <textarea
                  className="w-full bg-dark-800/60 border border-dark-700 rounded-xl px-4 py-3 text-sm text-dark-200 placeholder:text-dark-500 resize-none focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20 transition-all min-h-[80px]"
                  placeholder="Add notes about your decision (optional)..."
                  value={notes}
                  onChange={e => setNotes(e.target.value)}
                />
                <div className="flex flex-wrap gap-3 mt-4">
                  <button
                    onClick={() => handleApproval('approved')}
                    disabled={approving}
                    className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white rounded-xl text-sm font-medium transition-all disabled:opacity-50 shadow-lg shadow-green-500/10"
                  >
                    <ThumbsUp className="w-4 h-4" />
                    Approve All
                  </button>
                  <button
                    onClick={() => handleApproval('partially_approved')}
                    disabled={approving || selectedSections.length === 0}
                    className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-yellow-600 to-amber-600 hover:from-yellow-500 hover:to-amber-500 text-white rounded-xl text-sm font-medium transition-all disabled:opacity-50 shadow-lg shadow-yellow-500/10"
                  >
                    <CheckCircle className="w-4 h-4" />
                    Approve Selected ({selectedSections.length})
                  </button>
                  <button
                    onClick={() => handleApproval('rejected')}
                    disabled={approving}
                    className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white rounded-xl text-sm font-medium transition-all disabled:opacity-50 shadow-lg shadow-red-500/10"
                  >
                    <ThumbsDown className="w-4 h-4" />
                    Reject
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          {/* Chat Section */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="rounded-2xl bg-dark-900/80 border border-dark-700/50 overflow-hidden"
          >
            <div className="px-6 py-4 border-b border-dark-700/50 bg-gradient-to-r from-indigo-500/5 to-transparent">
              <h3 className="text-white font-semibold flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-indigo-500/10 flex items-center justify-center">
                  <MessageSquare className="w-4 h-4 text-indigo-400" />
                </div>
                Ask Follow-up Questions
              </h3>
              <p className="text-dark-400 text-xs mt-1">Ask about evidence gaps, applicable precedents, or next investigation steps</p>
            </div>

            {/* Chat Messages */}
            <div className="p-4 space-y-3 max-h-[420px] overflow-y-auto">
              {chatMessages.length === 0 && !chatLoading && (
                <div className="text-center py-10">
                  <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto mb-4">
                    <MessageSquare className="w-8 h-8 text-indigo-400/50" />
                  </div>
                  <p className="text-dark-400 text-sm mb-4">Start a conversation with the Legal AI</p>
                  <div className="flex flex-wrap gap-2 justify-center max-w-lg mx-auto">
                    {[
                      'What evidence do I need to strengthen this case?',
                      'Explain the primary charges in simple terms',
                      'What are the next investigation steps?',
                      'Are there any bail implications?',
                    ].map((q) => (
                      <button
                        key={q}
                        onClick={() => setChatInput(q)}
                        className="px-3 py-2 bg-dark-800/60 hover:bg-dark-700 text-dark-300 text-xs rounded-xl transition-all border border-dark-700/50 hover:border-indigo-500/30 hover:text-indigo-300"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {chatMessages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-r from-indigo-600/20 to-purple-600/20 text-indigo-100 border border-indigo-500/20'
                      : 'bg-dark-800/80 text-dark-200 border border-dark-700/50'
                  }`}>
                    {msg.role === 'assistant' && (
                      <div className="flex items-center gap-1.5 mb-1.5">
                        <Scale className="w-3 h-3 text-indigo-400" />
                        <span className="text-[10px] text-indigo-400 font-medium">Legal AI</span>
                      </div>
                    )}
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    <p className="text-[10px] text-dark-500 mt-2">{new Date(msg.created_at).toLocaleTimeString()}</p>
                  </div>
                </motion.div>
              ))}

              {chatLoading && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                  <div className="bg-dark-800/80 border border-dark-700/50 rounded-2xl px-4 py-3 flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" />
                      <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }} />
                      <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }} />
                    </div>
                    <span className="text-dark-400 text-xs">Analyzing...</span>
                  </div>
                </motion.div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Chat Input */}
            <div className="px-4 pb-4">
              <div className="flex gap-2 p-1.5 bg-dark-800/60 rounded-xl border border-dark-700/50 focus-within:border-indigo-500/30 transition-colors">
                <input
                  type="text"
                  className="flex-1 bg-transparent px-3 py-2 text-sm text-white placeholder:text-dark-500 outline-none"
                  placeholder="Ask about recommendations, evidence, next steps..."
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMessage() } }}
                  disabled={chatLoading}
                />
                <button
                  onClick={sendChatMessage}
                  disabled={chatLoading || !chatInput.trim()}
                  className="flex items-center justify-center w-10 h-10 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 rounded-lg text-white transition-all disabled:opacity-30 disabled:hover:from-indigo-600 disabled:hover:to-purple-600"
                >
                  {chatLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
