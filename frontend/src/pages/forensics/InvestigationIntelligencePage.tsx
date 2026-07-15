import { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Brain, AlertTriangle, CheckCircle, Clock, Shield,
  ChevronDown, Target, Zap, GitBranch, FileText,
  Network, BarChart3, Lightbulb, RefreshCw,
  Activity, Eye, AlertOctagon, Users, Car,
  Crosshair, CreditCard, Loader2,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import api from '../../api/client'
import { useParams } from 'react-router-dom'

// ─── Types ───────────────────────────────────────────────────────────────────

interface Hypothesis {
  id: number
  title: string
  description: string
  confidence: number
  supporting_evidence: string[]
  conflicting_evidence: string[]
  reasoning: string
  suspects: string[]
  key_factors: string[]
  status: string
  verification_required: boolean
}

interface NextStep {
  action: string
  priority: 'high' | 'medium' | 'low'
  reason: string
  category?: string
}

interface Contradiction {
  id: number
  type: string
  severity: 'high' | 'medium' | 'low'
  description: string
  source_a: string
  source_b: string
  finding_a: string
  finding_b: string
  recommendation: string
}

interface ConfidenceDashboard {
  overall_investigation_confidence: number
  overall_evidence_confidence: number
  category_scores: Record<string, { confidence: number; tools_used: number; status: string }>
  contradiction_penalty: number
  contradictions_count: number
  tools_executed: number
  tools_successful: number
  criminal_matches_found: number
}

interface TimelineEvent {
  order: number
  timestamp: string | null
  type: string
  title: string
  description: string
  source: string
  evidence_id: number
  confidence: number
}

interface GraphNode {
  id: string
  type: 'case' | 'evidence' | 'suspect' | 'vehicle' | 'weapon' | 'license_plate'
  label: string
  data: Record<string, any>
}

interface GraphEdge {
  source: string
  target: string
  type: string
  label: string
  confidence?: number
}

interface ExecutiveSummary {
  report: string
  generated_at: string
  metadata: Record<string, any>
  disclaimer: string
  human_verification_required: boolean
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function InvestigationIntelligencePage() {
  const { caseId } = useParams<{ caseId: string }>()
  const [activeTab, setActiveTab] = useState<'hypotheses' | 'contradictions' | 'timeline' | 'graph' | 'summary'>('hypotheses')
  const [loading, setLoading] = useState(false)

  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([])
  const [nextSteps, setNextSteps] = useState<NextStep[]>([])
  const [contradictions, setContradictions] = useState<Contradiction[]>([])
  const [confidence, setConfidence] = useState<ConfidenceDashboard | null>(null)
  const [timeline, setTimeline] = useState<TimelineEvent[]>([])
  const [graph, setGraph] = useState<{ nodes: GraphNode[]; edges: GraphEdge[]; stats: any } | null>(null)
  const [summary, setSummary] = useState<ExecutiveSummary | null>(null)

  const [expandedHypothesis, setExpandedHypothesis] = useState<number | null>(null)

  useEffect(() => {
    if (caseId) loadTabData()
  }, [caseId, activeTab])

  const loadTabData = async () => {
    if (!caseId) return
    setLoading(true)
    try {
      switch (activeTab) {
        case 'hypotheses': {
          const res = await api.get(`/api/ai-investigation/cases/${caseId}/hypotheses`)
          setHypotheses(res.data.hypotheses || [])
          setNextSteps(res.data.recommended_actions || [])
          break
        }
        case 'contradictions': {
          const res = await api.get(`/api/ai-investigation/cases/${caseId}/contradictions`)
          setContradictions(res.data.contradictions?.contradictions || [])
          setConfidence(res.data.confidence_dashboard || null)
          break
        }
        case 'timeline': {
          const res = await api.get(`/api/ai-investigation/cases/${caseId}/timeline`)
          setTimeline(res.data.events || [])
          break
        }
        case 'graph': {
          const res = await api.get(`/api/ai-investigation/cases/${caseId}/relationship-graph`)
          setGraph(res.data)
          break
        }
        case 'summary': {
          const res = await api.get(`/api/ai-investigation/cases/${caseId}/executive-summary`)
          setSummary(res.data)
          break
        }
      }
    } catch (e) {
      console.error(`Failed to load ${activeTab}`, e)
    } finally {
      setLoading(false)
    }
  }

  const tabs = [
    { key: 'hypotheses', label: 'Hypotheses', icon: Lightbulb },
    { key: 'contradictions', label: 'Contradictions', icon: AlertOctagon },
    { key: 'timeline', label: 'Timeline', icon: Activity },
    { key: 'graph', label: 'Relationship Graph', icon: Network },
    { key: 'summary', label: 'Executive Summary', icon: FileText },
  ] as const

  return (
    <div className="min-h-screen bg-dark-900 p-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-purple-500/20 to-primary-500/20 flex items-center justify-center">
          <Brain className="w-6 h-6 text-purple-400" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-white">Investigation Intelligence</h1>
          <p className="text-sm text-dark-400">Case #{caseId} — Decision Support Engine</p>
        </div>
        <button
          onClick={loadTabData}
          disabled={loading}
          className="ml-auto flex items-center gap-2 px-4 py-2 rounded-xl bg-dark-800 border border-dark-700/50 hover:border-primary-500/30 text-sm text-dark-300 hover:text-white transition-all"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 mb-6 bg-dark-800/50 rounded-xl p-1 border border-dark-700/30">
        {tabs.map(tab => {
          const Icon = tab.icon
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.key
                  ? 'bg-primary-500/10 text-primary-400 border border-primary-500/20'
                  : 'text-dark-400 hover:text-white hover:bg-dark-700/50'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-primary-400 animate-spin" />
        </div>
      ) : (
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'hypotheses' && (
              <HypothesesPanel
                hypotheses={hypotheses}
                nextSteps={nextSteps}
                expanded={expandedHypothesis}
                setExpanded={setExpandedHypothesis}
              />
            )}
            {activeTab === 'contradictions' && (
              <ContradictionsPanel contradictions={contradictions} confidence={confidence} />
            )}
            {activeTab === 'timeline' && (
              <TimelinePanel events={timeline} />
            )}
            {activeTab === 'graph' && (
              <RelationshipGraphPanel graph={graph} />
            )}
            {activeTab === 'summary' && (
              <ExecutiveSummaryPanel summary={summary} />
            )}
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  )
}

// ─── Hypotheses Panel ─────────────────────────────────────────────────────────

function HypothesesPanel({
  hypotheses, nextSteps, expanded, setExpanded,
}: {
  hypotheses: Hypothesis[]
  nextSteps: NextStep[]
  expanded: number | null
  setExpanded: (id: number | null) => void
}) {
  if (!hypotheses.length) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <Lightbulb className="w-12 h-12 text-dark-600 mb-4" />
        <p className="text-dark-400 text-sm">No hypotheses generated yet.</p>
        <p className="text-dark-500 text-xs mt-1">Upload and analyze evidence to generate investigation hypotheses.</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Lightbulb className="w-5 h-5 text-amber-400" />
          <h2 className="text-sm font-semibold text-white">Investigation Hypotheses</h2>
          <span className="ml-2 text-xs text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full">
            AI-Assisted — Requires Verification
          </span>
        </div>

        {hypotheses.map(h => (
          <motion.div
            key={h.id}
            layout
            className="bg-dark-800/50 border border-dark-700/30 rounded-2xl overflow-hidden"
          >
            <button
              onClick={() => setExpanded(expanded === h.id ? null : h.id)}
              className="w-full flex items-center gap-3 p-4 text-left hover:bg-dark-700/20 transition-colors"
            >
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                h.confidence >= 70 ? 'bg-green-500/10' : h.confidence >= 40 ? 'bg-amber-500/10' : 'bg-red-500/10'
              }`}>
                <span className={`text-sm font-bold ${
                  h.confidence >= 70 ? 'text-green-400' : h.confidence >= 40 ? 'text-amber-400' : 'text-red-400'
                }`}>{h.confidence}%</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white">{h.title}</p>
                <p className="text-xs text-dark-400 truncate mt-0.5">{h.description?.slice(0, 100)}</p>
              </div>
              <ChevronDown className={`w-4 h-4 text-dark-500 transition-transform ${expanded === h.id ? 'rotate-180' : ''}`} />
            </button>

            <AnimatePresence>
              {expanded === h.id && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className="px-4 pb-4 space-y-3 border-t border-dark-700/30 pt-3">
                    <div>
                      <p className="text-xs font-medium text-dark-300 mb-1">Reasoning</p>
                      <p className="text-xs text-dark-400">{h.reasoning}</p>
                    </div>
                    {h.supporting_evidence.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-green-400 mb-1">Supporting Evidence</p>
                        <ul className="space-y-1">
                          {h.supporting_evidence.map((e, i) => (
                            <li key={i} className="flex items-start gap-2 text-xs text-dark-300">
                              <CheckCircle className="w-3 h-3 text-green-400 mt-0.5 flex-shrink-0" />
                              {e}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {h.conflicting_evidence.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-red-400 mb-1">Conflicting Evidence</p>
                        <ul className="space-y-1">
                          {h.conflicting_evidence.map((e, i) => (
                            <li key={i} className="flex items-start gap-2 text-xs text-dark-300">
                              <AlertTriangle className="w-3 h-3 text-red-400 mt-0.5 flex-shrink-0" />
                              {e}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {h.suspects.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-purple-400 mb-1">Persons of Interest</p>
                        <div className="flex flex-wrap gap-2">
                          {h.suspects.map((s, i) => (
                            <span key={i} className="px-2 py-1 text-xs bg-purple-500/10 text-purple-300 rounded-lg border border-purple-500/20">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    <div className="mt-2 pt-2 border-t border-dark-700/30">
                      <p className="text-[10px] text-amber-400/80 italic">
                        AI-Assisted Hypothesis — Requires Human Verification. Not an accusation of guilt.
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>

      {/* Next Steps Sidebar */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Zap className="w-5 h-5 text-primary-400" />
          <h2 className="text-sm font-semibold text-white">Recommended Next Steps</h2>
        </div>
        <div className="space-y-2">
          {nextSteps.map((step, i) => (
            <div key={i} className="flex items-start gap-3 p-3 bg-dark-800/50 rounded-xl border border-dark-700/30">
              <div className={`w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0 ${
                step.priority === 'high' ? 'bg-red-500/10' : step.priority === 'medium' ? 'bg-amber-500/10' : 'bg-dark-700'
              }`}>
                <span className={`text-[10px] font-bold ${
                  step.priority === 'high' ? 'text-red-400' : step.priority === 'medium' ? 'text-amber-400' : 'text-dark-400'
                }`}>{i + 1}</span>
              </div>
              <div>
                <p className="text-xs text-white font-medium">{step.action}</p>
                <p className="text-[10px] text-dark-400 mt-0.5">{step.reason}</p>
                {step.category && (
                  <span className="inline-block mt-1 text-[10px] px-1.5 py-0.5 bg-dark-700 text-dark-300 rounded">
                    {step.category}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Contradictions Panel ─────────────────────────────────────────────────────

function ContradictionsPanel({
  contradictions, confidence,
}: {
  contradictions: Contradiction[]
  confidence: ConfidenceDashboard | null
}) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Confidence Dashboard */}
      {confidence && (
        <div className="lg:col-span-3 grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="bg-dark-800/50 rounded-2xl border border-dark-700/30 p-4 text-center">
            <div className="text-2xl font-bold text-primary-400">{confidence.overall_investigation_confidence.toFixed(0)}%</div>
            <p className="text-xs text-dark-400 mt-1">Overall Confidence</p>
          </div>
          <div className="bg-dark-800/50 rounded-2xl border border-dark-700/30 p-4 text-center">
            <div className="text-2xl font-bold text-green-400">{confidence.tools_successful}/{confidence.tools_executed}</div>
            <p className="text-xs text-dark-400 mt-1">Tools Succeeded</p>
          </div>
          <div className="bg-dark-800/50 rounded-2xl border border-dark-700/30 p-4 text-center">
            <div className="text-2xl font-bold text-purple-400">{confidence.criminal_matches_found}</div>
            <p className="text-xs text-dark-400 mt-1">Criminal Matches</p>
          </div>
          <div className="bg-dark-800/50 rounded-2xl border border-dark-700/30 p-4 text-center">
            <div className={`text-2xl font-bold ${confidence.contradiction_penalty > 10 ? 'text-red-400' : 'text-amber-400'}`}>
              -{confidence.contradiction_penalty}%
            </div>
            <p className="text-xs text-dark-400 mt-1">Contradiction Penalty</p>
          </div>
        </div>
      )}

      {/* Category Confidence Scores */}
      {confidence?.category_scores && Object.keys(confidence.category_scores).length > 0 && (
        <div className="lg:col-span-2 bg-dark-800/50 rounded-2xl border border-dark-700/30 p-5">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-5 h-5 text-primary-400" />
            <h3 className="text-sm font-semibold text-white">Confidence by Category</h3>
          </div>
          <div className="space-y-3">
            {Object.entries(confidence.category_scores).map(([key, val]) => (
              <div key={key}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-dark-300 capitalize">{key.replace(/_/g, ' ')}</span>
                  <span className="text-xs text-dark-400">{(val.confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full h-2 bg-dark-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      val.confidence >= 0.8 ? 'bg-green-400' : val.confidence >= 0.5 ? 'bg-amber-400' : 'bg-red-400'
                    }`}
                    style={{ width: `${Math.min(val.confidence * 100, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Contradictions List */}
      <div className={`${confidence?.category_scores && Object.keys(confidence.category_scores).length > 0 ? '' : 'lg:col-span-3'} space-y-3`}>
        <div className="flex items-center gap-2 mb-2">
          <AlertOctagon className="w-5 h-5 text-red-400" />
          <h3 className="text-sm font-semibold text-white">Contradictions</h3>
          {contradictions.length > 0 && (
            <span className="text-xs text-red-400 bg-red-500/10 px-2 py-0.5 rounded-full ml-2">
              {contradictions.length} found
            </span>
          )}
        </div>

        {contradictions.length === 0 ? (
          <div className="flex flex-col items-center py-8 text-center">
            <CheckCircle className="w-10 h-10 text-green-400/50 mb-3" />
            <p className="text-sm text-dark-400">No contradictions detected</p>
          </div>
        ) : (
          contradictions.map(c => (
            <div
              key={c.id}
              className={`p-4 rounded-xl border ${
                c.severity === 'high' ? 'bg-red-500/5 border-red-500/20' :
                c.severity === 'medium' ? 'bg-amber-500/5 border-amber-500/20' :
                'bg-dark-800/50 border-dark-700/30'
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                  c.severity === 'high' ? 'bg-red-500/20 text-red-400' :
                  c.severity === 'medium' ? 'bg-amber-500/20 text-amber-400' :
                  'bg-dark-700 text-dark-400'
                }`}>{c.severity.toUpperCase()}</span>
                <span className="text-[10px] text-dark-500 capitalize">{c.type.replace(/_/g, ' ')}</span>
              </div>
              <p className="text-xs text-white mb-2">{c.description}</p>
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div className="px-2 py-1.5 bg-dark-700/50 rounded-lg">
                  <p className="text-dark-500 mb-0.5">Source A</p>
                  <p className="text-dark-300">{c.finding_a}</p>
                </div>
                <div className="px-2 py-1.5 bg-dark-700/50 rounded-lg">
                  <p className="text-dark-500 mb-0.5">Source B</p>
                  <p className="text-dark-300">{c.finding_b}</p>
                </div>
              </div>
              {c.recommendation && (
                <p className="text-[10px] text-primary-400 mt-2 italic">{c.recommendation}</p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

// ─── Timeline Panel ───────────────────────────────────────────────────────────

function TimelinePanel({ events }: { events: TimelineEvent[] }) {
  if (!events.length) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <Activity className="w-12 h-12 text-dark-600 mb-4" />
        <p className="text-dark-400 text-sm">No timeline events available.</p>
      </div>
    )
  }

  const typeColors: Record<string, string> = {
    evidence_uploaded: 'bg-blue-500/10 text-blue-400',
    photo_captured: 'bg-cyan-500/10 text-cyan-400',
    file_created: 'bg-slate-500/10 text-slate-400',
    file_modified: 'bg-amber-500/10 text-amber-400',
    audio_evidence: 'bg-violet-500/10 text-violet-400',
    suspect_identified: 'bg-red-500/10 text-red-400',
    weapon_found: 'bg-orange-500/10 text-orange-400',
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-primary-400" />
        <h2 className="text-sm font-semibold text-white">Reconstructed Timeline</h2>
        <span className="text-xs text-dark-400 ml-2">{events.length} events</span>
      </div>

      <div className="relative pl-8">
        <div className="absolute left-3 top-0 bottom-0 w-px bg-dark-700/50" />

        {events.map((event, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.03 }}
            className="relative flex items-start gap-4 pb-4"
          >
            <div className={`absolute left-[-20px] w-7 h-7 rounded-full flex items-center justify-center ${typeColors[event.type] || 'bg-dark-700 text-dark-400'}`}>
              <span className="text-[9px] font-bold">{event.order}</span>
            </div>
            <div className="flex-1 bg-dark-800/50 rounded-xl border border-dark-700/30 p-3 ml-4">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-white">{event.title}</span>
                {event.confidence < 1 && (
                  <span className="text-[10px] text-dark-500">{(event.confidence * 100).toFixed(0)}% conf</span>
                )}
              </div>
              <p className="text-[10px] text-dark-400">{event.description}</p>
              {event.timestamp && (
                <p className="text-[10px] text-dark-500 mt-1">
                  <Clock className="w-3 h-3 inline mr-1" />
                  {event.timestamp}
                </p>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

// ─── Relationship Graph Panel ─────────────────────────────────────────────────

function RelationshipGraphPanel({ graph }: { graph: { nodes: GraphNode[]; edges: GraphEdge[]; stats: any } | null }) {
  if (!graph || !graph.nodes.length) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <Network className="w-12 h-12 text-dark-600 mb-4" />
        <p className="text-dark-400 text-sm">No relationship data available.</p>
      </div>
    )
  }

  const nodeTypeConfig: Record<string, { color: string; icon: any }> = {
    case: { color: 'bg-primary-500/20 text-primary-400 border-primary-500/30', icon: Brain },
    evidence: { color: 'bg-blue-500/20 text-blue-400 border-blue-500/30', icon: Eye },
    suspect: { color: 'bg-red-500/20 text-red-400 border-red-500/30', icon: Users },
    vehicle: { color: 'bg-sky-500/20 text-sky-400 border-sky-500/30', icon: Car },
    weapon: { color: 'bg-orange-500/20 text-orange-400 border-orange-500/30', icon: Crosshair },
    license_plate: { color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30', icon: CreditCard },
  }

  const groupedNodes = useMemo(() => {
    const groups: Record<string, GraphNode[]> = {}
    for (const node of graph.nodes) {
      if (!groups[node.type]) groups[node.type] = []
      groups[node.type].push(node)
    }
    return groups
  }, [graph.nodes])

  return (
    <div>
      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
        <div className="bg-dark-800/50 rounded-xl border border-dark-700/30 p-3 text-center">
          <p className="text-lg font-bold text-white">{graph.stats.total_nodes}</p>
          <p className="text-[10px] text-dark-400">Entities</p>
        </div>
        <div className="bg-dark-800/50 rounded-xl border border-dark-700/30 p-3 text-center">
          <p className="text-lg font-bold text-white">{graph.stats.total_edges}</p>
          <p className="text-[10px] text-dark-400">Connections</p>
        </div>
        <div className="bg-dark-800/50 rounded-xl border border-dark-700/30 p-3 text-center">
          <p className="text-lg font-bold text-red-400">{graph.stats.suspects}</p>
          <p className="text-[10px] text-dark-400">Suspects</p>
        </div>
        <div className="bg-dark-800/50 rounded-xl border border-dark-700/30 p-3 text-center">
          <p className="text-lg font-bold text-sky-400">{graph.stats.vehicles}</p>
          <p className="text-[10px] text-dark-400">Vehicles</p>
        </div>
        <div className="bg-dark-800/50 rounded-xl border border-dark-700/30 p-3 text-center">
          <p className="text-lg font-bold text-blue-400">{graph.stats.evidence_items}</p>
          <p className="text-[10px] text-dark-400">Evidence</p>
        </div>
      </div>

      {/* Node Groups */}
      <div className="space-y-6">
        {Object.entries(groupedNodes).map(([type, nodes]) => {
          const config = nodeTypeConfig[type] || { color: 'bg-dark-700 text-dark-400 border-dark-600', icon: Target }
          const Icon = config.icon
          return (
            <div key={type}>
              <div className="flex items-center gap-2 mb-3">
                <Icon className="w-4 h-4" />
                <h3 className="text-xs font-semibold text-white capitalize">{type.replace(/_/g, ' ')}s ({nodes.length})</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {nodes.slice(0, 12).map(node => (
                  <div key={node.id} className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${config.color}`}>
                    <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                    <span className="text-xs truncate">{node.label}</span>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {/* Edge List */}
      {graph.edges.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center gap-2 mb-3">
            <GitBranch className="w-4 h-4 text-primary-400" />
            <h3 className="text-xs font-semibold text-white">Connections ({graph.edges.length})</h3>
          </div>
          <div className="space-y-1 max-h-60 overflow-y-auto">
            {graph.edges.slice(0, 20).map((edge, i) => (
              <div key={i} className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dark-800/50 text-xs">
                <span className="text-dark-300 truncate max-w-[120px]">{edge.source.replace(/^(case_|evidence_|suspect_|vehicle_|weapon_|plate_)/, '')}</span>
                <span className="text-dark-600">→</span>
                <span className="text-primary-400 text-[10px]">{edge.label}</span>
                <span className="text-dark-600">→</span>
                <span className="text-dark-300 truncate max-w-[120px]">{edge.target.replace(/^(case_|evidence_|suspect_|vehicle_|weapon_|plate_)/, '')}</span>
                {edge.confidence != null && (
                  <span className="ml-auto text-[10px] text-dark-500">{(edge.confidence * 100).toFixed(0)}%</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Executive Summary Panel ──────────────────────────────────────────────────

function ExecutiveSummaryPanel({ summary }: { summary: ExecutiveSummary | null }) {
  if (!summary) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <FileText className="w-12 h-12 text-dark-600 mb-4" />
        <p className="text-dark-400 text-sm">Executive summary not yet generated.</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-primary-400" />
          <h2 className="text-sm font-semibold text-white">Executive Investigation Summary</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-dark-500">Generated: {new Date(summary.generated_at).toLocaleString()}</span>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="flex items-start gap-3 p-3 mb-4 bg-amber-500/5 border border-amber-500/20 rounded-xl">
        <Shield className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
        <p className="text-xs text-amber-300">{summary.disclaimer}</p>
      </div>

      {/* Report Content */}
      <div className="bg-dark-800/50 rounded-2xl border border-dark-700/30 p-6">
        <div className="prose prose-invert prose-sm max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{summary.report}</ReactMarkdown>
        </div>
      </div>

      {/* Metadata */}
      {summary.metadata && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
          {summary.metadata.evidence_count != null && (
            <div className="bg-dark-800/50 rounded-xl border border-dark-700/30 p-3 text-center">
              <p className="text-sm font-bold text-white">{summary.metadata.evidence_count}</p>
              <p className="text-[10px] text-dark-400">Evidence Items</p>
            </div>
          )}
          {summary.metadata.execution_count != null && (
            <div className="bg-dark-800/50 rounded-xl border border-dark-700/30 p-3 text-center">
              <p className="text-sm font-bold text-white">{summary.metadata.execution_count}</p>
              <p className="text-[10px] text-dark-400">Analyses Run</p>
            </div>
          )}
          {summary.metadata.hypotheses_count != null && (
            <div className="bg-dark-800/50 rounded-xl border border-dark-700/30 p-3 text-center">
              <p className="text-sm font-bold text-white">{summary.metadata.hypotheses_count}</p>
              <p className="text-[10px] text-dark-400">Hypotheses</p>
            </div>
          )}
          {summary.metadata.overall_confidence != null && (
            <div className="bg-dark-800/50 rounded-xl border border-dark-700/30 p-3 text-center">
              <p className="text-sm font-bold text-primary-400">{summary.metadata.overall_confidence.toFixed(0)}%</p>
              <p className="text-[10px] text-dark-400">Confidence</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
