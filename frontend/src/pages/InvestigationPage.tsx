import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Brain, CheckCircle, Loader2,
  Target, Lightbulb, Scale, AlertTriangle,
} from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../api/client'

interface InvestigationResult {
  recommendations: string[]
  next_steps: string[]
  legal_references: string[]
  risk_assessment: string
}

interface CaseBasic {
  fir_number: string
  title: string | null
  status: string
  complainant_name: string
  offense_type: string | null
  sections_applied: string[] | null
  witnesses: Array<Record<string, unknown>> | null
  accused_persons: Array<Record<string, unknown>> | null
}

export default function InvestigationPage() {
  const { caseId } = useParams()
  const [loading, setLoading] = useState(false)
  const [context, setContext] = useState('')
  const [result, setResult] = useState<InvestigationResult | null>(null)
  const [caseData, setCaseData] = useState<CaseBasic | null>(null)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    api.get(`/api/cases/${caseId}`).then(r => setCaseData(r.data)).catch(() => {})
  }, [caseId])

  const runInvestigation = async () => {
    setLoading(true)
    setProgress(0)
    const interval = setInterval(() => {
      setProgress(prev => Math.min(prev + Math.random() * 15, 90))
    }, 500)
    try {
      const response = await api.post('/api/agents/investigate', {
        case_id: caseId,
        context: context || null,
      })
      setResult(response.data)
      setProgress(100)
      toast.success('Investigation analysis complete')
    } catch {
      toast.error('Investigation analysis failed')
    } finally {
      clearInterval(interval)
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-600/20 rounded-xl flex items-center justify-center">
              <Brain className="w-5 h-5 text-primary-400" />
            </div>
            Investigation Assistant
          </h1>
          <p className="text-dark-400 text-sm mt-1">
            {caseData ? `${caseData.title || caseData.fir_number} — ${caseData.complainant_name}` : `Case ${caseId}`}
          </p>
        </div>
        <Link to={`/cases/${caseId}`} className="btn-secondary text-sm">← Back to Case</Link>
      </div>

      {/* Case Context Cards */}
      {caseData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="rounded-xl bg-dark-900/60 border border-dark-700/50 p-3">
            <p className="text-dark-400 text-[10px] uppercase tracking-wide">Status</p>
            <p className="text-white text-sm font-medium mt-1 capitalize">{caseData.status.replace('_', ' ')}</p>
          </div>
          <div className="rounded-xl bg-dark-900/60 border border-dark-700/50 p-3">
            <p className="text-dark-400 text-[10px] uppercase tracking-wide">Offense</p>
            <p className="text-white text-sm font-medium mt-1">{caseData.offense_type || 'Not specified'}</p>
          </div>
          <div className="rounded-xl bg-dark-900/60 border border-dark-700/50 p-3">
            <p className="text-dark-400 text-[10px] uppercase tracking-wide">Witnesses</p>
            <p className="text-white text-sm font-medium mt-1">{caseData.witnesses?.length || 0}</p>
          </div>
          <div className="rounded-xl bg-dark-900/60 border border-dark-700/50 p-3">
            <p className="text-dark-400 text-[10px] uppercase tracking-wide">Accused</p>
            <p className="text-white text-sm font-medium mt-1">{caseData.accused_persons?.length || 0}</p>
          </div>
        </div>
      )}

      {/* AI Analysis Section */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-gradient-to-br from-primary-500/20 to-purple-500/20 rounded-xl flex items-center justify-center">
            <Brain className="w-5 h-5 text-primary-400" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Case Analysis AI</h2>
            <p className="text-dark-400 text-xs">Analyzes evidence, applicable laws, and recommends investigative steps</p>
          </div>
        </div>
        <textarea
          className="input min-h-[80px] mb-4 text-sm"
          placeholder="Optional: Add context, ask specific questions, or guide the investigation focus..."
          value={context}
          onChange={(e) => setContext(e.target.value)}
        />
        {loading && (
          <div className="mb-4">
            <div className="flex items-center justify-between text-xs text-dark-400 mb-1">
              <span>Analyzing case data...</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="w-full h-1.5 bg-dark-800 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-primary-500 to-purple-500 rounded-full"
                animate={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}
        <button
          onClick={runInvestigation}
          disabled={loading}
          className="btn-primary flex items-center gap-2 disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
          {loading ? 'Analyzing...' : 'Run Investigation Analysis'}
        </button>
      </motion.div>

      {/* Results */}
      {result && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          {/* Recommendations */}
          <div className="card border-l-2 border-l-green-500">
            <h3 className="text-white font-semibold flex items-center gap-2 mb-4">
              <Lightbulb className="w-5 h-5 text-green-400" />
              AI Recommendations
            </h3>
            <div className="space-y-3">
              {result.recommendations.map((rec, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-start gap-3 p-3 bg-dark-900/40 rounded-lg"
                >
                  <div className="w-6 h-6 rounded-full bg-green-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-green-400 text-xs font-bold">{i + 1}</span>
                  </div>
                  <p className="text-dark-200 text-sm">{rec}</p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Next Steps */}
          <div className="card border-l-2 border-l-yellow-500">
            <h3 className="text-white font-semibold flex items-center gap-2 mb-4">
              <Target className="w-5 h-5 text-yellow-400" />
              Immediate Next Steps
            </h3>
            <div className="space-y-2">
              {result.next_steps.map((step, i) => (
                <div key={i} className="flex items-start gap-3 p-2">
                  <CheckCircle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                  <p className="text-dark-300 text-sm">{step}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Legal References */}
          <div className="card border-l-2 border-l-blue-500">
            <h3 className="text-white font-semibold flex items-center gap-2 mb-4">
              <Scale className="w-5 h-5 text-blue-400" />
              Applicable Laws & Sections
            </h3>
            <div className="flex flex-wrap gap-2">
              {result.legal_references.map((ref, i) => (
                <span key={i} className="px-3 py-1.5 bg-blue-500/10 text-blue-400 rounded-lg text-xs font-medium border border-blue-500/20">
                  {ref}
                </span>
              ))}
            </div>
          </div>

          {/* Risk Assessment */}
          <div className="card border-l-2 border-l-red-500">
            <h3 className="text-white font-semibold flex items-center gap-2 mb-3">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              Risk Assessment
            </h3>
            <p className="text-dark-300 text-sm leading-relaxed">{result.risk_assessment}</p>
          </div>
        </motion.div>
      )}
    </div>
  )
}
