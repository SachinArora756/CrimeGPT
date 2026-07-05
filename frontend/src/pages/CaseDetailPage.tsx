import { useEffect, useState } from 'react'
import { useParams, Link, useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  FileText, Upload, Brain, BookOpen, Calendar, User, Shield,
  Clock, MessageSquare, CheckCircle, Send, AlertTriangle, TrendingUp,
  Eye, BarChart3, Users, Zap, Pencil, Check, X,
} from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../api/client'

interface CaseDetail {
  id: number
  public_id: string
  fir_number: string
  title: string | null
  complainant_name: string
  complainant_contact: string | null
  complainant_address: string | null
  accused_name: string | null
  incident_date: string | null
  incident_time: string | null
  incident_location: string | null
  description: string
  status: string
  priority: string | null
  assigned_officer_id: number | null
  created_by_id: number | null
  sections_applied: string[] | null
  offense_type: string | null
  station_id: string | null
  victims: Array<Record<string, unknown>> | null
  accused_persons: Array<Record<string, unknown>> | null
  witnesses: Array<Record<string, unknown>> | null
  investigation_team: Array<Record<string, unknown>> | null
  ai_confidence: number | null
  risk_score: number | null
  created_at: string
  updated_at: string
}

interface TimelineEvent {
  id: number
  event_type: string
  title: string
  description: string | null
  created_at: string
}

interface ChatMsg {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

interface CompletenessItem {
  key: string
  label: string
  completed: boolean
  weight: number
}

type Tab = 'overview' | 'timeline' | 'ai' | 'completeness'

export default function CaseDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const basePath = location.pathname.startsWith('/admin') ? '/admin' : ''
  const [caseData, setCaseData] = useState<CaseDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [timeline, setTimeline] = useState<TimelineEvent[]>([])
  const [chatMessages, setChatMessages] = useState<ChatMsg[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [completeness, setCompleteness] = useState<{ percentage: number; items: CompletenessItem[] } | null>(null)
  const [evidenceCount, setEvidenceCount] = useState(0)
  const [docCount, setDocCount] = useState(0)
  const [editingTitle, setEditingTitle] = useState(false)
  const [titleDraft, setTitleDraft] = useState('')
  const [savingTitle, setSavingTitle] = useState(false)

  const saveTitle = async () => {
    if (!titleDraft.trim() || !caseData) return
    setSavingTitle(true)
    try {
      await api.put(`/api/cases/${id}`, { title: titleDraft.trim() })
      setCaseData({ ...caseData, title: titleDraft.trim() })
      setEditingTitle(false)
      toast.success('Case title updated')
    } catch {
      toast.error('Failed to update title')
    } finally {
      setSavingTitle(false)
    }
  }

  useEffect(() => { loadCase() }, [id])

  useEffect(() => {
    if (!id) return
    if (activeTab === 'timeline') loadTimeline()
    if (activeTab === 'ai') loadChatHistory()
    if (activeTab === 'completeness') loadCompleteness()
  }, [activeTab, id])

  const loadCase = async () => {
    try {
      const [caseRes, evRes, docRes] = await Promise.all([
        api.get(`/api/cases/${id}`),
        api.get(`/api/evidence/case/${id}`).catch(() => ({ data: { evidence: [] } })),
        api.get(`/api/documents/case/${id}`).catch(() => ({ data: [] })),
      ])
      setCaseData(caseRes.data)
      setEvidenceCount(evRes.data.evidence?.length || 0)
      setDocCount(Array.isArray(docRes.data) ? docRes.data.length : 0)
    } catch { setCaseData(null) }
    finally { setLoading(false) }
  }

  const loadTimeline = async () => {
    try { const res = await api.get(`/api/timeline/${id}`); setTimeline(res.data) } catch {}
  }

  const loadChatHistory = async () => {
    try { const res = await api.get(`/api/chat/${id}/history`); setChatMessages(res.data) } catch {}
  }

  const loadCompleteness = async () => {
    try { const res = await api.get(`/api/cases/${id}/completeness`); setCompleteness(res.data) } catch {}
  }

  const sendChat = async () => {
    if (!chatInput.trim() || chatLoading) return
    const msg = chatInput.trim()
    setChatInput('')
    setChatMessages((prev) => [...prev, { id: Date.now(), role: 'user', content: msg, created_at: new Date().toISOString() }])
    setChatLoading(true)
    try {
      const res = await api.post(`/api/chat/${id}`, { message: msg })
      setChatMessages((prev) => [...prev, res.data])
    } catch {
      setChatMessages((prev) => [...prev, { id: Date.now() + 1, role: 'assistant', content: 'Error processing request.', created_at: new Date().toISOString() }])
    } finally { setChatLoading(false) }
  }

  if (loading) return (
    <div className="space-y-4">
      <div className="card animate-pulse h-32 bg-dark-800/50" />
      <div className="grid grid-cols-4 gap-4">
        {[1,2,3,4].map(i => <div key={i} className="card animate-pulse h-20 bg-dark-800/50" />)}
      </div>
    </div>
  )
  if (!caseData) return (
    <div className="flex flex-col items-center justify-center h-64 gap-4">
      <Shield className="w-12 h-12 text-red-400" />
      <p className="text-dark-400 text-lg">Case not found or access denied</p>
      <Link to="/cases" className="btn-secondary">Back to Cases</Link>
    </div>
  )

  const statusColors: Record<string, { bg: string; text: string; border: string }> = {
    registered: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/30' },
    investigating: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/30' },
    chargesheet_filed: { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/30' },
    closed: { bg: 'bg-dark-500/10', text: 'text-dark-300', border: 'border-dark-500/30' },
  }
  const sc = statusColors[caseData.status] || statusColors.registered

  const aiConfidence = caseData.ai_confidence ?? 0
  const riskScore = caseData.risk_score ?? 0

  const tabs: { key: Tab; label: string; icon: typeof Clock }[] = [
    { key: 'overview', label: 'Overview', icon: BookOpen },
    { key: 'timeline', label: 'Timeline', icon: Clock },
    { key: 'ai', label: 'Ask CrimeGPT', icon: MessageSquare },
    { key: 'completeness', label: 'Progress', icon: CheckCircle },
  ]

  return (
    <div className="space-y-6">
      {/* Case Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="relative overflow-hidden rounded-2xl bg-dark-900/80 border border-dark-700 p-6">
        <div className="absolute inset-0 bg-gradient-to-r from-primary-600/5 via-transparent to-transparent" />
        <div className="relative flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              {editingTitle ? (
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={titleDraft}
                    onChange={e => setTitleDraft(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') saveTitle(); if (e.key === 'Escape') setEditingTitle(false) }}
                    className="bg-dark-800 border border-primary-500/50 rounded-lg px-3 py-1.5 text-lg font-bold text-white outline-none focus:ring-1 focus:ring-primary-500/30 w-72"
                    autoFocus
                    disabled={savingTitle}
                  />
                  <button onClick={saveTitle} disabled={savingTitle} className="p-1.5 rounded-lg bg-green-500/10 text-green-400 hover:bg-green-500/20 transition-colors">
                    <Check className="w-4 h-4" />
                  </button>
                  <button onClick={() => setEditingTitle(false)} className="p-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2 group/title">
                  <h1 className="text-xl font-bold text-white">{caseData.title || `Case: ${caseData.fir_number}`}</h1>
                  <button
                    onClick={() => { setTitleDraft(caseData.title || ''); setEditingTitle(true) }}
                    className="p-1.5 rounded-lg text-dark-500 hover:text-primary-400 hover:bg-primary-500/10 transition-all opacity-0 group-hover/title:opacity-100"
                    title="Edit case title"
                  >
                    <Pencil className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${sc.bg} ${sc.text} ${sc.border}`}>
                {caseData.status.replace('_', ' ').toUpperCase()}
              </span>
              {caseData.priority && (
                <span className={`px-2 py-0.5 rounded text-xs font-semibold uppercase ${
                  caseData.priority === 'critical' ? 'bg-red-500/10 text-red-400 border border-red-500/30' :
                  caseData.priority === 'high' ? 'bg-orange-500/10 text-orange-400 border border-orange-500/30' :
                  'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30'
                }`}>
                  {caseData.priority}
                </span>
              )}
            </div>
            <div className="flex items-center gap-4 text-sm text-dark-400">
              <span>FIR: {caseData.fir_number}</span>
              {caseData.offense_type && <span>• {caseData.offense_type}</span>}
              {caseData.station_id && <span>• Station: {caseData.station_id}</span>}
            </div>
            <div className="flex items-center gap-4 mt-2 text-xs text-dark-500">
              <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> Created: {new Date(caseData.created_at).toLocaleDateString()}</span>
              <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> Updated: {new Date(caseData.updated_at).toLocaleDateString()}</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link to={`${basePath}/evidence/${id}`} className="btn-secondary flex items-center gap-1.5 text-xs px-3 py-2">
              <Upload className="w-3.5 h-3.5" /> Evidence
            </Link>
            <Link to={`${basePath}/documents/${id}`} className="btn-secondary flex items-center gap-1.5 text-xs px-3 py-2">
              <FileText className="w-3.5 h-3.5" /> Documents
            </Link>
            <Link to={`${basePath}/diary/${id}`} className="btn-secondary flex items-center gap-1.5 text-xs px-3 py-2">
              <BookOpen className="w-3.5 h-3.5" /> Diary
            </Link>
            <Link to={`${basePath}/legal/${id}`} className="btn-secondary flex items-center gap-1.5 text-xs px-3 py-2">
              <BarChart3 className="w-3.5 h-3.5" /> Legal AI
            </Link>
            <Link to={`${basePath}/investigation/${id}`} className="btn-primary flex items-center gap-1.5 text-xs px-3 py-2">
              <Brain className="w-3.5 h-3.5" /> Investigate
            </Link>
          </div>
        </div>
      </motion.div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          { label: 'AI Confidence', value: `${aiConfidence}%`, icon: Brain, color: 'text-purple-400', bg: 'bg-purple-500/10' },
          { label: 'Risk Score', value: `${riskScore}/100`, icon: AlertTriangle, color: riskScore > 60 ? 'text-red-400' : 'text-yellow-400', bg: riskScore > 60 ? 'bg-red-500/10' : 'bg-yellow-500/10' },
          { label: 'Evidence', value: evidenceCount, icon: Eye, color: 'text-blue-400', bg: 'bg-blue-500/10' },
          { label: 'Documents', value: docCount, icon: FileText, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
          { label: 'Team Size', value: caseData.investigation_team?.length ?? 1, icon: Users, color: 'text-green-400', bg: 'bg-green-500/10' },
        ].map((stat) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="rounded-xl bg-dark-900/60 border border-dark-700/50 p-3 text-center"
          >
            <div className={`w-8 h-8 rounded-lg ${stat.bg} flex items-center justify-center mx-auto mb-1.5`}>
              <stat.icon className={`w-4 h-4 ${stat.color}`} />
            </div>
            <p className="text-white font-bold text-lg">{stat.value}</p>
            <p className="text-dark-400 text-[10px] uppercase tracking-wide">{stat.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Progress Bar — uses completeness API */}
      <ProgressSection caseId={id!} status={caseData.status} />

      {/* Tabs */}
      <div className="flex gap-1 border-b border-dark-700">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-primary-500 text-primary-400'
                : 'border-transparent text-dark-400 hover:text-white'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card">
            <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
              <User className="w-4 h-4 text-primary-400" /> Complainant Details
            </h2>
            <div className="space-y-3">
              <InfoRow label="Name" value={caseData.complainant_name} />
              <InfoRow label="Contact" value={caseData.complainant_contact} />
              <InfoRow label="Address" value={caseData.complainant_address} />
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card">
            <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
              <Shield className="w-4 h-4 text-red-400" /> Incident Details
            </h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <InfoRow label="Accused" value={caseData.accused_name} />
                {caseData.accused_name && (
                  <button
                    onClick={() => navigate('/criminal-intel/add', { state: { fromCase: { full_name: caseData.accused_name, case_fir: caseData.fir_number, offense_type: caseData.offense_type, station_id: caseData.station_id } } })}
                    className="text-xs px-2.5 py-1 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20 hover:bg-purple-500/20 transition-colors whitespace-nowrap"
                  >
                    + Criminal Profile
                  </button>
                )}
              </div>
              <InfoRow label="Date" value={caseData.incident_date} />
              <InfoRow label="Time" value={caseData.incident_time} />
              <InfoRow label="Location" value={caseData.incident_location} />
              <InfoRow label="Station" value={caseData.station_id} />
              <InfoRow label="Officer ID" value={caseData.assigned_officer_id?.toString()} />
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card lg:col-span-2">
            <h2 className="text-base font-semibold text-white mb-3">Complaint Description</h2>
            <p className="text-dark-300 text-sm whitespace-pre-wrap leading-relaxed">{caseData.description}</p>
          </motion.div>

          {caseData.sections_applied && caseData.sections_applied.length > 0 && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card lg:col-span-2">
              <h2 className="text-base font-semibold text-white mb-3 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-yellow-400" /> Applicable Sections
              </h2>
              <div className="flex flex-wrap gap-2">
                {caseData.sections_applied.map((s, i) => (
                  <span key={i} className="px-3 py-1.5 bg-primary-600/10 text-primary-400 rounded-lg text-xs font-medium border border-primary-600/20">
                    {s}
                  </span>
                ))}
              </div>
            </motion.div>
          )}

          {caseData.witnesses && caseData.witnesses.length > 0 && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card">
              <h2 className="text-base font-semibold text-white mb-3 flex items-center gap-2">
                <Users className="w-4 h-4 text-green-400" /> Witnesses
              </h2>
              <div className="space-y-2">
                {caseData.witnesses.map((w, i) => (
                  <div key={i} className="p-2 bg-dark-900/60 rounded-lg text-sm text-dark-300">
                    {(w as Record<string, string>).name || JSON.stringify(w)}
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {caseData.accused_persons && caseData.accused_persons.length > 0 && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-base font-semibold text-white flex items-center gap-2">
                  <Zap className="w-4 h-4 text-red-400" /> Accused Persons
                </h2>
              </div>
              <div className="space-y-2">
                {caseData.accused_persons.map((a, i) => {
                  const accused = a as Record<string, string>
                  return (
                    <div key={i} className="p-3 bg-dark-900/60 rounded-lg flex items-center justify-between">
                      <span className="text-sm text-dark-300">{accused.name || JSON.stringify(a)}</span>
                      <button
                        onClick={() => navigate('/criminal-intel/add', { state: { fromCase: { full_name: accused.name || '', case_fir: caseData.fir_number, offense_type: caseData.offense_type, station_id: caseData.station_id, description: accused.description || '' } } })}
                        className="text-xs px-2.5 py-1 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20 hover:bg-purple-500/20 transition-colors"
                      >
                        + Criminal Profile
                      </button>
                    </div>
                  )
                })}
              </div>
            </motion.div>
          )}
        </div>
      )}

      {activeTab === 'timeline' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card">
          <h2 className="text-base font-semibold text-white mb-6">Investigation Timeline</h2>
          {timeline.length === 0 ? (
            <p className="text-dark-400 text-center py-8">No timeline events yet</p>
          ) : (
            <div className="relative pl-6 space-y-6">
              <div className="absolute left-2 top-2 bottom-2 w-0.5 bg-gradient-to-b from-primary-500 via-dark-700 to-dark-800" />
              {timeline.map((event, i) => (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="relative"
                >
                  <div className="absolute -left-4 top-1 w-3 h-3 rounded-full bg-primary-500 border-2 border-dark-900 shadow-sm shadow-primary-500/30" />
                  <div className="bg-dark-900/40 rounded-lg p-3 border border-dark-800">
                    <p className="text-white text-sm font-medium">{event.title}</p>
                    {event.description && <p className="text-dark-400 text-xs mt-1">{event.description}</p>}
                    <p className="text-dark-500 text-[10px] mt-1.5 flex items-center gap-1">
                      <Clock className="w-3 h-3" /> {new Date(event.created_at).toLocaleString()}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>
      )}

      {activeTab === 'ai' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card flex flex-col" style={{ minHeight: '500px' }}>
          <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary-400" /> Ask CrimeGPT
          </h2>
          <div className="flex-1 overflow-y-auto space-y-3 mb-4 max-h-[400px]">
            {chatMessages.length === 0 && (
              <div className="text-center py-12">
                <Brain className="w-12 h-12 text-dark-600 mx-auto mb-3" />
                <p className="text-dark-400 text-sm">Ask about applicable laws, investigation steps, or case analysis</p>
              </div>
            )}
            {chatMessages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] rounded-xl px-4 py-2.5 ${
                  msg.role === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-dark-800 text-dark-200 border border-dark-700'
                }`}>
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-dark-800 border border-dark-700 rounded-xl px-4 py-2.5">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              </div>
            )}
          </div>
          <div className="flex gap-2 border-t border-dark-700 pt-4">
            <input
              type="text"
              className="input flex-1"
              placeholder="Ask about this case..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendChat()}
            />
            <button onClick={sendChat} disabled={chatLoading || !chatInput.trim()} className="btn-primary px-4 disabled:opacity-50">
              <Send className="w-4 h-4" />
            </button>
          </div>
        </motion.div>
      )}

      {activeTab === 'completeness' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card">
          <h2 className="text-base font-semibold text-white mb-6">Investigation Completeness</h2>
          {completeness ? (
            <>
              <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-dark-300 text-sm">Overall Progress</span>
                  <span className="text-white font-bold text-lg">{completeness.percentage}%</span>
                </div>
                <div className="w-full h-3 bg-dark-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${completeness.percentage}%` }}
                    transition={{ duration: 0.8, ease: 'easeOut' }}
                    className={`h-full rounded-full ${
                      completeness.percentage >= 80 ? 'bg-green-500' :
                      completeness.percentage >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                  />
                </div>
              </div>
              <div className="space-y-3">
                {completeness.items.map((item) => (
                  <div key={item.key} className="flex items-center gap-3">
                    <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                      item.completed ? 'bg-green-500/20 text-green-400' : 'bg-dark-700 text-dark-500'
                    }`}>
                      {item.completed ? <CheckCircle className="w-3.5 h-3.5" /> : <div className="w-2 h-2 rounded-full bg-dark-600" />}
                    </div>
                    <span className={`text-sm ${item.completed ? 'text-dark-200' : 'text-dark-400'}`}>
                      {item.label}
                    </span>
                    <span className="text-dark-500 text-xs ml-auto">{item.weight}pts</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-dark-400 text-center py-8">Loading...</p>
          )}
        </motion.div>
      )}
    </div>
  )
}

function ProgressSection({ caseId, status }: { caseId: string; status: string }) {
  const [pct, setPct] = useState<number | null>(null)

  useEffect(() => {
    api.get(`/api/cases/${caseId}/completeness`)
      .then(r => setPct(r.data.percentage ?? null))
      .catch(() => setPct(null))
  }, [caseId])

  const progress = pct ?? (status === 'closed' ? 100 : status === 'chargesheet_filed' ? 80 : status === 'investigating' ? 45 : 15)

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="rounded-xl bg-dark-900/60 border border-dark-700/50 p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-dark-300 flex items-center gap-2"><TrendingUp className="w-4 h-4 text-primary-400" /> Investigation Progress</span>
        <span className="text-white font-bold">{progress}%</span>
      </div>
      <div className="w-full h-2 bg-dark-800 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
          className={`h-full rounded-full ${
            progress >= 80 ? 'bg-green-500' :
            progress >= 50 ? 'bg-yellow-500' : 'bg-blue-500'
          }`}
        />
      </div>
    </motion.div>
  )
}

function InfoRow({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="flex items-start gap-2">
      <span className="text-dark-500 text-xs min-w-[80px] uppercase tracking-wide">{label}</span>
      <span className="text-dark-200 text-sm">{value || '—'}</span>
    </div>
  )
}
