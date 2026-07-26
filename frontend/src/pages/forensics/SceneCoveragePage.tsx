import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ChevronLeft, Target, CheckCircle, AlertTriangle, XCircle,
  Camera, RefreshCw, Loader2
} from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../../api/client'

interface CoverageZone {
  id: number
  case_id: number
  zone_key: string
  zone_label: string
  required_shots: number
  actual_shots: number
  status: string
}

export default function SceneCoveragePage() {
  const { caseId } = useParams()
  const navigate = useNavigate()
  const [zones, setZones] = useState<CoverageZone[]>([])
  const [loading, setLoading] = useState(true)
  const [, setOverallStatus] = useState('not_initialized')
  const [crimeType, setCrimeType] = useState('')
  const [initializing, setInitializing] = useState(false)

  useEffect(() => {
    if (!caseId) return
    fetchCoverage()
  }, [caseId])

  const fetchCoverage = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/api/forensic-photography/coverage/${caseId}`)
      setZones(res.data.zones)
      setOverallStatus(res.data.overall_status)
    } catch {
      toast.error('Failed to load coverage')
    }
    setLoading(false)
  }

  const handleInitialize = async () => {
    if (!crimeType || !caseId) return
    setInitializing(true)
    try {
      const formData = new FormData()
      formData.append('crime_type', crimeType)
      const res = await api.post(`/api/forensic-photography/coverage/${caseId}/zones`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setZones(res.data)
      setOverallStatus('red')
      toast.success('Coverage zones initialized')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to initialize')
    }
    setInitializing(false)
  }

  const completedZones = zones.filter(z => z.status === 'green').length
  const inProgressZones = zones.filter(z => z.status === 'yellow').length
  const pendingZones = zones.filter(z => z.status === 'red').length
  const totalRequired = zones.reduce((sum, z) => sum + z.required_shots, 0)
  const totalActual = zones.reduce((sum, z) => sum + z.actual_shots, 0)

  const statusIcon = (status: string) => {
    if (status === 'green') return <CheckCircle className="w-5 h-5 text-green-400" />
    if (status === 'yellow') return <AlertTriangle className="w-5 h-5 text-amber-400" />
    return <XCircle className="w-5 h-5 text-red-400" />
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-96">
        <div className="w-8 h-8 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/forensics/photography')} className="p-2 rounded-xl hover:bg-dark-700/50">
            <ChevronLeft className="w-5 h-5 text-dark-400" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <Target className="w-5 h-5 text-green-400" /> Scene Coverage Tracker
            </h1>
            <p className="text-dark-400 text-xs">Case #{caseId} — Track photography completeness</p>
          </div>
        </div>
        <button onClick={fetchCoverage} className="p-2 rounded-xl hover:bg-dark-700/50">
          <RefreshCw className="w-4 h-4 text-dark-400" />
        </button>
      </div>

      {/* Not initialized */}
      {zones.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl bg-dark-800/50 border border-dark-700/50 p-8 text-center"
        >
          <Target className="w-16 h-16 text-dark-600 mx-auto mb-4" />
          <p className="text-dark-300 text-sm mb-4">Coverage zones not yet initialized for this case</p>
          <div className="flex items-center justify-center gap-3">
            <select
              value={crimeType}
              onChange={e => setCrimeType(e.target.value)}
              className="input text-sm w-48"
            >
              <option value="">Select crime type...</option>
              <option value="murder">Murder</option>
              <option value="robbery">Robbery</option>
              <option value="accident">Accident</option>
              <option value="theft">Theft</option>
              <option value="sexual_assault">Sexual Assault</option>
              <option value="arson">Arson</option>
              <option value="drug_seizure">Drug Seizure</option>
            </select>
            <button
              onClick={handleInitialize}
              disabled={!crimeType || initializing}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-green-600 to-emerald-600 text-white text-sm font-medium disabled:opacity-50"
            >
              {initializing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Target className="w-4 h-4" />}
              Initialize Zones
            </button>
          </div>
        </motion.div>
      )}

      {/* Stats */}
      {zones.length > 0 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-5 rounded-2xl bg-dark-800/50 border border-dark-700/50">
              <p className="text-[10px] text-dark-500 uppercase tracking-wider">Total Photos</p>
              <p className="text-2xl font-bold text-white mt-1">{totalActual}<span className="text-dark-500 text-sm">/{totalRequired}</span></p>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="p-5 rounded-2xl bg-green-500/10 border border-green-500/20">
              <p className="text-[10px] text-green-400 uppercase tracking-wider">Complete</p>
              <p className="text-2xl font-bold text-green-400 mt-1">{completedZones}</p>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="p-5 rounded-2xl bg-amber-500/10 border border-amber-500/20">
              <p className="text-[10px] text-amber-400 uppercase tracking-wider">In Progress</p>
              <p className="text-2xl font-bold text-amber-400 mt-1">{inProgressZones}</p>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="p-5 rounded-2xl bg-red-500/10 border border-red-500/20">
              <p className="text-[10px] text-red-400 uppercase tracking-wider">Pending</p>
              <p className="text-2xl font-bold text-red-400 mt-1">{pendingZones}</p>
            </motion.div>
          </div>

          {/* Progress bar */}
          <div className="rounded-2xl bg-dark-800/50 border border-dark-700/50 p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-dark-400">Overall Progress</span>
              <span className="text-xs text-white font-medium">
                {zones.length > 0 ? Math.round((completedZones / zones.length) * 100) : 0}%
              </span>
            </div>
            <div className="h-3 bg-dark-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full transition-all duration-500"
                style={{ width: `${zones.length > 0 ? (completedZones / zones.length) * 100 : 0}%` }}
              />
            </div>
          </div>

          {/* Zone Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {zones.map((zone, i) => (
              <motion.div
                key={zone.zone_key}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 + i * 0.04 }}
                className={`p-5 rounded-2xl border transition-all ${
                  zone.status === 'green' ? 'bg-green-500/5 border-green-500/30' :
                  zone.status === 'yellow' ? 'bg-amber-500/5 border-amber-500/30' :
                  'bg-red-500/5 border-red-500/30'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-white">{zone.zone_label}</h4>
                    <p className="text-[10px] text-dark-500 mt-0.5">Zone: {zone.zone_key}</p>
                  </div>
                  {statusIcon(zone.status)}
                </div>
                <div className="mt-3">
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="text-dark-400">Photos taken</span>
                    <span className={`font-bold ${
                      zone.status === 'green' ? 'text-green-400' :
                      zone.status === 'yellow' ? 'text-amber-400' : 'text-red-400'
                    }`}>
                      {zone.actual_shots}/{zone.required_shots}
                    </span>
                  </div>
                  <div className="h-2 bg-dark-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        zone.status === 'green' ? 'bg-green-500' :
                        zone.status === 'yellow' ? 'bg-amber-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.min(100, (zone.actual_shots / zone.required_shots) * 100)}%` }}
                    />
                  </div>
                </div>
                {zone.status === 'red' && (
                  <p className="text-[10px] text-red-300 mt-2 flex items-center gap-1">
                    <Camera className="w-3 h-3" />
                    Needs {zone.required_shots - zone.actual_shots} more photo(s)
                  </p>
                )}
              </motion.div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
