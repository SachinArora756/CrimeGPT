import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Brain, CheckCircle, AlertCircle, BookOpen, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../api/client'

interface InvestigationResult {
  recommendations: string[]
  next_steps: string[]
  legal_references: string[]
  risk_assessment: string
}

export default function InvestigationPage() {
  const { caseId } = useParams()
  const [loading, setLoading] = useState(false)
  const [context, setContext] = useState('')
  const [result, setResult] = useState<InvestigationResult | null>(null)

  const runInvestigation = async () => {
    setLoading(true)
    try {
      const response = await api.post('/api/agents/investigate', {
        case_id: Number(caseId),
        context: context || null,
      })
      setResult(response.data)
      toast.success('Investigation analysis complete')
    } catch {
      toast.error('Investigation analysis failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-white">Investigation Assistant — Case #{caseId}</h1>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card"
      >
        <div className="flex items-center gap-3 mb-4">
          <Brain className="w-6 h-6 text-primary-400" />
          <h2 className="text-lg font-semibold text-white">AI Investigation Agent</h2>
        </div>
        <p className="text-dark-400 text-sm mb-4">
          The AI will analyze case details, evidence, and legal provisions to recommend investigative steps.
          You retain full decision-making authority.
        </p>
        <textarea
          className="input min-h-[100px] mb-4"
          placeholder="Optional: Add context or specific questions for the investigation agent..."
          value={context}
          onChange={(e) => setContext(e.target.value)}
        />
        <button
          onClick={runInvestigation}
          disabled={loading}
          className="btn-primary flex items-center gap-2 disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
          {loading ? 'Analyzing...' : 'Run Investigation Analysis'}
        </button>
      </motion.div>

      {result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          <div className="card">
            <h3 className="text-white font-semibold flex items-center gap-2 mb-4">
              <CheckCircle className="w-5 h-5 text-green-400" />
              Recommendations
            </h3>
            <ul className="space-y-2">
              {result.recommendations.map((rec, i) => (
                <li key={i} className="flex items-start gap-3 text-dark-300">
                  <span className="text-primary-400 font-mono text-sm mt-0.5">{i + 1}.</span>
                  {rec}
                </li>
              ))}
            </ul>
          </div>

          <div className="card">
            <h3 className="text-white font-semibold flex items-center gap-2 mb-4">
              <AlertCircle className="w-5 h-5 text-yellow-400" />
              Immediate Next Steps
            </h3>
            <ul className="space-y-2">
              {result.next_steps.map((step, i) => (
                <li key={i} className="flex items-start gap-3 text-dark-300">
                  <span className="w-2 h-2 rounded-full bg-yellow-400 mt-2 flex-shrink-0"></span>
                  {step}
                </li>
              ))}
            </ul>
          </div>

          <div className="card">
            <h3 className="text-white font-semibold flex items-center gap-2 mb-4">
              <BookOpen className="w-5 h-5 text-blue-400" />
              Legal References
            </h3>
            <div className="flex flex-wrap gap-2">
              {result.legal_references.map((ref, i) => (
                <span key={i} className="px-3 py-1.5 bg-blue-500/20 text-blue-400 rounded-lg text-sm border border-blue-500/30">
                  {ref}
                </span>
              ))}
            </div>
          </div>

          <div className="card">
            <h3 className="text-white font-semibold mb-3">Risk Assessment</h3>
            <p className="text-dark-300">{result.risk_assessment}</p>
          </div>
        </motion.div>
      )}
    </div>
  )
}
