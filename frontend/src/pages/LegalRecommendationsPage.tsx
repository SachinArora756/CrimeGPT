import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Scale, CheckCircle, XCircle, AlertTriangle, Loader2, BookOpen, Shield, ThumbsUp, ThumbsDown } from 'lucide-react'
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

export default function LegalRecommendationsPage() {
  const { caseId } = useParams()
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [approving, setApproving] = useState(false)
  const [selectedSections, setSelectedSections] = useState<string[]>([])
  const [notes, setNotes] = useState('')

  useEffect(() => { fetchRecommendation() }, [caseId])

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
      <div className="space-y-4 p-6">
        {[1, 2, 3].map(i => <div key={i} className="rounded-xl animate-pulse h-24 bg-dark-800/50" />)}
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-600/20 rounded-xl flex items-center justify-center">
              <Scale className="w-5 h-5 text-indigo-400" />
            </div>
            Legal Recommendations
          </h1>
          <p className="text-dark-400 text-sm mt-1">AI-powered section analysis for Case #{caseId}</p>
        </div>
        <div className="flex gap-2">
          <Link to={`/cases/${caseId}`} className="btn-secondary text-sm">← Back to Case</Link>
          <button onClick={generateRecommendation} disabled={generating} className="btn-primary flex items-center gap-2 text-sm">
            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Scale className="w-4 h-4" />}
            {generating ? 'Analyzing...' : recommendation ? 'Regenerate' : 'Generate'}
          </button>
        </div>
      </div>

      {!recommendation ? (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card text-center py-16">
          <Scale className="w-16 h-16 text-dark-600 mx-auto mb-4" />
          <h2 className="text-white text-lg font-semibold mb-2">No Recommendations Yet</h2>
          <p className="text-dark-400 text-sm mb-6">Click "Generate" to run AI-powered legal section analysis using RAG</p>
          <button onClick={generateRecommendation} disabled={generating} className="btn-primary mx-auto flex items-center gap-2">
            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Scale className="w-4 h-4" />}
            Generate Recommendations
          </button>
        </motion.div>
      ) : (
        <div className="space-y-6">
          {/* Confidence & Status Header */}
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center">
                  <span className="text-2xl font-bold text-indigo-400">{Math.round(recommendation.overall_confidence * 100)}%</span>
                </div>
                <div>
                  <p className="text-white font-semibold">Overall Confidence</p>
                  <p className="text-dark-400 text-xs mt-0.5">Generated: {new Date(recommendation.created_at).toLocaleString()}</p>
                </div>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                recommendation.status === 'approved' ? 'bg-green-500/10 text-green-400 border border-green-500/30' :
                recommendation.status === 'rejected' ? 'bg-red-500/10 text-red-400 border border-red-500/30' :
                recommendation.status === 'partially_approved' ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30' :
                'bg-blue-500/10 text-blue-400 border border-blue-500/30'
              }`}>
                {recommendation.status.replace('_', ' ').toUpperCase()}
              </span>
            </div>
          </motion.div>

          {/* Primary Charges */}
          {primaryCharges.length > 0 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card border-l-2 border-l-green-500">
              <h3 className="text-white font-semibold flex items-center gap-2 mb-4">
                <Shield className="w-5 h-5 text-green-400" />
                Primary Charges ({primaryCharges.length})
              </h3>
              <div className="space-y-3">
                {primaryCharges.map((charge, i) => (
                  <div key={i} className="p-4 bg-dark-900/40 rounded-xl border border-dark-700/50">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <button
                          onClick={() => toggleSection(charge.section)}
                          className={`w-5 h-5 rounded border flex-shrink-0 mt-0.5 flex items-center justify-center transition-colors ${
                            selectedSections.includes(charge.section)
                              ? 'bg-green-500 border-green-500'
                              : 'border-dark-600 hover:border-green-400'
                          }`}
                        >
                          {selectedSections.includes(charge.section) && <CheckCircle className="w-3.5 h-3.5 text-white" />}
                        </button>
                        <div>
                          <p className="text-white font-medium text-sm">{charge.section} — {charge.act}</p>
                          <p className="text-dark-300 text-xs mt-0.5">{charge.title}</p>
                          {charge.explanation && (
                            <p className="text-dark-400 text-xs mt-1">{charge.explanation}</p>
                          )}
                          {charge.punishment_range && (
                            <p className="text-dark-500 text-xs mt-1">Punishment: {charge.punishment_range}</p>
                          )}
                        </div>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        charge.confidence >= 0.8 ? 'text-green-400 bg-green-500/10' :
                        charge.confidence >= 0.5 ? 'text-yellow-400 bg-yellow-500/10' :
                        'text-red-400 bg-red-500/10'
                      }`}>
                        {Math.round(charge.confidence * 100)}%
                      </span>
                    </div>
                    {charge.supporting_evidence.length > 0 && (
                      <div className="mt-2 ml-8 flex flex-wrap gap-1.5">
                        {charge.supporting_evidence.map((ref, j) => (
                          <span key={j} className="px-2 py-0.5 bg-dark-800 text-dark-300 rounded text-[10px]">{ref}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Alternative Charges */}
          {alternativeCharges.length > 0 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card border-l-2 border-l-yellow-500">
              <h3 className="text-white font-semibold flex items-center gap-2 mb-4">
                <BookOpen className="w-5 h-5 text-yellow-400" />
                Alternative Charges ({alternativeCharges.length})
              </h3>
              <div className="space-y-3">
                {alternativeCharges.map((charge, i) => (
                  <div key={i} className="p-3 bg-dark-900/40 rounded-lg border border-dark-700/50 flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <button
                        onClick={() => toggleSection(charge.section)}
                        className={`w-5 h-5 rounded border flex-shrink-0 mt-0.5 flex items-center justify-center transition-colors ${
                          selectedSections.includes(charge.section)
                            ? 'bg-yellow-500 border-yellow-500'
                            : 'border-dark-600 hover:border-yellow-400'
                        }`}
                      >
                        {selectedSections.includes(charge.section) && <CheckCircle className="w-3.5 h-3.5 text-white" />}
                      </button>
                      <div>
                        <p className="text-white font-medium text-sm">{charge.section} — {charge.act}</p>
                        <p className="text-dark-300 text-xs mt-0.5">{charge.title}</p>
                      </div>
                    </div>
                    <span className="text-dark-400 text-xs">{Math.round(charge.confidence * 100)}%</span>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Evidence Gaps */}
          {recommendation.evidence_gaps.length > 0 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="card border-l-2 border-l-red-500">
              <h3 className="text-white font-semibold flex items-center gap-2 mb-4">
                <AlertTriangle className="w-5 h-5 text-red-400" />
                Evidence Gaps
              </h3>
              <ul className="space-y-2">
                {recommendation.evidence_gaps.map((gap, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-dark-300">
                    <XCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                    {gap}
                  </li>
                ))}
              </ul>
            </motion.div>
          )}

          {/* Procedural Notes */}
          {recommendation.procedural_notes.length > 0 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="card border-l-2 border-l-blue-500">
              <h3 className="text-white font-semibold flex items-center gap-2 mb-4">
                <BookOpen className="w-5 h-5 text-blue-400" />
                Procedural Notes
              </h3>
              <ul className="space-y-2">
                {recommendation.procedural_notes.map((note, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-dark-300">
                    <CheckCircle className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                    {note}
                  </li>
                ))}
              </ul>
            </motion.div>
          )}

          {/* Approval Section */}
          {recommendation.status === 'pending_approval' && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="card">
              <h3 className="text-white font-semibold mb-4">Officer Review</h3>
              <textarea
                className="input min-h-[80px] mb-4 text-sm"
                placeholder="Add notes about your decision (optional)..."
                value={notes}
                onChange={e => setNotes(e.target.value)}
              />
              <div className="flex gap-3">
                <button
                  onClick={() => handleApproval('approved')}
                  disabled={approving}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
                >
                  <ThumbsUp className="w-4 h-4" />
                  Approve All
                </button>
                <button
                  onClick={() => handleApproval('partially_approved')}
                  disabled={approving || selectedSections.length === 0}
                  className="flex items-center gap-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-500 text-white rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
                >
                  <CheckCircle className="w-4 h-4" />
                  Approve Selected ({selectedSections.length})
                </button>
                <button
                  onClick={() => handleApproval('rejected')}
                  disabled={approving}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
                >
                  <ThumbsDown className="w-4 h-4" />
                  Reject
                </button>
              </div>
            </motion.div>
          )}
        </div>
      )}
    </div>
  )
}
