import { useState, useRef, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Mic, MicOff, Brain, Send } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../api/client'
import { useCaseStore } from '../store/caseStore'
import { useDashboardStore } from '../store/dashboardStore'

export default function NewCasePage() {
  const navigate = useNavigate()
  const [complaintText, setComplaintText] = useState('')
  const [extracting, setExtracting] = useState(false)
  const [recording, setRecording] = useState(false)
  const [extracted, setExtracted] = useState<Record<string, unknown> | null>(null)
  const [form, setForm] = useState({
    complainant_name: '',
    complainant_contact: '',
    complainant_address: '',
    accused_name: '',
    incident_date: '',
    incident_time: '',
    incident_location: '',
    description: '',
    offense_type: '',
    station_id: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [showCustomOffense, setShowCustomOffense] = useState(false)

  const OFFENSE_TYPES = useMemo(() => [
    'Theft (Section 303 BNS)',
    'Robbery (Section 309 BNS)',
    'Murder (Section 101 BNS)',
    'Attempt to Murder (Section 109 BNS)',
    'Kidnapping (Section 137 BNS)',
    'Assault (Section 115 BNS)',
    'Sexual Harassment (Section 75 BNS)',
    'Rape (Section 63 BNS)',
    'Cheating (Section 318 BNS)',
    'Forgery (Section 336 BNS)',
    'Criminal Breach of Trust (Section 316 BNS)',
    'Extortion (Section 308 BNS)',
    'Dacoity (Section 310 BNS)',
    'Rioting (Section 189 BNS)',
    'Dowry Death (Section 80 BNS)',
    'Domestic Violence (Section 85 BNS)',
    'Cyber Crime (IT Act)',
    'Drug Trafficking (NDPS Act)',
    'Arms Act Violation',
    'SC/ST Atrocity (PoA Act)',
    'POCSO Act Violation',
    'Motor Vehicle Theft',
    'House Breaking (Section 329 BNS)',
    'Criminal Intimidation (Section 351 BNS)',
    'Mischief / Property Damage (Section 324 BNS)',
  ], [])

  const handleExtract = async () => {
    if (!complaintText.trim()) {
      toast.error('Enter complaint text first')
      return
    }
    setExtracting(true)
    try {
      const response = await api.post('/api/agents/intake', {
        complaint_text: complaintText,
        language: 'en',
      })
      const data = response.data
      setExtracted(data)
      const extractedOffense = data.offense_type || form.offense_type
      const isKnownOffense = OFFENSE_TYPES.includes(extractedOffense)
      setShowCustomOffense(!isKnownOffense && !!extractedOffense)
      setForm({
        ...form,
        complainant_name: data.complainant_name || form.complainant_name,
        accused_name: data.accused_name || form.accused_name,
        incident_date: data.incident_date || form.incident_date,
        incident_location: data.incident_location || form.incident_location,
        offense_type: extractedOffense,
        description: complaintText,
      })
      toast.success('Data extracted successfully')
    } catch {
      toast.error('Extraction failed — fill manually')
    } finally {
      setExtracting(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const payload = {
        ...form,
        incident_date: form.incident_date || null,
      }
      const response = await api.post('/api/cases/', payload)
      useCaseStore.getState().invalidateList()
      useDashboardStore.getState().invalidate()
      toast.success(`Case created: ${response.data.fir_number}`)
      navigate(`/cases/${response.data.public_id}`)
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      toast.error(error.response?.data?.detail || 'Failed to create case')
    } finally {
      setSubmitting(false)
    }
  }

  const recognitionRef = useRef<{ stop: () => void } | null>(null)

  const toggleRecording = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) {
      toast.error('Speech recognition not supported in this browser')
      return
    }

    if (!recording) {
      const recognition = new SpeechRecognition()
      recognition.lang = 'en-IN'
      recognition.continuous = true
      recognition.interimResults = true
      recognition.onresult = (event: { results: { length: number; [i: number]: { [j: number]: { transcript: string } } } }) => {
        let transcript = ''
        for (let i = 0; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript
        }
        setComplaintText(transcript)
      }
      recognition.onerror = () => {
        setRecording(false)
        toast.error('Voice recognition error')
      }
      recognition.onend = () => setRecording(false)
      recognition.start()
      recognitionRef.current = recognition
      setRecording(true)
      toast.success('Listening... speak your complaint')
    } else {
      if (recognitionRef.current) recognitionRef.current.stop()
      setRecording(false)
      toast.success('Recording stopped')
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Register New Case</h1>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card"
      >
        <h2 className="text-lg font-semibold text-white mb-4">Complaint Input</h2>
        <p className="text-dark-400 text-sm mb-4">
          Enter the complaint text or use voice input. AI will extract structured data automatically.
        </p>
        <div className="relative">
          <textarea
            className="input min-h-[160px] resize-y"
            placeholder="Enter the full complaint statement here..."
            value={complaintText}
            onChange={(e) => setComplaintText(e.target.value)}
          />
          <div className="absolute bottom-3 right-3 flex gap-2">
            <button
              type="button"
              onClick={toggleRecording}
              className={`p-2 rounded-lg transition-colors ${
                recording ? 'bg-red-500 text-white' : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
              }`}
            >
              {recording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>
            <button
              type="button"
              onClick={handleExtract}
              disabled={extracting}
              className="flex items-center gap-2 px-3 py-1.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-sm disabled:opacity-50"
            >
              <Brain className="w-4 h-4" />
              {extracting ? 'Extracting...' : 'Extract'}
            </button>
          </div>
        </div>

        {extracted && (
          <div className="mt-4 p-4 bg-dark-900 rounded-lg border border-primary-600/30">
            <p className="text-sm text-primary-400 font-medium mb-2">AI Extracted Data:</p>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {Object.entries(extracted).filter(([, v]) => v).map(([k, v]) => (
                <div key={k}>
                  <span className="text-dark-400">{k.replace('_', ' ')}: </span>
                  <span className="text-white">{Array.isArray(v) ? (v as string[]).join(', ') : String(v)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card"
      >
        <h2 className="text-lg font-semibold text-white mb-4">Case Details</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1">Complainant Name *</label>
              <input
                type="text"
                className="input"
                value={form.complainant_name}
                onChange={(e) => setForm({ ...form, complainant_name: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1">Contact</label>
              <input
                type="text"
                className="input"
                value={form.complainant_contact}
                onChange={(e) => setForm({ ...form, complainant_contact: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1">Accused Name</label>
              <input
                type="text"
                className="input"
                value={form.accused_name}
                onChange={(e) => setForm({ ...form, accused_name: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1">Offense Type</label>
              <select
                className="input"
                value={showCustomOffense ? '__other__' : form.offense_type}
                onChange={(e) => {
                  if (e.target.value === '__other__') {
                    setShowCustomOffense(true)
                    setForm({ ...form, offense_type: '' })
                  } else {
                    setShowCustomOffense(false)
                    setForm({ ...form, offense_type: e.target.value })
                  }
                }}
              >
                <option value="">Select offense type</option>
                {OFFENSE_TYPES.map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
                <option value="__other__">Others (specify below)</option>
              </select>
              {showCustomOffense && (
                <input
                  type="text"
                  className="input mt-2"
                  placeholder="Enter offense type..."
                  value={form.offense_type}
                  onChange={(e) => setForm({ ...form, offense_type: e.target.value })}
                  autoFocus
                />
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1">Incident Date</label>
              <input
                type="date"
                className="input"
                value={form.incident_date}
                onChange={(e) => setForm({ ...form, incident_date: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1">Incident Time</label>
              <input
                type="time"
                className="input"
                value={form.incident_time}
                onChange={(e) => setForm({ ...form, incident_time: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-300 mb-1">Incident Location</label>
            <input
              type="text"
              className="input"
              value={form.incident_location}
              onChange={(e) => setForm({ ...form, incident_location: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-300 mb-1">Complainant Address</label>
            <textarea
              className="input min-h-[80px]"
              value={form.complainant_address}
              onChange={(e) => setForm({ ...form, complainant_address: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-300 mb-1">Description *</label>
            <textarea
              className="input min-h-[120px]"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              required
            />
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary flex items-center gap-2 disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              {submitting ? 'Creating...' : 'Register Case'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  )
}
