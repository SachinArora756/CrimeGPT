import { useState, useCallback, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import {
  ArrowLeft, Upload, Loader2, CheckCircle, XCircle,
  Microscope, Bookmark, Brain, Copy, Clock,
  FileImage, Shield, Activity, Zap, AlertTriangle,
  User, Fingerprint, Skull
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import api from '../../api/client'
import toast from 'react-hot-toast'

interface ExecutionResult {
  execution_id: string
  tool_key: string
  status: string
  input_filename: string | null
  output_data: Record<string, unknown> | null
  ai_summary: string | null
  confidence_score: number | null
  execution_time_ms: number | null
  created_at: string
  completed_at: string | null
  case_id: number | null
  evidence_id: number | null
}

export default function ToolExecutionPage() {
  const { toolKey, executionId } = useParams<{ toolKey?: string; executionId?: string }>()
  const navigate = useNavigate()
  const [files, setFiles] = useState<File[]>([])
  const [filePreviews, setFilePreviews] = useState<(string | null)[]>([])
  const [executing, setExecuting] = useState(false)
  const [result, setResult] = useState<ExecutionResult | null>(null)
  const [progress, setProgress] = useState(0)
  const [summarizing, setSummarizing] = useState(false)
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set())
  const [sceneContext, setSceneContext] = useState('')

  useEffect(() => {
    if (executionId) {
      api.get(`/api/forensic-toolkit/executions/${executionId}`)
        .then(res => setResult(res.data))
        .catch(() => toast.error('Execution not found'))
    }
  }, [executionId])

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFiles(prev => [...prev, ...acceptedFiles])
      setResult(null)
      const previews = acceptedFiles.map(f => f.type.startsWith('image/') ? URL.createObjectURL(f) : null)
      setFilePreviews(prev => [...prev, ...previews])
    }
  }, [])

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
    setFilePreviews(prev => prev.filter((_, i) => i !== index))
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    maxSize: 50 * 1024 * 1024,
  })

  const executeTask = async () => {
    if (!files.length || !toolKey) return
    setExecuting(true)
    setProgress(10)

    const interval = setInterval(() => {
      setProgress(p => Math.min(p + Math.random() * 15, 85))
    }, 500)

    try {
      const formData = new FormData()
      files.forEach(f => formData.append('file', f))
      const toolParams: Record<string, string> = {}
      if (sceneContext.trim() && toolKey === 'crime_scene_analysis') {
        toolParams.officer_notes = sceneContext.trim()
      }
      formData.append('params', JSON.stringify(toolParams))

      const response = await api.post(`/api/forensic-toolkit/execute/${toolKey}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setProgress(100)
      setResult(response.data)
      toast.success('Analysis complete')
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      toast.error(err.response?.data?.detail || 'Execution failed')
    } finally {
      clearInterval(interval)
      setExecuting(false)
      setProgress(0)
    }
  }

  const handleSummarize = async () => {
    if (!result) return
    setSummarizing(true)
    try {
      const response = await api.post(`/api/forensic-toolkit/executions/${result.execution_id}/summarize`)
      setResult(prev => prev ? { ...prev, ai_summary: response.data.ai_summary } : null)
      toast.success('AI summary generated')
    } catch {
      toast.error('Failed to generate summary')
    } finally {
      setSummarizing(false)
    }
  }

  const handleBookmark = async () => {
    if (!result) return
    try {
      await api.post('/api/forensic-toolkit/saved', {
        execution_id: result.execution_id,
        title: `${toolKey} - ${result.input_filename}`,
        notes: '',
      })
      toast.success('Result saved to bookmarks')
    } catch {
      toast.error('Failed to save')
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  const toggleExpand = (key: string) => {
    setExpandedKeys(prev => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const sanitizeValue = (val: unknown): unknown => {
    if (typeof val === 'string') {
      if (/^\/(data|uploads|tmp|var|storage|mnt|app|home|root)\//.test(val)) {
        const filename = val.split('/').pop() || 'file'
        return `[Evidence File: ${filename}]`
      }
      return val
    }
    if (Array.isArray(val)) return val.map(sanitizeValue)
    if (val && typeof val === 'object') {
      const sanitized: Record<string, unknown> = {}
      for (const [k, v] of Object.entries(val as Record<string, unknown>)) {
        if (k === 'file_path' || k === 'image_path' || k === 'output_path') {
          sanitized[k] = '[secured]'
        } else {
          sanitized[k] = sanitizeValue(v)
        }
      }
      return sanitized
    }
    return val
  }

  const renderOutputValue = (key: string, value: unknown) => {
    const isExpanded = expandedKeys.has(key)
    const displayValue = sanitizeValue(value)

    if (typeof displayValue === 'string') {
      const isLong = displayValue.length > 200
      return (
        <div className="relative group">
          <div className="bg-dark-900 rounded-lg p-3 border border-dark-700/30">
            <p className="text-sm text-dark-200 whitespace-pre-wrap break-words font-mono">
              {isLong && !isExpanded ? displayValue.slice(0, 200) + '...' : displayValue}
            </p>
            {isLong && (
              <button
                onClick={() => toggleExpand(key)}
                className="mt-2 text-xs text-primary-400 hover:text-primary-300"
              >
                {isExpanded ? 'Show less' : 'Show all'}
              </button>
            )}
          </div>
          <button
            onClick={() => copyToClipboard(String(displayValue))}
            className="absolute top-2 right-2 p-1.5 rounded-md bg-dark-800 hover:bg-dark-700 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <Copy className="w-3 h-3 text-dark-400" />
          </button>
        </div>
      )
    }

    if (Array.isArray(displayValue)) {
      return (
        <div className="space-y-1.5">
          {(displayValue as unknown[]).slice(0, isExpanded ? undefined : 10).map((item, i) => (
            <div key={i} className="px-3 py-2 bg-dark-900 rounded-lg border border-dark-700/30">
              <p className="text-xs text-dark-200 font-mono">
                {typeof item === 'object' ? JSON.stringify(item) : String(item)}
              </p>
            </div>
          ))}
          {(displayValue as unknown[]).length > 10 && (
            <button
              onClick={() => toggleExpand(key)}
              className="text-xs text-primary-400 hover:text-primary-300 px-3"
            >
              {isExpanded ? 'Show less' : `Show all ${(displayValue as unknown[]).length} items`}
            </button>
          )}
        </div>
      )
    }

    if (typeof displayValue === 'object' && displayValue !== null) {
      const json = JSON.stringify(displayValue, null, 2)
      return (
        <div className="relative group">
          <pre className="bg-dark-900 rounded-lg p-3 border border-dark-700/30 text-xs text-dark-200 overflow-x-auto max-h-48 font-mono">
            {json}
          </pre>
          <button
            onClick={() => copyToClipboard(json)}
            className="absolute top-2 right-2 p-1.5 rounded-md bg-dark-800 hover:bg-dark-700 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <Copy className="w-3 h-3 text-dark-400" />
          </button>
        </div>
      )
    }

    return <p className="text-sm text-white px-3 py-2 bg-dark-900 rounded-lg border border-dark-700/30">{String(displayValue)}</p>
  }

  const BIOMETRIC_TOOLS = ['face_recognize', 'fingerprint_match', 'dna_search']

  const getDangerColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'extreme': return 'text-red-400 bg-red-500/10 border-red-500/30'
      case 'high': return 'text-orange-400 bg-orange-500/10 border-orange-500/30'
      case 'medium': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30'
      default: return 'text-green-400 bg-green-500/10 border-green-500/30'
    }
  }

  const getWantedColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'most_wanted': return 'text-red-400 bg-red-500/10 border-red-500/30'
      case 'wanted': case 'absconding': return 'text-orange-400 bg-orange-500/10 border-orange-500/30'
      case 'arrested': return 'text-blue-400 bg-blue-500/10 border-blue-500/30'
      case 'surrendered': return 'text-green-400 bg-green-500/10 border-green-500/30'
      default: return 'text-dark-400 bg-dark-700/50 border-dark-600/30'
    }
  }

  const TOOL_STYLES: Record<string, { border: string; gradient: string; iconBg: string; iconText: string; scoreText: string }> = {
    face_recognize: {
      border: 'border-red-500/30',
      gradient: 'bg-gradient-to-r from-red-500/5 to-transparent',
      iconBg: 'bg-red-500/10',
      iconText: 'text-red-400',
      scoreText: 'text-red-400',
    },
    fingerprint_match: {
      border: 'border-purple-500/30',
      gradient: 'bg-gradient-to-r from-purple-500/5 to-transparent',
      iconBg: 'bg-purple-500/10',
      iconText: 'text-purple-400',
      scoreText: 'text-purple-400',
    },
    dna_search: {
      border: 'border-green-500/30',
      gradient: 'bg-gradient-to-r from-green-500/5 to-transparent',
      iconBg: 'bg-green-500/10',
      iconText: 'text-green-400',
      scoreText: 'text-green-400',
    },
  }

  const renderCriminalProfileCard = (match: Record<string, unknown>, index: number) => {
    const profile = match.criminal_profile as Record<string, string | number | string[] | null | undefined> | undefined
    const similarity = (match.similarity as number) * 100

    const styles = TOOL_STYLES[toolKey || ''] || TOOL_STYLES.face_recognize

    return (
      <div key={index} className={`rounded-xl bg-dark-800/80 border ${styles.border} overflow-hidden`}>
        {/* Match Header */}
        <div className={`px-4 py-3 ${styles.gradient} border-b border-dark-700/30`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-9 h-9 rounded-lg ${styles.iconBg} flex items-center justify-center`}>
                <Skull className={`w-5 h-5 ${styles.iconText}`} />
              </div>
              <div>
                <h5 className="text-sm font-bold text-white">
                  {String(match.criminal_name || profile?.profile_full_name || 'Unknown')}
                </h5>
                <p className="text-[10px] text-dark-400">ID: {String(match.criminal_id || 'N/A')}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-lg font-bold ${styles.scoreText}`}>
                {similarity.toFixed(1)}%
              </span>
              <span className="text-[10px] text-dark-500">match</span>
            </div>
          </div>

          {/* Status badges */}
          <div className="flex items-center gap-2 mt-2">
            {!!match.wanted_status && String(match.wanted_status) !== 'not_wanted' && (
              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold border ${getWantedColor(String(match.wanted_status))}`}>
                <AlertTriangle className="w-3 h-3" />
                {String(match.wanted_status).replace(/_/g, ' ').toUpperCase()}
              </span>
            )}
            {!!(match.danger_level || profile?.danger_level) && (
              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold border ${getDangerColor(String(match.danger_level || profile?.danger_level))}`}>
                {'Danger: '}{String(match.danger_level || profile?.danger_level).toUpperCase()}
              </span>
            )}
            {!!profile?.reward_amount && Number(profile.reward_amount) > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold border text-yellow-400 bg-yellow-500/10 border-yellow-500/30">
                {'Reward: ₹'}{Number(profile.reward_amount).toLocaleString()}
              </span>
            )}
          </div>
        </div>

        {/* Profile Details */}
        {profile && (
          <div className="p-4 space-y-4">
            {/* Personal Information */}
            <div>
              <h6 className="text-[10px] text-dark-500 uppercase font-semibold tracking-wide mb-2">Personal Information</h6>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {profile.father_name && (
                  <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                    <p className="text-[9px] text-dark-500">Father's Name</p>
                    <p className="text-xs text-white">{String(profile.father_name)}</p>
                  </div>
                )}
                {profile.gender && (
                  <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                    <p className="text-[9px] text-dark-500">Gender</p>
                    <p className="text-xs text-white capitalize">{String(profile.gender)}</p>
                  </div>
                )}
                {profile.date_of_birth && (
                  <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                    <p className="text-[9px] text-dark-500">Date of Birth</p>
                    <p className="text-xs text-white">{String(profile.date_of_birth)}</p>
                  </div>
                )}
                {profile.nationality && (
                  <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                    <p className="text-[9px] text-dark-500">Nationality</p>
                    <p className="text-xs text-white">{String(profile.nationality)}</p>
                  </div>
                )}
                {profile.occupation && (
                  <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                    <p className="text-[9px] text-dark-500">Occupation</p>
                    <p className="text-xs text-white">{String(profile.occupation)}</p>
                  </div>
                )}
                {profile.education && (
                  <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                    <p className="text-[9px] text-dark-500">Education</p>
                    <p className="text-xs text-white">{String(profile.education)}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Physical Description */}
            {(profile.height_cm || profile.weight_kg || profile.complexion || profile.build) && (
              <div>
                <h6 className="text-[10px] text-dark-500 uppercase font-semibold tracking-wide mb-2">Physical Description</h6>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {profile.height_cm && (
                    <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                      <p className="text-[9px] text-dark-500">Height</p>
                      <p className="text-xs text-white">{String(profile.height_cm)} cm</p>
                    </div>
                  )}
                  {profile.weight_kg && (
                    <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                      <p className="text-[9px] text-dark-500">Weight</p>
                      <p className="text-xs text-white">{String(profile.weight_kg)} kg</p>
                    </div>
                  )}
                  {profile.build && (
                    <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                      <p className="text-[9px] text-dark-500">Build</p>
                      <p className="text-xs text-white capitalize">{String(profile.build)}</p>
                    </div>
                  )}
                  {profile.complexion && (
                    <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                      <p className="text-[9px] text-dark-500">Complexion</p>
                      <p className="text-xs text-white capitalize">{String(profile.complexion)}</p>
                    </div>
                  )}
                  {profile.hair_color && (
                    <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                      <p className="text-[9px] text-dark-500">Hair Color</p>
                      <p className="text-xs text-white capitalize">{String(profile.hair_color)}</p>
                    </div>
                  )}
                  {profile.eye_color && (
                    <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                      <p className="text-[9px] text-dark-500">Eye Color</p>
                      <p className="text-xs text-white capitalize">{String(profile.eye_color)}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Identifying Marks */}
            {profile.identifying_marks && (Array.isArray(profile.identifying_marks) ? (profile.identifying_marks as unknown[]).length > 0 : true) && (
              <div>
                <h6 className="text-[10px] text-dark-500 uppercase font-semibold tracking-wide mb-2">Identifying Marks</h6>
                <div className="flex flex-wrap gap-1.5">
                  {(Array.isArray(profile.identifying_marks)
                    ? (profile.identifying_marks as string[])
                    : [String(profile.identifying_marks)]
                  ).map((mark, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[10px] text-amber-400">
                      {mark}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Criminal History */}
            {(profile.total_arrests || profile.total_firs || profile.total_convictions) && (
              <div>
                <h6 className="text-[10px] text-dark-500 uppercase font-semibold tracking-wide mb-2">Criminal History</h6>
                <div className="grid grid-cols-3 gap-2">
                  <div className="px-2.5 py-2 bg-dark-900 rounded-lg text-center">
                    <p className="text-lg font-bold text-red-400">{String(profile.total_arrests || 0)}</p>
                    <p className="text-[9px] text-dark-500">Arrests</p>
                  </div>
                  <div className="px-2.5 py-2 bg-dark-900 rounded-lg text-center">
                    <p className="text-lg font-bold text-orange-400">{String(profile.total_firs || 0)}</p>
                    <p className="text-[9px] text-dark-500">FIRs</p>
                  </div>
                  <div className="px-2.5 py-2 bg-dark-900 rounded-lg text-center">
                    <p className="text-lg font-bold text-yellow-400">{String(profile.total_convictions || 0)}</p>
                    <p className="text-[9px] text-dark-500">Convictions</p>
                  </div>
                </div>
              </div>
            )}

            {/* Crime Categories */}
            {profile.crime_categories && (Array.isArray(profile.crime_categories) ? (profile.crime_categories as unknown[]).length > 0 : true) && (
              <div>
                <h6 className="text-[10px] text-dark-500 uppercase font-semibold tracking-wide mb-2">Crime Categories</h6>
                <div className="flex flex-wrap gap-1.5">
                  {(Array.isArray(profile.crime_categories)
                    ? (profile.crime_categories as string[])
                    : [String(profile.crime_categories)]
                  ).map((cat, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-lg bg-red-500/10 border border-red-500/20 text-[10px] text-red-400">
                      {cat}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Modus Operandi */}
            {profile.modus_operandi && (
              <div>
                <h6 className="text-[10px] text-dark-500 uppercase font-semibold tracking-wide mb-2">Modus Operandi</h6>
                <p className="text-xs text-dark-200 bg-dark-900 rounded-lg px-3 py-2 leading-relaxed">
                  {String(profile.modus_operandi)}
                </p>
              </div>
            )}

            {/* Gang Information */}
            {(profile.gang_name || profile.gang_role) && (
              <div>
                <h6 className="text-[10px] text-dark-500 uppercase font-semibold tracking-wide mb-2">Gang Information</h6>
                <div className="grid grid-cols-2 gap-2">
                  {profile.gang_name && (
                    <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                      <p className="text-[9px] text-dark-500">Gang Name</p>
                      <p className="text-xs text-white">{String(profile.gang_name)}</p>
                    </div>
                  )}
                  {profile.gang_role && (
                    <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                      <p className="text-[9px] text-dark-500">Role</p>
                      <p className="text-xs text-white capitalize">{String(profile.gang_role)}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Known Weapons */}
            {profile.known_weapons && (Array.isArray(profile.known_weapons) ? (profile.known_weapons as unknown[]).length > 0 : true) && (
              <div>
                <h6 className="text-[10px] text-dark-500 uppercase font-semibold tracking-wide mb-2">Known Weapons</h6>
                <div className="flex flex-wrap gap-1.5">
                  {(Array.isArray(profile.known_weapons)
                    ? (profile.known_weapons as string[])
                    : [String(profile.known_weapons)]
                  ).map((weapon, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-lg bg-orange-500/10 border border-orange-500/20 text-[10px] text-orange-400">
                      {weapon}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Additional Info */}
            {(profile.bail_status || profile.last_known_activity || profile.first_offense_date) && (
              <div>
                <h6 className="text-[10px] text-dark-500 uppercase font-semibold tracking-wide mb-2">Additional Information</h6>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {profile.bail_status && (
                    <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                      <p className="text-[9px] text-dark-500">Bail Status</p>
                      <p className="text-xs text-white capitalize">{String(profile.bail_status)}</p>
                    </div>
                  )}
                  {profile.first_offense_date && (
                    <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                      <p className="text-[9px] text-dark-500">First Offense</p>
                      <p className="text-xs text-white">{String(profile.first_offense_date)}</p>
                    </div>
                  )}
                  {profile.last_known_activity && (
                    <div className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                      <p className="text-[9px] text-dark-500">Last Activity</p>
                      <p className="text-xs text-white">{String(profile.last_known_activity)}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Fallback: show raw match data if no profile */}
        {!profile && (
          <div className="p-3">
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(match).filter(([k]) => k !== 'criminal_profile' && k !== 'criminal_name' && k !== 'similarity').map(([k, v]) => (
                <div key={k} className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                  <p className="text-[9px] text-dark-500">{k.replace(/_/g, ' ')}</p>
                  <p className="text-xs text-white">{String(v)}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderBiometricResults = () => {
    if (!result?.output_data || !toolKey || !BIOMETRIC_TOOLS.includes(toolKey)) return null

    const output = result.output_data as Record<string, unknown>
    const matches = output.matches as Record<string, unknown>[] | undefined

    return (
      <div className="space-y-4">
        {/* Match Summary Header */}
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-gradient-to-r from-dark-800 to-dark-800/50 border border-dark-700/50">
          <div className="w-10 h-10 rounded-xl bg-primary-500/10 flex items-center justify-center">
            {toolKey === 'face_recognize' && <User className="w-5 h-5 text-red-400" />}
            {toolKey === 'fingerprint_match' && <Fingerprint className="w-5 h-5 text-purple-400" />}
            {toolKey === 'dna_search' && <Shield className="w-5 h-5 text-green-400" />}
          </div>
          <div>
            <p className="text-sm font-bold text-white">
              {matches && matches.length > 0 ? `${matches.length} Match${matches.length > 1 ? 'es' : ''} Found` : 'No Matches Found'}
            </p>
            <p className="text-[10px] text-dark-400">
              Searched {String(output.database_records_searched || 0)} records in {String(output.database_searched || 'criminal database')}
            </p>
          </div>
          {result.confidence_score && (
            <div className="ml-auto text-right">
              <p className="text-lg font-bold text-primary-400">{(result.confidence_score * 100).toFixed(1)}%</p>
              <p className="text-[9px] text-dark-500">Top Match</p>
            </div>
          )}
        </div>

        {/* Match Cards */}
        {matches && matches.length > 0 && (
          <div className="space-y-3">
            {matches.map((match, i) => renderCriminalProfileCard(match, i))}
          </div>
        )}

        {(!matches || matches.length === 0) && (
          <div className="rounded-xl bg-dark-800/50 border border-dark-700/30 p-8 text-center">
            <Shield className="w-10 h-10 text-dark-600 mx-auto mb-3" />
            <p className="text-sm text-dark-400">No matches found in the criminal database</p>
            <p className="text-[10px] text-dark-500 mt-1">The uploaded evidence did not match any existing records</p>
          </div>
        )}

        {/* Other output fields (method, execution time, etc.) */}
        <div className="space-y-2">
          <h4 className="text-[11px] text-dark-500 uppercase font-semibold tracking-wide">Technical Details</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {Object.entries(output)
              .filter(([key]) => !['matches', 'faces', 'input_template_summary', 'extracted_profile', 'text_preview'].includes(key))
              .map(([key, value]) => {
                if (typeof value === 'object' && value !== null) return null
                return (
                  <div key={key} className="px-2.5 py-1.5 bg-dark-900 rounded-lg">
                    <p className="text-[9px] text-dark-500">{key.replace(/_/g, ' ')}</p>
                    <p className="text-xs text-white truncate">{String(value)}</p>
                  </div>
                )
              })
              .filter(Boolean)}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/forensics/tools')}
          className="p-2.5 rounded-xl bg-dark-800 border border-dark-700/50 hover:bg-dark-700 hover:border-dark-600 text-dark-300 hover:text-white transition-all"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="relative">
          <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 blur-md" />
          <div className="relative w-12 h-12 rounded-xl bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center shadow-lg shadow-purple-500/20">
            <Microscope className="w-6 h-6 text-white" />
          </div>
        </div>
        <div>
          <h1 className="text-xl font-bold text-white capitalize">{toolKey?.replace(/_/g, ' ')}</h1>
          <p className="text-dark-400 text-xs">Upload evidence file and execute forensic analysis</p>
        </div>
        {result && (
          <div className="ml-auto flex items-center gap-2">
            <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium ${
              result.status === 'completed'
                ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                : 'bg-red-500/10 text-red-400 border border-red-500/20'
            }`}>
              {result.status === 'completed' ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
              {result.status}
            </span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left: Input Panel (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          {/* Dropzone */}
          <div
            {...getRootProps()}
            className={`relative rounded-2xl border-2 border-dashed transition-all duration-300 cursor-pointer overflow-hidden ${
              isDragActive ? 'border-primary-400 bg-primary-400/5 scale-[1.01]' :
              files.length ? 'border-green-500/30 bg-green-500/5' :
              'border-dark-600/50 hover:border-primary-500/30 hover:bg-dark-800/30'
            }`}
          >
            <input {...getInputProps()} />
            {files.length > 0 ? (
              <div className="p-4">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {files.map((f, idx) => (
                    <div key={idx} className="relative rounded-xl border border-dark-700/50 bg-dark-900/50 overflow-hidden group">
                      {filePreviews[idx] ? (
                        <img src={filePreviews[idx]!} alt={f.name} className="w-full h-24 object-cover" />
                      ) : (
                        <div className="w-full h-24 flex items-center justify-center bg-dark-800">
                          <CheckCircle className="w-6 h-6 text-green-400" />
                        </div>
                      )}
                      <div className="p-2">
                        <p className="text-[11px] text-white truncate">{f.name}</p>
                        <p className="text-[10px] text-dark-400">{(f.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                      <button
                        type="button"
                        onClick={e => { e.stopPropagation(); removeFile(idx) }}
                        className="absolute top-1 right-1 w-5 h-5 rounded-full bg-dark-900/80 text-dark-300 hover:text-red-400 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
                <p className="text-[10px] text-dark-500 mt-3 text-center">{files.length} file{files.length > 1 ? 's' : ''} selected — click or drop to add more</p>
              </div>
            ) : (
              <div className="p-10 text-center">
                <div className="w-14 h-14 mx-auto rounded-2xl bg-dark-800 border border-dark-700/50 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <Upload className="w-6 h-6 text-dark-400" />
                </div>
                <p className="text-sm text-dark-300 font-medium">Drop evidence files here</p>
                <p className="text-xs text-dark-500 mt-1.5">or click to browse (multiple files supported)</p>
                <div className="flex items-center justify-center gap-2 mt-4">
                  <span className="text-[10px] px-2 py-1 rounded bg-dark-800 text-dark-500 border border-dark-700/50">Max 50MB each</span>
                  <span className="text-[10px] px-2 py-1 rounded bg-dark-800 text-dark-500 border border-dark-700/50">Images, Audio, PDF</span>
                </div>
              </div>
            )}
          </div>

          {/* Officer Notes (Crime Scene Analysis only) */}
          {toolKey === 'crime_scene_analysis' && (
            <div className="rounded-xl border border-dark-700/50 bg-dark-800/30 p-4">
              <label className="text-sm font-medium text-dark-200 flex items-center gap-2 mb-2">
                <FileImage className="w-4 h-4 text-primary-400" />
                Officer's Scene Description (Optional)
              </label>
              <textarea
                className="w-full bg-dark-900/60 border border-dark-700/50 rounded-lg px-3 py-2.5 text-sm text-dark-200 placeholder-dark-500 focus:outline-none focus:border-primary-500/50 resize-none"
                rows={4}
                placeholder="Describe what you observed at the crime scene — e.g. type of incident, visible injuries, weapon found near the door, broken window on the east side, blood stains on the floor..."
                value={sceneContext}
                onChange={e => setSceneContext(e.target.value)}
                maxLength={3000}
              />
              <p className="text-[10px] text-dark-500 mt-1.5">Your notes help the AI provide more accurate analysis even if the image is unclear.</p>
            </div>
          )}

          {/* Execute Button */}
          <button
            onClick={executeTask}
            disabled={!files.length || executing}
            className="w-full flex items-center justify-center gap-2.5 py-3.5 rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white font-medium text-sm disabled:opacity-30 disabled:hover:from-primary-600 transition-all shadow-lg shadow-primary-500/20 disabled:shadow-none"
          >
            {executing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Processing Analysis...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4" />
                <span>Execute Analysis</span>
              </>
            )}
          </button>

          {/* Progress */}
          <AnimatePresence>
            {executing && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="rounded-xl bg-dark-800/80 border border-dark-700/50 p-4 overflow-hidden"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary-400 animate-pulse" />
                    <span className="text-xs text-dark-300">Running forensic pipeline...</span>
                  </div>
                  <span className="text-xs font-mono text-primary-400">{Math.round(progress)}%</span>
                </div>
                <div className="w-full h-2 bg-dark-700 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-primary-600 to-primary-400 rounded-full"
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
                <div className="mt-3 space-y-1.5">
                  {['Parsing file structure', 'Executing analysis algorithms', 'Processing results'].map((step, i) => (
                    <div key={step} className="flex items-center gap-2">
                      {progress > (i + 1) * 30 ? (
                        <CheckCircle className="w-3 h-3 text-green-400" />
                      ) : progress > i * 30 ? (
                        <Loader2 className="w-3 h-3 text-primary-400 animate-spin" />
                      ) : (
                        <Clock className="w-3 h-3 text-dark-600" />
                      )}
                      <span className={`text-[11px] ${progress > i * 30 ? 'text-dark-300' : 'text-dark-600'}`}>
                        {step}
                      </span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Quick Stats */}
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="grid grid-cols-3 gap-2"
            >
              <div className="rounded-xl bg-dark-800/80 border border-dark-700/50 p-3 text-center">
                <Activity className="w-4 h-4 mx-auto text-purple-400 mb-1" />
                <p className="text-xs font-bold text-white">
                  {result.execution_time_ms ? `${(result.execution_time_ms / 1000).toFixed(1)}s` : '—'}
                </p>
                <p className="text-[9px] text-dark-500">Duration</p>
              </div>
              <div className="rounded-xl bg-dark-800/80 border border-dark-700/50 p-3 text-center">
                <Shield className="w-4 h-4 mx-auto text-green-400 mb-1" />
                <p className="text-xs font-bold text-white">
                  {result.confidence_score != null ? `${Math.round(result.confidence_score * 100)}%` : '—'}
                </p>
                <p className="text-[9px] text-dark-500">Confidence</p>
              </div>
              <div className="rounded-xl bg-dark-800/80 border border-dark-700/50 p-3 text-center">
                <FileImage className="w-4 h-4 mx-auto text-blue-400 mb-1" />
                <p className="text-xs font-bold text-white truncate">{result.input_filename?.split('.').pop()?.toUpperCase() || '—'}</p>
                <p className="text-[9px] text-dark-500">Format</p>
              </div>
            </motion.div>
          )}
        </div>

        {/* Right: Results Panel (3 cols) */}
        <div className="lg:col-span-3">
          {result ? (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="space-y-4"
            >
              {/* Result Header Card */}
              <div className="rounded-xl bg-dark-800/80 border border-dark-700/50 p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                      result.status === 'completed' ? 'bg-green-500/10 border border-green-500/20' : 'bg-red-500/10 border border-red-500/20'
                    }`}>
                      {result.status === 'completed' ? (
                        <CheckCircle className="w-5 h-5 text-green-400" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-400" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-bold text-white capitalize">{result.status}</p>
                      <p className="text-[10px] text-dark-500">
                        {result.completed_at ? new Date(result.completed_at).toLocaleString() : new Date(result.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleSummarize}
                      disabled={summarizing}
                      className="flex items-center gap-1.5 px-3 py-2 text-xs bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 border border-purple-500/20 rounded-lg transition-colors disabled:opacity-50"
                    >
                      {summarizing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Brain className="w-3 h-3" />}
                      AI Summary
                    </button>
                    <button
                      onClick={handleBookmark}
                      className="flex items-center gap-1.5 px-3 py-2 text-xs bg-dark-700 hover:bg-dark-600 text-dark-200 rounded-lg transition-colors border border-dark-600/50"
                    >
                      <Bookmark className="w-3 h-3" /> Save
                    </button>
                  </div>
                </div>

                {/* Metadata Row */}
                <div className="flex items-center gap-4 text-[10px] text-dark-500 border-t border-dark-700/30 pt-3">
                  <span>ID: {result.execution_id.slice(0, 8)}...</span>
                  {result.case_id && <span>Case #{result.case_id}</span>}
                  <span>File: {result.input_filename}</span>
                </div>
              </div>

              {/* AI Summary */}
              <AnimatePresence>
                {result.ai_summary && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="rounded-xl bg-gradient-to-br from-purple-500/5 to-blue-500/5 border border-purple-500/20 p-5 overflow-hidden"
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-7 h-7 rounded-lg bg-purple-500/10 flex items-center justify-center">
                        <Brain className="w-4 h-4 text-purple-400" />
                      </div>
                      <h4 className="text-xs font-bold text-purple-400">AI Analysis Summary</h4>
                      <button
                        onClick={() => copyToClipboard(result.ai_summary!)}
                        className="ml-auto p-1.5 rounded-md hover:bg-dark-700 transition-colors"
                      >
                        <Copy className="w-3 h-3 text-dark-400" />
                      </button>
                    </div>
                    <div className="text-sm text-dark-200 leading-relaxed prose prose-invert prose-sm max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.ai_summary}</ReactMarkdown>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Output Data */}
              {result.output_data && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-primary-400" />
                    <h4 className="text-sm font-bold text-white">Analysis Results</h4>
                    <span className="text-[10px] text-dark-500 ml-auto">
                      {Object.keys(result.output_data).length} fields
                    </span>
                  </div>

                  {/* Tool-specific biometric rendering */}
                  {toolKey && BIOMETRIC_TOOLS.includes(toolKey) ? (
                    renderBiometricResults()
                  ) : (
                    <div className="space-y-3">
                      {Object.entries(result.output_data).filter(([key]) => !['model_used', 'model', 'model_name', 'engine'].includes(key)).map(([key, value]) => (
                        <div key={key} className="rounded-xl bg-dark-800/80 border border-dark-700/50 overflow-hidden">
                          <div className="px-4 py-2.5 border-b border-dark-700/30 flex items-center justify-between">
                            <p className="text-[11px] text-dark-400 uppercase font-semibold tracking-wide">
                              {key.replace(/_/g, ' ')}
                            </p>
                            {typeof value === 'string' && (
                              <button
                                onClick={() => copyToClipboard(String(value))}
                                className="p-1 rounded hover:bg-dark-700 transition-colors"
                              >
                                <Copy className="w-3 h-3 text-dark-500" />
                              </button>
                            )}
                          </div>
                          <div className="p-3">
                            {renderOutputValue(key, value)}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          ) : (
            <div className="rounded-2xl bg-dark-800/50 border border-dark-700/30 p-16 text-center h-full flex flex-col items-center justify-center">
              <div className="w-20 h-20 rounded-2xl bg-dark-800 border border-dark-700/50 flex items-center justify-center mb-5">
                <Microscope className="w-9 h-9 text-dark-600" />
              </div>
              <p className="text-dark-400 text-sm font-medium">No results yet</p>
              <p className="text-dark-500 text-xs mt-1.5 max-w-xs">
                Upload an evidence file and execute analysis to view forensic results here
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
