import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Brain, Upload, Send, FileImage, FileAudio, FileText, AlertTriangle,
  CheckCircle, XCircle, Loader2, Clock, Shield, User, Bot,
  Plus, ChevronRight, ChevronDown, Trash2, Search, Copy,
  Camera, Fingerprint, Car, FileSearch, Hash, Mic, Eye, Target,
  Skull, Dna, CreditCard, ScanLine, Activity, MapPin,
  Image, File, X,
  Crosshair, Zap, Globe, Lock, Scale, AlertOctagon,
} from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import api from '../../api/client'
import { useAuthStore } from '../../store/authStore'

// ─── Types ───────────────────────────────────────────────────────────────────

interface Session {
  session_id: string
  title: string
  status: string
  created_at: string
  updated_at: string
  message_count: number
}

interface Message {
  message_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  attachments?: any[]
  tool_executions?: any[]
  metadata?: any
  created_at: string
}

interface ToolProgress {
  tool_key: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  confidence?: number
  execution_time_ms?: number
  output?: any
}

interface Classification {
  type: string
  mime_type: string
  confidence: number
}

// ─── Tool Metadata ───────────────────────────────────────────────────────────

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
  face_recognize: { icon: User, label: 'Face Recognition', color: 'text-rose-400', bgColor: 'bg-rose-500/10' },
  fingerprint_match: { icon: Fingerprint, label: 'Fingerprint Match', color: 'text-purple-400', bgColor: 'bg-purple-500/10' },
  dna_search: { icon: Dna, label: 'DNA Analysis', color: 'text-green-400', bgColor: 'bg-green-500/10' },
  vehicle_detect: { icon: Car, label: 'Vehicle Detection', color: 'text-sky-400', bgColor: 'bg-sky-500/10' },
  license_plate_ocr: { icon: CreditCard, label: 'License Plate', color: 'text-yellow-400', bgColor: 'bg-yellow-500/10' },
  weapon_detect: { icon: Crosshair, label: 'Weapon Detection', color: 'text-red-400', bgColor: 'bg-red-500/10' },
  image_similarity: { icon: Image, label: 'Image Similarity', color: 'text-indigo-400', bgColor: 'bg-indigo-500/10' },
  crime_scene_analysis: { icon: AlertOctagon, label: 'Crime Scene AI', color: 'text-red-400', bgColor: 'bg-red-500/10' },
}

function getToolMeta(toolKey: string) {
  return TOOL_META[toolKey] || { icon: Zap, label: toolKey.replace(/_/g, ' '), color: 'text-dark-400', bgColor: 'bg-dark-700' }
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function AIInvestigationPage() {
  const { accessToken } = useAuthStore()
  const [sessions, setSessions] = useState<Session[]>([])
  const [activeSession, setActiveSession] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isInvestigating, setIsInvestigating] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<{ name: string; classification?: Classification; message_id?: string; url?: string } | null>(null)
  const [toolProgress, setToolProgress] = useState<ToolProgress[]>([])
  const [criminalMatches, setCriminalMatches] = useState<any[]>([])
  const [showSidebar, setShowSidebar] = useState(true)
  const [showTimeline, setShowTimeline] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set())
  const [expandedReportSections, setExpandedReportSections] = useState<Set<string>>(new Set(['executive-summary']))
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const filePreviewRef = useRef<string | null>(null)

  useEffect(() => { loadSessions() }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, toolProgress])

  const filteredSessions = useMemo(() => {
    if (!searchQuery) return sessions
    return sessions.filter(s => s.title.toLowerCase().includes(searchQuery.toLowerCase()))
  }, [sessions, searchQuery])

  // ─── API Functions (unchanged) ──────────────────────────────────────────────

  const loadSessions = async () => {
    try {
      const res = await api.get('/api/ai-investigation/sessions')
      setSessions(res.data)
    } catch (e) {
      console.error('Failed to load sessions', e)
    }
  }

  const createSession = async () => {
    try {
      const res = await api.post('/api/ai-investigation/sessions', { title: null })
      setSessions(prev => [res.data, ...prev])
      setActiveSession(res.data.session_id)
      setMessages([])
      setUploadedFile(null)
      setToolProgress([])
      setCriminalMatches([])
    } catch (e) {
      console.error('Failed to create session', e)
    }
  }

  const loadSession = async (sessionId: string) => {
    try {
      const res = await api.get(`/api/ai-investigation/sessions/${sessionId}`)
      setActiveSession(sessionId)
      setMessages(res.data.messages || [])
      setUploadedFile(null)
      setToolProgress([])
      setCriminalMatches([])
    } catch (e) {
      console.error('Failed to load session', e)
    }
  }

  const deleteSession = async (sessionId: string) => {
    try {
      await api.delete(`/api/ai-investigation/sessions/${sessionId}`)
      setSessions(prev => prev.filter(s => s.session_id !== sessionId))
      if (activeSession === sessionId) {
        setActiveSession(null)
        setMessages([])
      }
    } catch (e) {
      console.error('Failed to delete session', e)
    }
  }

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (!acceptedFiles.length) return

    let sessionId = activeSession
    if (!sessionId) {
      const res = await api.post('/api/ai-investigation/sessions', { title: null })
      setSessions(prev => [res.data, ...prev])
      sessionId = res.data.session_id
      setActiveSession(sessionId)
      setMessages([])
    }

    const file = acceptedFiles[0]
    const formData = new FormData()
    formData.append('file', file)

    const previewUrl = file.type.startsWith('image/') ? URL.createObjectURL(file) : null
    filePreviewRef.current = previewUrl

    try {
      setIsLoading(true)
      const res = await api.post(`/api/ai-investigation/sessions/${sessionId}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setUploadedFile({
        name: res.data.original_filename,
        classification: res.data.classification,
        message_id: res.data.message_id,
        url: previewUrl || undefined,
      })
      setMessages(prev => [...prev, {
        message_id: res.data.message_id,
        role: 'user',
        content: `Uploaded evidence: ${res.data.original_filename}`,
        attachments: [{ ...res.data, preview_url: previewUrl }],
        created_at: new Date().toISOString(),
      }])
      startInvestigation(sessionId!)
    } catch (e) {
      console.error('Upload failed', e)
    } finally {
      setIsLoading(false)
    }
  }, [activeSession])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'],
      'audio/*': ['.wav', '.mp3', '.ogg', '.flac', '.m4a'],
      'application/pdf': ['.pdf'],
      'text/*': ['.txt', '.csv'],
    },
  })

  const startInvestigation = async (sessionId: string) => {
    setIsInvestigating(true)
    setToolProgress([])
    setCriminalMatches([])
    setShowTimeline(true)

    const formData = new FormData()
    formData.append('message', inputMessage || '')

    try {
      const response = await fetch(`/api/ai-investigation/sessions/${sessionId}/investigate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${accessToken}` },
        body: formData,
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
              handleSSEEvent(eventName, data)
            } catch {}
          }
        }
      }
    } catch (e) {
      console.error('Investigation error', e)
    } finally {
      setIsInvestigating(false)
      setInputMessage('')
      loadSessions()
    }
  }

  const handleSSEEvent = (event: string, data: any) => {
    switch (event) {
      case 'classification':
        setUploadedFile(prev => prev ? { ...prev, classification: data } : null)
        break
      case 'plan':
        if (Array.isArray(data.tools_selected)) {
          setToolProgress(data.tools_selected.map((t: string) => ({
            tool_key: t, status: 'pending',
          })))
        }
        break
      case 'tool_start':
        setToolProgress(prev => prev.map(t =>
          t.tool_key === data.tool_key ? { ...t, status: 'running' } : t
        ))
        break
      case 'tool_complete':
        setToolProgress(prev => prev.map(t =>
          t.tool_key === data.tool_key ? {
            ...t,
            status: data.status === 'completed' ? 'completed' : 'failed',
            confidence: data.confidence,
            execution_time_ms: data.execution_time_ms,
            output: data.output,
          } : t
        ))
        break
      case 'criminal_matches':
        setCriminalMatches(data.matches || [])
        break
      case 'report_complete':
        setMessages(prev => [...prev, {
          message_id: crypto.randomUUID(),
          role: 'assistant',
          content: data.report,
          created_at: new Date().toISOString(),
        }])
        break
      case 'complete':
        if (data.criminal_matches?.length) {
          setCriminalMatches(data.criminal_matches)
        }
        break
    }
  }

  const sendFollowUp = async () => {
    if (!inputMessage.trim() || !activeSession) return

    const userMsg: Message = {
      message_id: crypto.randomUUID(),
      role: 'user',
      content: inputMessage,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    setInputMessage('')
    setIsLoading(true)

    try {
      const res = await api.post(`/api/ai-investigation/sessions/${activeSession}/message`, {
        message: userMsg.content,
      })
      setMessages(prev => [...prev, {
        message_id: res.data.assistant_message.message_id,
        role: 'assistant',
        content: res.data.assistant_message.content,
        created_at: res.data.assistant_message.created_at,
      }])
    } catch (e) {
      setMessages(prev => [...prev, {
        message_id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Failed to process your message. Please try again.',
        created_at: new Date().toISOString(),
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (uploadedFile && !isInvestigating) {
        startInvestigation(activeSession!)
      } else {
        sendFollowUp()
      }
    }
  }

  const toggleToolExpand = (toolKey: string) => {
    setExpandedTools(prev => {
      const next = new Set(prev)
      if (next.has(toolKey)) next.delete(toolKey)
      else next.add(toolKey)
      return next
    })
  }

  const toggleReportSection = (section: string) => {
    setExpandedReportSections(prev => {
      const next = new Set(prev)
      if (next.has(section)) next.delete(section)
      else next.add(section)
      return next
    })
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  // ─── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden bg-dark-900">
      {/* ─── Left Sidebar: Sessions ──────────────────────────────────────── */}
      <AnimatePresence>
        {showSidebar && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 300, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-r border-dark-700/50 flex flex-col bg-dark-900/80 backdrop-blur-sm"
          >
            <div className="p-3 border-b border-dark-700/50 space-y-2">
              <button
                onClick={createSession}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white text-sm font-medium transition-all shadow-lg shadow-primary-500/20 hover:shadow-primary-500/30"
              >
                <Plus className="w-4 h-4" />
                New Investigation
              </button>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-dark-500" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Search investigations..."
                  className="w-full pl-9 pr-3 py-2 text-xs bg-dark-800 border border-dark-700/50 rounded-lg text-dark-300 placeholder-dark-500 focus:outline-none focus:border-primary-500/50"
                />
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {filteredSessions.map(s => (
                <motion.div
                  key={s.session_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  onClick={() => loadSession(s.session_id)}
                  className={`group relative flex items-start gap-3 px-3 py-2.5 rounded-xl cursor-pointer transition-all duration-200 ${
                    activeSession === s.session_id
                      ? 'bg-primary-500/10 border border-primary-500/20 shadow-sm'
                      : 'hover:bg-dark-800 border border-transparent'
                  }`}
                >
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    activeSession === s.session_id ? 'bg-primary-500/20' : 'bg-dark-750'
                  }`}>
                    <Brain className={`w-4 h-4 ${activeSession === s.session_id ? 'text-primary-400' : 'text-dark-400'}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium truncate ${
                      activeSession === s.session_id ? 'text-white' : 'text-dark-200'
                    }`}>{s.title}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] text-dark-500">
                        {new Date(s.created_at).toLocaleDateString()}
                      </span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                        s.status === 'completed' ? 'bg-green-500/10 text-green-400' :
                        s.status === 'active' ? 'bg-amber-500/10 text-amber-400' :
                        'bg-dark-700 text-dark-400'
                      }`}>
                        {s.status}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteSession(s.session_id) }}
                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-dark-700 transition-all"
                  >
                    <Trash2 className="w-3 h-3 text-dark-500 hover:text-red-400" />
                  </button>
                </motion.div>
              ))}
              {filteredSessions.length === 0 && (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <div className="w-12 h-12 rounded-xl bg-dark-800 flex items-center justify-center mb-3">
                    <Search className="w-5 h-5 text-dark-500" />
                  </div>
                  <p className="text-dark-500 text-xs">No investigations found</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ─── Main Chat Area ──────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-3 border-b border-dark-700/50 bg-dark-900/90 backdrop-blur-sm">
          <button
            onClick={() => setShowSidebar(!showSidebar)}
            className="p-2 rounded-lg hover:bg-dark-800 text-dark-400 hover:text-white transition-colors"
          >
            <ChevronRight className={`w-4 h-4 transition-transform duration-200 ${showSidebar ? 'rotate-180' : ''}`} />
          </button>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500/20 to-purple-500/20 flex items-center justify-center">
              <Brain className="w-4.5 h-4.5 text-primary-400" />
            </div>
            <div>
              <h1 className="text-sm font-semibold text-white leading-tight">Crime Analyst AI</h1>
              <p className="text-[10px] text-dark-500 leading-tight">Forensic Analysis Engine</p>
            </div>
          </div>
          {isInvestigating && (
            <div className="ml-auto flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20">
              <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              <span className="text-amber-400 text-xs font-medium">Investigating</span>
            </div>
          )}
          {!isInvestigating && toolProgress.length > 0 && toolProgress.every(t => t.status === 'completed' || t.status === 'failed') && (
            <div className="ml-auto flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20">
              <CheckCircle className="w-3 h-3 text-green-400" />
              <span className="text-green-400 text-xs font-medium">Analysis Complete</span>
            </div>
          )}
          <button
            onClick={() => setShowTimeline(!showTimeline)}
            className={`p-2 rounded-lg transition-colors ${showTimeline ? 'bg-primary-500/10 text-primary-400' : 'hover:bg-dark-800 text-dark-400 hover:text-white'}`}
          >
            <Activity className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 flex overflow-hidden">
          {/* ─── Messages Area ───────────────────────────────────────────── */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex-1 overflow-y-auto">
              {/* Empty State */}
              {messages.length === 0 && !activeSession && (
                <div className="flex flex-col items-center justify-center h-full px-4">
                  <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ duration: 0.5 }}
                    className="text-center max-w-lg"
                  >
                    <div className="relative w-24 h-24 mx-auto mb-6">
                      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-primary-500/20 to-purple-500/20 animate-pulse-glow" />
                      <div className="relative w-full h-full rounded-2xl bg-dark-800 border border-dark-700/50 flex items-center justify-center">
                        <Brain className="w-12 h-12 text-primary-400" />
                      </div>
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">Crime Analyst AI</h2>
                    <p className="text-dark-400 text-sm mb-8 leading-relaxed">
                      Upload evidence and I'll automatically classify it, run forensic analysis tools,
                      search criminal intelligence databases, and generate a comprehensive investigation report.
                    </p>

                    <div {...getRootProps()} className={`relative w-full border-2 border-dashed rounded-2xl p-10 cursor-pointer transition-all duration-300 group ${
                      isDragActive
                        ? 'border-primary-400 bg-primary-400/5 scale-[1.02]'
                        : 'border-dark-600/50 hover:border-primary-500/30 hover:bg-dark-800/50'
                    }`}>
                      <input {...getInputProps()} />
                      <div className="flex flex-col items-center">
                        <div className="w-14 h-14 rounded-2xl bg-dark-750 border border-dark-700/50 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                          <Upload className="w-6 h-6 text-dark-400 group-hover:text-primary-400 transition-colors" />
                        </div>
                        <p className="text-dark-200 text-sm font-medium">
                          {isDragActive ? 'Drop evidence here...' : 'Drag & drop evidence file'}
                        </p>
                        <p className="text-dark-500 text-xs mt-1.5">
                          or click to browse
                        </p>
                        <div className="flex items-center gap-3 mt-4">
                          {[
                            { icon: FileImage, label: 'Images' },
                            { icon: FileAudio, label: 'Audio' },
                            { icon: FileText, label: 'Documents' },
                          ].map(({ icon: Icon, label }) => (
                            <span key={label} className="flex items-center gap-1.5 text-[10px] text-dark-500 px-2 py-1 rounded-md bg-dark-800">
                              <Icon className="w-3 h-3" />
                              {label}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                </div>
              )}

              {/* Active session, no messages */}
              {messages.length === 0 && activeSession && !uploadedFile && (
                <div className="flex flex-col items-center justify-center h-full px-4">
                  <div {...getRootProps()} className={`w-full max-w-md border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-300 ${
                    isDragActive ? 'border-primary-400 bg-primary-400/5' : 'border-dark-600/50 hover:border-primary-500/30'
                  }`}>
                    <input {...getInputProps()} />
                    <Upload className="w-10 h-10 mx-auto mb-4 text-dark-400" />
                    <p className="text-dark-200 text-sm font-medium">Upload evidence to begin</p>
                    <p className="text-dark-500 text-xs mt-1">Images, audio, PDFs, documents</p>
                  </div>
                </div>
              )}

              {/* ─── Message List ──────────────────────────────────────────── */}
              {(messages.length > 0 || toolProgress.length > 0) && (
                <div className="p-4 lg:p-6 space-y-5 max-w-4xl mx-auto w-full">
                  {messages.map((msg) => (
                    <MessageBubble
                      key={msg.message_id}
                      message={msg}
                      expandedReportSections={expandedReportSections}
                      toggleReportSection={toggleReportSection}
                      copyToClipboard={copyToClipboard}
                    />
                  ))}

                  {/* ─── Tool Execution Cards ─────────────────────────────── */}
                  {toolProgress.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="space-y-3"
                    >
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-500/20 to-purple-500/20 flex items-center justify-center">
                          <Bot className="w-4 h-4 text-primary-400" />
                        </div>
                        <div>
                          <h3 className="text-sm font-semibold text-white">Forensic Analysis Pipeline</h3>
                          <p className="text-[10px] text-dark-500">
                            {toolProgress.filter(t => t.status === 'completed').length}/{toolProgress.length} tools completed
                          </p>
                        </div>
                        {isInvestigating && (
                          <div className="ml-auto">
                            <div className="w-5 h-5 border-2 border-primary-400/30 border-t-primary-400 rounded-full animate-spin" />
                          </div>
                        )}
                      </div>

                      {/* Progress Bar */}
                      <div className="w-full h-1.5 bg-dark-800 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-gradient-to-r from-primary-500 to-green-500 rounded-full"
                          initial={{ width: '0%' }}
                          animate={{
                            width: `${(toolProgress.filter(t => t.status === 'completed' || t.status === 'failed').length / toolProgress.length) * 100}%`
                          }}
                          transition={{ duration: 0.5 }}
                        />
                      </div>

                      {/* Tool Cards Grid */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
                        {toolProgress.map((tool, index) => (
                          <ToolCard
                            key={tool.tool_key}
                            tool={tool}
                            index={index}
                            isExpanded={expandedTools.has(tool.tool_key)}
                            onToggle={() => toggleToolExpand(tool.tool_key)}
                            copyToClipboard={copyToClipboard}
                          />
                        ))}
                      </div>
                    </motion.div>
                  )}

                  {/* ─── Criminal Matches ────────────────────────────────── */}
                  {criminalMatches.length > 0 && (
                    <CriminalMatchesSection matches={criminalMatches} />
                  )}

                  {/* Loading indicator */}
                  {isLoading && !isInvestigating && (
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-500/20 to-purple-500/20 flex items-center justify-center">
                        <Bot className="w-4 h-4 text-primary-400" />
                      </div>
                      <div className="bg-dark-800 border border-dark-700/50 rounded-2xl rounded-tl-md px-5 py-3">
                        <div className="flex items-center gap-2">
                          <div className="flex gap-1">
                            <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                          </div>
                          <span className="text-dark-400 text-xs ml-2">Analyzing...</span>
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>

            {/* ─── Input Area ──────────────────────────────────────────────── */}
            <div className="border-t border-dark-700/50 p-4 bg-dark-900/90 backdrop-blur-sm">
              {/* File attachment preview */}
              {activeSession && uploadedFile && (
                <div className="flex items-center gap-2 mb-3 px-3 py-2 rounded-xl bg-dark-800 border border-dark-700/50">
                  <div className="w-8 h-8 rounded-lg bg-primary-500/10 flex items-center justify-center">
                    <FileImage className="w-4 h-4 text-primary-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-white truncate">{uploadedFile.name}</p>
                    {uploadedFile.classification && (
                      <p className="text-[10px] text-dark-500">
                        Classified as: <span className="text-primary-400">{uploadedFile.classification.type}</span>
                      </p>
                    )}
                  </div>
                  <button onClick={() => setUploadedFile(null)} className="p-1 rounded hover:bg-dark-700">
                    <X className="w-3 h-3 text-dark-500" />
                  </button>
                </div>
              )}

              <div className="flex items-end gap-3 max-w-4xl mx-auto">
                {activeSession && (
                  <div {...getRootProps()} className="cursor-pointer">
                    <input {...getInputProps()} />
                    <button className="p-2.5 rounded-xl hover:bg-dark-800 border border-dark-700/50 text-dark-400 hover:text-primary-400 transition-all">
                      <Upload className="w-4 h-4" />
                    </button>
                  </div>
                )}
                <div className="flex-1 relative">
                  <textarea
                    ref={inputRef}
                    value={inputMessage}
                    onChange={e => setInputMessage(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={
                      !activeSession
                        ? 'Create a new investigation to begin...'
                        : isInvestigating
                        ? 'Investigation in progress...'
                        : 'Ask a follow-up question about the evidence...'
                    }
                    disabled={!activeSession || isInvestigating}
                    rows={1}
                    className="w-full bg-dark-800 border border-dark-700/50 rounded-xl px-4 py-3 pr-12 text-sm text-white placeholder-dark-500 resize-none focus:outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/20 disabled:opacity-50 transition-all"
                  />
                </div>
                <button
                  onClick={() => {
                    if (uploadedFile && !isInvestigating) {
                      startInvestigation(activeSession!)
                    } else {
                      sendFollowUp()
                    }
                  }}
                  disabled={!activeSession || isInvestigating || (!inputMessage.trim() && !uploadedFile)}
                  className="p-2.5 rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white disabled:opacity-30 disabled:hover:from-primary-600 transition-all shadow-lg shadow-primary-500/20 disabled:shadow-none"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* ─── Right Sidebar: Timeline ────────────────────────────────── */}
          <AnimatePresence>
            {showTimeline && toolProgress.length > 0 && (
              <motion.div
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 280, opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="border-l border-dark-700/50 bg-dark-900/80 backdrop-blur-sm overflow-y-auto flex-shrink-0"
              >
                <div className="p-4">
                  <div className="flex items-center gap-2 mb-4">
                    <Activity className="w-4 h-4 text-primary-400" />
                    <h3 className="text-sm font-semibold text-white">Investigation Timeline</h3>
                  </div>

                  {/* File Preview */}
                  {filePreviewRef.current && (
                    <div className="mb-4 rounded-xl overflow-hidden border border-dark-700/50">
                      <img src={filePreviewRef.current} alt="Evidence" className="w-full h-32 object-cover" />
                      <div className="p-2 bg-dark-800">
                        <p className="text-[10px] text-dark-400 truncate">{uploadedFile?.name}</p>
                      </div>
                    </div>
                  )}

                  {/* Timeline Items */}
                  <div className="relative">
                    <div className="absolute left-4 top-0 bottom-0 w-px bg-dark-700/50" />
                    <div className="space-y-1">
                      {toolProgress.map((tool, index) => {
                        const meta = getToolMeta(tool.tool_key)
                        return (
                          <motion.div
                            key={tool.tool_key}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className="relative flex items-start gap-3 pl-1 py-2"
                          >
                            <div className={`relative z-10 w-7 h-7 rounded-lg flex items-center justify-center ${
                              tool.status === 'completed' ? 'bg-green-500/10' :
                              tool.status === 'running' ? 'bg-amber-500/10' :
                              tool.status === 'failed' ? 'bg-red-500/10' :
                              'bg-dark-800'
                            }`}>
                              {tool.status === 'running' ? (
                                <Loader2 className="w-3.5 h-3.5 text-amber-400 animate-spin" />
                              ) : tool.status === 'completed' ? (
                                <CheckCircle className="w-3.5 h-3.5 text-green-400" />
                              ) : tool.status === 'failed' ? (
                                <XCircle className="w-3.5 h-3.5 text-red-400" />
                              ) : (
                                <Clock className="w-3.5 h-3.5 text-dark-500" />
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-medium text-dark-200 truncate">{meta.label}</p>
                              <div className="flex items-center gap-2 mt-0.5">
                                {tool.execution_time_ms && (
                                  <span className="text-[10px] text-dark-500">{tool.execution_time_ms}ms</span>
                                )}
                                {tool.confidence != null && (
                                  <span className="text-[10px] text-dark-500">
                                    {(tool.confidence * 100).toFixed(0)}%
                                  </span>
                                )}
                              </div>
                            </div>
                          </motion.div>
                        )
                      })}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}

// ─── Sub-Components ────────────────────────────────────────────────────────────

function MessageBubble({
  message,
  expandedReportSections,
  toggleReportSection,
  copyToClipboard,
}: {
  message: Message
  expandedReportSections: Set<string>
  toggleReportSection: (s: string) => void
  copyToClipboard: (t: string) => void
}) {
  const isUser = message.role === 'user'
  const isReport = !isUser && message.content.includes('## ')

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
        isUser
          ? 'bg-primary-500/20'
          : 'bg-gradient-to-br from-primary-500/20 to-purple-500/20'
      }`}>
        {isUser ? (
          <User className="w-4 h-4 text-primary-300" />
        ) : (
          <Bot className="w-4 h-4 text-primary-400" />
        )}
      </div>

      {/* Content */}
      <div className={`max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Attachment preview */}
        {message.attachments && message.attachments.length > 0 && (
          <div className={`mb-2 rounded-2xl overflow-hidden border border-dark-700/50 ${isUser ? 'rounded-tr-md' : 'rounded-tl-md'}`}>
            {message.attachments[0]?.preview_url && (
              <img
                src={message.attachments[0].preview_url}
                alt="Evidence"
                className="w-full max-w-xs h-40 object-cover"
              />
            )}
            <div className="flex items-center gap-2 px-3 py-2 bg-dark-800">
              <FileImage className="w-3.5 h-3.5 text-primary-400" />
              <span className="text-xs text-dark-200 truncate">{message.attachments[0]?.original_filename}</span>
              {message.attachments[0]?.classification && (
                <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-primary-500/10 text-primary-400 border border-primary-500/20">
                  {message.attachments[0].classification.type}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Message bubble */}
        <div className={`rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-primary-600 text-white rounded-tr-md'
            : 'bg-dark-800 border border-dark-700/50 text-dark-200 rounded-tl-md'
        }`}>
          {isReport ? (
            <InvestigationReport
              content={message.content}
              expandedSections={expandedReportSections}
              toggleSection={toggleReportSection}
              copyToClipboard={copyToClipboard}
            />
          ) : (
            <div className="text-sm leading-relaxed prose prose-invert prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Timestamp */}
        <p className={`text-[10px] text-dark-500 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
          {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </motion.div>
  )
}

function ToolCard({
  tool,
  index,
  isExpanded,
  onToggle,
  copyToClipboard,
}: {
  tool: ToolProgress
  index: number
  isExpanded: boolean
  onToggle: () => void
  copyToClipboard: (t: string) => void
}) {
  const meta = getToolMeta(tool.tool_key)
  const Icon = meta.icon

  const statusConfig = {
    completed: { bg: 'bg-green-500/10', border: 'border-green-500/20', text: 'text-green-400', label: 'Completed' },
    running: { bg: 'bg-amber-500/10', border: 'border-amber-500/20', text: 'text-amber-400', label: 'Running' },
    failed: { bg: 'bg-red-500/10', border: 'border-red-500/20', text: 'text-red-400', label: 'Failed' },
    pending: { bg: 'bg-dark-800', border: 'border-dark-700/50', text: 'text-dark-500', label: 'Queued' },
  }
  const status = statusConfig[tool.status]

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className={`rounded-xl border ${status.border} ${status.bg} overflow-hidden transition-all duration-200 hover:shadow-lg`}
    >
      {/* Card Header */}
      <div
        className="flex items-center gap-3 px-4 py-3 cursor-pointer"
        onClick={onToggle}
      >
        <div className={`w-9 h-9 rounded-lg ${meta.bgColor} flex items-center justify-center`}>
          {tool.status === 'running' ? (
            <Loader2 className={`w-4 h-4 ${meta.color} animate-spin`} />
          ) : (
            <Icon className={`w-4 h-4 ${meta.color}`} />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-white">{meta.label}</p>
          <div className="flex items-center gap-2 mt-0.5">
            <span className={`text-[10px] font-medium ${status.text}`}>{status.label}</span>
            {tool.execution_time_ms && (
              <span className="text-[10px] text-dark-500">{tool.execution_time_ms}ms</span>
            )}
          </div>
        </div>
        {tool.confidence != null && (
          <div className="text-right">
            <p className="text-xs font-bold text-white">{(tool.confidence * 100).toFixed(0)}%</p>
            <p className="text-[10px] text-dark-500">confidence</p>
          </div>
        )}
        <ChevronDown className={`w-4 h-4 text-dark-500 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`} />
      </div>

      {/* Expanded Content */}
      <AnimatePresence>
        {isExpanded && tool.output && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-3 border-t border-dark-700/30 pt-3">
              <ToolOutputContent tool={tool} copyToClipboard={copyToClipboard} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function sanitizeOutput(val: unknown): unknown {
  if (typeof val === 'string') {
    if (/^\/(data|uploads|tmp|var|storage|mnt|app|home|root)\//.test(val)) {
      const filename = val.split('/').pop() || 'file'
      return `[Evidence File: ${filename}]`
    }
    return val
  }
  if (Array.isArray(val)) return val.map(sanitizeOutput)
  if (val && typeof val === 'object') {
    const sanitized: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(val as Record<string, unknown>)) {
      if (k === 'file_path' || k === 'image_path' || k === 'output_path') {
        sanitized[k] = '[secured]'
      } else {
        sanitized[k] = sanitizeOutput(v)
      }
    }
    return sanitized
  }
  return val
}

function ToolOutputContent({ tool, copyToClipboard }: { tool: ToolProgress; copyToClipboard: (t: string) => void }) {
  const output = tool.output
  if (!output) return null

  switch (tool.tool_key) {
    case 'image_ocr':
    case 'document_ocr':
      return (
        <div className="space-y-2">
          {output.text && (
            <div className="relative">
              <div className="bg-dark-900 rounded-lg p-3 text-xs text-dark-200 font-mono max-h-32 overflow-y-auto border border-dark-700/30">
                {output.text.slice(0, 500)}
                {output.text.length > 500 && '...'}
              </div>
              <button
                onClick={() => copyToClipboard(output.text)}
                className="absolute top-2 right-2 p-1.5 rounded-md bg-dark-800 hover:bg-dark-700 transition-colors"
              >
                <Copy className="w-3 h-3 text-dark-400" />
              </button>
            </div>
          )}
          <div className="flex items-center gap-3 text-[10px] text-dark-500">
            {output.char_count && <span>{output.char_count} characters</span>}
            {output.regions_detected && <span>{output.regions_detected} regions</span>}
            {output.method && <span className="px-1.5 py-0.5 rounded bg-dark-800">{output.method}</span>}
          </div>
        </div>
      )

    case 'license_plate_ocr':
      return (
        <div className="space-y-2">
          {output.plates?.map((plate: any, i: number) => (
            <div key={i} className="flex items-center gap-3 p-2.5 bg-dark-900 rounded-lg border border-dark-700/30">
              <div className="w-8 h-8 rounded-lg bg-yellow-500/10 flex items-center justify-center">
                <CreditCard className="w-4 h-4 text-yellow-400" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-bold text-white font-mono tracking-wider">{plate.text}</p>
                <p className="text-[10px] text-dark-500">{plate.method} {plate.confidence && `• ${(plate.confidence * 100).toFixed(0)}% confidence`}</p>
              </div>
            </div>
          ))}
          {output.plates_detected === 0 && (
            <p className="text-xs text-dark-500 italic">No plates detected</p>
          )}
        </div>
      )

    case 'face_detect':
      return (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs text-dark-300">
            <Eye className="w-3.5 h-3.5 text-pink-400" />
            <span>{output.faces_detected || 0} face(s) detected</span>
          </div>
          {output.faces?.map((face: any, i: number) => (
            <div key={i} className="flex items-center gap-3 p-2 bg-dark-900 rounded-lg border border-dark-700/30">
              <div className="w-7 h-7 rounded-full bg-pink-500/10 flex items-center justify-center">
                <span className="text-xs text-pink-400 font-bold">{face.face_id}</span>
              </div>
              <div className="flex-1 flex items-center gap-3 text-[10px] text-dark-400">
                {face.confidence && <span>Conf: {(face.confidence * 100).toFixed(0)}%</span>}
                {face.age && <span>Age: ~{face.age}</span>}
                {face.gender && <span>{face.gender}</span>}
              </div>
            </div>
          ))}
        </div>
      )

    case 'face_recognize':
      return (
        <div className="space-y-2">
          {output.matches?.map((match: any, i: number) => (
            <div key={i} className="p-2.5 bg-dark-900 rounded-lg border border-red-500/20">
              <div className="flex items-center gap-2">
                <Skull className="w-4 h-4 text-red-400" />
                <span className="text-xs font-semibold text-white">{match.criminal_name || match.full_name}</span>
                {match.wanted_status && (
                  <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20">
                    {match.wanted_status}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3 mt-1.5 text-[10px] text-dark-400">
                <span>Similarity: {(match.similarity * 100).toFixed(1)}%</span>
                {match.danger_level && <span>Danger: {match.danger_level}</span>}
              </div>
            </div>
          ))}
          {(!output.matches || output.matches.length === 0) && (
            <p className="text-xs text-dark-500 italic">No criminal matches found</p>
          )}
        </div>
      )

    case 'fingerprint_match':
      return (
        <div className="space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <DataBadge label="Minutiae" value={output.minutiae_extracted?.toString() || '0'} />
            <DataBadge label="Quality" value={output.quality_assessment || 'N/A'} />
          </div>
          {output.matches?.map((match: any, i: number) => (
            <div key={i} className="p-2.5 bg-dark-900 rounded-lg border border-purple-500/20">
              <div className="flex items-center gap-2">
                <Fingerprint className="w-4 h-4 text-purple-400" />
                <span className="text-xs font-semibold text-white">{match.criminal_name}</span>
                <span className="ml-auto text-xs font-bold text-purple-400">
                  {(match.similarity * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )

    case 'dna_search':
      return (
        <div className="space-y-2">
          {output.extracted_profile && (
            <div className="text-[10px] text-dark-400">
              Profile ID: {output.extracted_profile.dna_id || 'Extracted'}
            </div>
          )}
          {output.matches?.map((match: any, i: number) => (
            <div key={i} className="p-2.5 bg-dark-900 rounded-lg border border-green-500/20">
              <div className="flex items-center gap-2">
                <Dna className="w-4 h-4 text-green-400" />
                <span className="text-xs font-semibold text-white">{match.criminal_name}</span>
                <span className="ml-auto text-xs font-bold text-green-400">
                  {(match.similarity * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          ))}
          {(!output.matches || output.matches.length === 0) && (
            <p className="text-xs text-dark-500 italic">No DNA matches in criminal database</p>
          )}
        </div>
      )

    case 'vehicle_detect':
      return (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-1.5">
            {output.vehicles?.map((v: any, i: number) => (
              <span key={i} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-sky-500/10 border border-sky-500/20 text-xs text-sky-400">
                <Car className="w-3 h-3" />
                {v.type} {v.color && `(${v.color})`}
                <span className="text-[10px] text-dark-500 ml-1">{(v.confidence * 100).toFixed(0)}%</span>
              </span>
            ))}
          </div>
          {output.vehicles_detected === 0 && (
            <p className="text-xs text-dark-500 italic">No vehicles detected</p>
          )}
        </div>
      )

    case 'weapon_detect':
      return (
        <div className="space-y-2">
          {output.weapons_detected > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {output.weapons?.map((w: any, i: number) => (
                <span key={i} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400">
                  <Crosshair className="w-3 h-3" />
                  {w.class}
                  <span className="text-[10px] text-dark-500 ml-1">{(w.confidence * 100).toFixed(0)}%</span>
                </span>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-xs text-green-400">
              <Shield className="w-3.5 h-3.5" />
              <span>No weapons detected</span>
            </div>
          )}
        </div>
      )

    case 'image_object_detect':
      return (
        <div className="flex flex-wrap gap-1.5">
          {output.objects?.map((obj: any, i: number) => (
            <span key={i} className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-300">
              {obj.class}
              <span className="text-[10px] text-dark-500">{(obj.confidence * 100).toFixed(0)}%</span>
            </span>
          ))}
          {output.gemini_objects?.map((obj: any, i: number) => (
            <span key={`g-${i}`} className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-purple-500/10 border border-purple-500/20 text-[11px] text-purple-300">
              {obj.class}
              <Globe className="w-2.5 h-2.5 text-purple-500" />
            </span>
          ))}
          {output.objects_detected === 0 && (
            <p className="text-xs text-dark-500 italic">No objects detected</p>
          )}
        </div>
      )

    case 'image_exif':
      return (
        <div className="grid grid-cols-2 gap-2">
          {output.camera_make && <DataBadge label="Camera" value={`${output.camera_make} ${output.camera_model || ''}`} />}
          {output.gps_latitude && <DataBadge label="GPS" value={`${output.gps_latitude?.toFixed(4)}, ${output.gps_longitude?.toFixed(4)}`} />}
          {output.datetime_original && <DataBadge label="Taken" value={output.datetime_original} />}
          {output.image_width && <DataBadge label="Resolution" value={`${output.image_width}x${output.image_height}`} />}
        </div>
      )

    case 'digital_hash':
      return (
        <div className="space-y-2">
          {['sha256', 'md5', 'sha1'].map(algo => output[algo] && (
            <div key={algo} className="flex items-center gap-2 p-2 bg-dark-900 rounded-lg border border-dark-700/30">
              <Lock className="w-3 h-3 text-emerald-400 flex-shrink-0" />
              <span className="text-[10px] text-dark-500 uppercase w-10">{algo}</span>
              <span className="text-[10px] text-dark-300 font-mono truncate flex-1">{output[algo]}</span>
              <button onClick={() => copyToClipboard(output[algo])} className="p-1 rounded hover:bg-dark-700">
                <Copy className="w-3 h-3 text-dark-500" />
              </button>
            </div>
          ))}
        </div>
      )

    case 'audio_transcribe':
      return (
        <div className="space-y-2">
          {output.text && (
            <div className="relative bg-dark-900 rounded-lg p-3 border border-dark-700/30">
              <p className="text-xs text-dark-200 max-h-28 overflow-y-auto">{output.text.slice(0, 500)}</p>
              <button
                onClick={() => copyToClipboard(output.text)}
                className="absolute top-2 right-2 p-1.5 rounded-md bg-dark-800 hover:bg-dark-700"
              >
                <Copy className="w-3 h-3 text-dark-400" />
              </button>
            </div>
          )}
          <div className="flex items-center gap-3 text-[10px] text-dark-500">
            {output.language_detected && <span>Language: {output.language_detected}</span>}
            {output.duration_seconds && <span>Duration: {output.duration_seconds}s</span>}
          </div>
        </div>
      )

    case 'crime_scene_analysis':
      return (
        <div className="space-y-2">
          {output.ai_report && (
            <div className="bg-dark-900 rounded-lg p-3 border border-dark-700/30 max-h-40 overflow-y-auto">
              <div className="text-xs text-dark-200 prose prose-invert prose-xs max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{output.ai_report.slice(0, 600)}</ReactMarkdown>
              </div>
            </div>
          )}
          {output.pipeline_results && (
            <div className="grid grid-cols-3 gap-1.5">
              <MiniStat label="Objects" value={output.pipeline_results.objects?.count || 0} color="text-amber-400" />
              <MiniStat label="Faces" value={output.pipeline_results.faces?.count || 0} color="text-pink-400" />
              <MiniStat label="Weapons" value={output.pipeline_results.weapons?.count || 0} color="text-red-400" />
            </div>
          )}
        </div>
      )

    default:
      return (
        <div className="bg-dark-900 rounded-lg p-3 border border-dark-700/30">
          <pre className="text-[10px] text-dark-400 font-mono max-h-28 overflow-auto whitespace-pre-wrap">
            {JSON.stringify(sanitizeOutput(output), null, 2).slice(0, 400)}
          </pre>
        </div>
      )
  }
}

function DataBadge({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg border border-dark-700/30">
      <p className="text-[10px] text-dark-500">{label}</p>
      <p className="text-xs text-dark-200 font-medium truncate">{value}</p>
    </div>
  )
}

function MiniStat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="text-center p-1.5 bg-dark-900 rounded-lg border border-dark-700/30">
      <p className={`text-sm font-bold ${color}`}>{value}</p>
      <p className="text-[9px] text-dark-500">{label}</p>
    </div>
  )
}

function CriminalMatchesSection({ matches }: { matches: any[] }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-red-500/20 bg-gradient-to-b from-red-500/5 to-transparent overflow-hidden"
    >
      <div className="flex items-center gap-3 px-5 py-4 border-b border-red-500/10">
        <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
          <AlertTriangle className="w-5 h-5 text-red-400" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-red-400">Criminal Intelligence Matches</h3>
          <p className="text-[10px] text-dark-500">{matches.length} suspect(s) identified in database</p>
        </div>
        <div className="ml-auto px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20">
          <span className="text-xs font-bold text-red-400">ALERT</span>
        </div>
      </div>
      <div className="p-4 space-y-3">
        {matches.map((match, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className="flex items-center gap-4 p-4 rounded-xl bg-dark-800 border border-dark-700/50 hover:border-red-500/30 transition-colors"
          >
            <div className="w-12 h-12 rounded-xl bg-dark-750 flex items-center justify-center border border-dark-700/50">
              <Skull className="w-6 h-6 text-red-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="text-sm font-bold text-white">{match.name || match.criminal_name}</p>
                {match.danger_level && (
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                    match.danger_level === 'high' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                    match.danger_level === 'medium' ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20' :
                    'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                  }`}>
                    {match.danger_level}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3 mt-1 text-xs text-dark-400">
                <span>ID: {match.criminal_id}</span>
                <span className="w-1 h-1 rounded-full bg-dark-600" />
                <span>{match.match_type} match</span>
                {match.similarity && (
                  <>
                    <span className="w-1 h-1 rounded-full bg-dark-600" />
                    <span className="text-red-400 font-medium">{(match.similarity * 100).toFixed(1)}%</span>
                  </>
                )}
              </div>
            </div>
            {match.wanted_status && (
              <span className="px-3 py-1.5 rounded-lg bg-red-500/10 text-red-400 text-xs font-bold border border-red-500/20">
                {match.wanted_status}
              </span>
            )}
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

function InvestigationReport({
  content,
  expandedSections,
  toggleSection,
  copyToClipboard,
}: {
  content: string
  expandedSections: Set<string>
  toggleSection: (s: string) => void
  copyToClipboard: (t: string) => void
}) {
  const sections = useMemo(() => {
    const parts: { title: string; key: string; content: string; icon: any }[] = []
    const lines = content.split('\n')
    let currentTitle = ''
    let currentContent: string[] = []
    let currentKey = ''

    const iconMap: Record<string, any> = {
      'executive': Brain,
      'summary': FileText,
      'evidence': Search,
      'findings': Target,
      'objects': Target,
      'persons': User,
      'criminal': Skull,
      'vehicle': Car,
      'weapon': Crosshair,
      'recommend': CheckCircle,
      'legal': Scale,
      'scene': MapPin,
      'environmental': Globe,
      'safety': Shield,
      'threat': AlertTriangle,
    }

    function getIcon(title: string) {
      const lower = title.toLowerCase()
      for (const [key, icon] of Object.entries(iconMap)) {
        if (lower.includes(key)) return icon
      }
      return FileText
    }

    for (const line of lines) {
      if (line.startsWith('## ')) {
        if (currentTitle) {
          parts.push({ title: currentTitle, key: currentKey, content: currentContent.join('\n'), icon: getIcon(currentTitle) })
        }
        currentTitle = line.slice(3).trim()
        currentKey = currentTitle.toLowerCase().replace(/\s+/g, '-')
        currentContent = []
      } else {
        currentContent.push(line)
      }
    }
    if (currentTitle) {
      parts.push({ title: currentTitle, key: currentKey, content: currentContent.join('\n'), icon: getIcon(currentTitle) })
    }

    if (parts.length === 0) {
      parts.push({ title: 'Report', key: 'report', content, icon: FileText })
    }

    return parts
  }, [content])

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 pb-2 mb-2 border-b border-dark-700/30">
        <Scale className="w-4 h-4 text-purple-400" />
        <span className="text-xs font-bold text-white">Investigation Report</span>
        <button
          onClick={() => copyToClipboard(content)}
          className="ml-auto p-1.5 rounded-md hover:bg-dark-700 transition-colors"
          title="Copy full report"
        >
          <Copy className="w-3 h-3 text-dark-400" />
        </button>
      </div>
      {sections.map((section) => {
        const Icon = section.icon
        const isOpen = expandedSections.has(section.key)
        return (
          <div key={section.key} className="rounded-lg border border-dark-700/30 overflow-hidden">
            <button
              onClick={() => toggleSection(section.key)}
              className="w-full flex items-center gap-2.5 px-3 py-2.5 text-left hover:bg-dark-700/30 transition-colors"
            >
              <Icon className="w-3.5 h-3.5 text-primary-400 flex-shrink-0" />
              <span className="text-xs font-semibold text-dark-200 flex-1">{section.title}</span>
              <ChevronDown className={`w-3.5 h-3.5 text-dark-500 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
            </button>
            <AnimatePresence>
              {isOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="px-3 pb-3 text-xs text-dark-300 leading-relaxed prose prose-invert prose-xs max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{section.content.trim()}</ReactMarkdown>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )
      })}
    </div>
  )
}
