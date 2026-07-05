import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BookOpen, Plus, Calendar, Clock, FileText, Loader2, User } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../api/client'

interface DiaryEntry {
  id: number
  case_id: number
  entry_date: string
  content: string
  entry_type: string
  officer_id: number
  created_at: string
}

const ENTRY_TYPES = [
  'investigation_step',
  'evidence_collected',
  'witness_statement',
  'arrest_details',
  'court_appearance',
  'supervisor_note',
  'other',
]

export default function CaseDiaryPage() {
  const { caseId } = useParams()
  const [entries, setEntries] = useState<DiaryEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState({
    content: '',
    entry_type: 'investigation_step',
    entry_date: new Date().toISOString().split('T')[0],
  })

  useEffect(() => { fetchEntries() }, [caseId])

  const fetchEntries = async () => {
    try {
      const res = await api.get(`/api/documents/diary/${caseId}`)
      setEntries(res.data)
    } catch { /* silent */ }
    finally { setLoading(false) }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.content.trim()) return
    setSubmitting(true)
    try {
      const res = await api.post(`/api/documents/diary/${caseId}`, form)
      setEntries(prev => [res.data, ...prev])
      setForm({ content: '', entry_type: 'investigation_step', entry_date: new Date().toISOString().split('T')[0] })
      setShowForm(false)
      toast.success('Diary entry added')
    } catch {
      toast.error('Failed to add diary entry')
    } finally {
      setSubmitting(false)
    }
  }

  const typeLabels: Record<string, { label: string; color: string }> = {
    investigation_step: { label: 'Investigation', color: 'text-blue-400 bg-blue-500/10' },
    evidence_collected: { label: 'Evidence', color: 'text-purple-400 bg-purple-500/10' },
    witness_statement: { label: 'Witness', color: 'text-green-400 bg-green-500/10' },
    arrest_details: { label: 'Arrest', color: 'text-red-400 bg-red-500/10' },
    court_appearance: { label: 'Court', color: 'text-orange-400 bg-orange-500/10' },
    supervisor_note: { label: 'Supervisor', color: 'text-yellow-400 bg-yellow-500/10' },
    other: { label: 'Other', color: 'text-dark-400 bg-dark-700' },
  }

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map(i => <div key={i} className="card animate-pulse h-24 bg-dark-800/50" />)}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-600/20 rounded-xl flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-amber-400" />
            </div>
            Case Diary
          </h1>
          <p className="text-dark-400 text-sm mt-1">Investigation diary entries for Case #{caseId}</p>
        </div>
        <div className="flex gap-2">
          <Link to={`/cases/${caseId}`} className="btn-secondary text-sm">← Back to Case</Link>
          <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-2 text-sm">
            <Plus className="w-4 h-4" />
            New Entry
          </button>
        </div>
      </div>

      {/* New Entry Form */}
      {showForm && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="card border border-primary-500/20">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <FileText className="w-4 h-4 text-primary-400" />
            New Diary Entry
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-dark-300 mb-1">Entry Date</label>
                <input
                  type="date"
                  className="input text-sm"
                  value={form.entry_date}
                  onChange={e => setForm({ ...form, entry_date: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm text-dark-300 mb-1">Entry Type</label>
                <select
                  className="input text-sm"
                  value={form.entry_type}
                  onChange={e => setForm({ ...form, entry_type: e.target.value })}
                >
                  {ENTRY_TYPES.map(t => (
                    <option key={t} value={t}>{typeLabels[t]?.label || t}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Content</label>
              <textarea
                className="input min-h-[120px] text-sm"
                placeholder="Describe the investigation activity, findings, or observations..."
                value={form.content}
                onChange={e => setForm({ ...form, content: e.target.value })}
                required
              />
            </div>
            <div className="flex gap-2">
              <button type="submit" disabled={submitting || !form.content.trim()} className="btn-primary flex items-center gap-2 text-sm disabled:opacity-50">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                Add Entry
              </button>
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary text-sm">Cancel</button>
            </div>
          </form>
        </motion.div>
      )}

      {/* Entries Timeline */}
      {entries.length === 0 ? (
        <div className="card text-center py-16">
          <BookOpen className="w-12 h-12 text-dark-600 mx-auto mb-3" />
          <p className="text-dark-400">No diary entries yet</p>
          <p className="text-dark-500 text-xs mt-1">Start documenting your investigation progress</p>
        </div>
      ) : (
        <div className="relative pl-6 space-y-4">
          <div className="absolute left-2 top-4 bottom-4 w-0.5 bg-gradient-to-b from-primary-500 via-dark-700 to-dark-800" />
          {entries.map((entry, i) => {
            const typeInfo = typeLabels[entry.entry_type] || typeLabels.other
            return (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="relative"
              >
                <div className="absolute -left-4 top-4 w-3 h-3 rounded-full bg-primary-500 border-2 border-dark-900 shadow-sm shadow-primary-500/30" />
                <div className="card">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${typeInfo.color}`}>
                        {typeInfo.label}
                      </span>
                      <span className="text-dark-500 text-xs flex items-center gap-1">
                        <Calendar className="w-3 h-3" /> {entry.entry_date}
                      </span>
                    </div>
                    <span className="text-dark-500 text-[10px] flex items-center gap-1">
                      <Clock className="w-3 h-3" /> {new Date(entry.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-dark-200 text-sm whitespace-pre-wrap leading-relaxed">{entry.content}</p>
                  <div className="mt-2 flex items-center gap-1 text-dark-500 text-[10px]">
                    <User className="w-3 h-3" />
                    Officer ID: {entry.officer_id}
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      )}
    </div>
  )
}
