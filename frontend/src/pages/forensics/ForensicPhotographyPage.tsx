import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Camera, Upload, Brain, Shield, Eye, Grid3x3,
  ChevronUp, AlertTriangle,
  Loader2, Image as ImageIcon, MapPin, Zap,
  Target, ArrowRight, Sparkles
} from 'lucide-react'
import toast from 'react-hot-toast'
import PhotoDropzone from '../../components/common/PhotoDropzone'
import AutoEnhanceResult from '../../components/forensic-photo/AutoEnhanceResult'
import { useForensicPhotoStore } from '../../store/forensicPhotoStore'
import api from '../../api/client'

const CRIME_TYPES = [
  'Murder', 'Robbery', 'Accident', 'Theft', 'Sexual Assault',
  'Arson', 'Drug Seizure', 'Kidnapping', 'Riot', 'Cybercrime',
  'Burglary', 'Assault', 'Fraud', 'Other'
]

export default function ForensicPhotographyPage() {
  const navigate = useNavigate()
  const {
    photos, guidanceData, coverageZones, loading, uploadingCount,
    autoEnhanceResults, fetchPhotos, uploadPhotos, fetchGuidance, fetchCoverage,
    assessQuality, initCoverage, pollAutoEnhance, clearAutoEnhanceResult,
  } = useForensicPhotoStore()

  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null)
  const [cases, setCases] = useState<any[]>([])
  const [crimeType, setCrimeType] = useState('')
  const [showGuidance, setShowGuidance] = useState(false)
  const [guidanceLoading, setGuidanceLoading] = useState(false)
  const [assessingId, setAssessingId] = useState<string | null>(null)
  const [category, setCategory] = useState('')
  const [comparePhotoId, setComparePhotoId] = useState<string | null>(null)

  useEffect(() => {
    api.get('/api/cases', { params: { page: 1, page_size: 50 } })
      .then(res => setCases(res.data.cases || res.data || []))
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (selectedCaseId) {
      fetchPhotos(selectedCaseId)
      fetchCoverage(selectedCaseId)
    }
  }, [selectedCaseId, fetchPhotos, fetchCoverage])

  useEffect(() => {
    const enhanced = Object.values(autoEnhanceResults).filter(
      r => r.status === 'completed' && r.auto_enhanced
    )
    if (enhanced.length > 0) {
      const latest = enhanced[enhanced.length - 1]
      if (latest.enhanced_photo_id) {
        toast('Quality issues detected — enhanced version ready', { icon: '✨', duration: 5000 })
        setComparePhotoId(latest.photo_id)
      }
    }
  }, [Object.keys(autoEnhanceResults).filter(k => autoEnhanceResults[k]?.status === 'completed').length])

  const handleFilesReady = useCallback(async (files: File[]) => {
    if (!selectedCaseId) {
      toast.error('Please select a case first')
      return
    }
    const uploaded = await uploadPhotos(selectedCaseId, files, category || undefined)
    if (uploaded.length > 0) {
      toast.success(`${uploaded.length} photo(s) uploaded — analyzing quality...`)
      pollAutoEnhance(uploaded.map((p: any) => p.photo_id))
    }
  }, [selectedCaseId, uploadPhotos, category, pollAutoEnhance])

  const handleGenerateGuidance = async () => {
    if (!crimeType) {
      toast.error('Please select a crime type')
      return
    }
    setGuidanceLoading(true)
    await fetchGuidance(crimeType)
    setShowGuidance(true)
    setGuidanceLoading(false)
    if (selectedCaseId && coverageZones.length === 0) {
      await initCoverage(selectedCaseId, crimeType)
    }
  }

  const handleAssessPhoto = async (photoId: string) => {
    setAssessingId(photoId)
    const result = await assessQuality(photoId)
    if (result) {
      toast.success(`Quality: ${Math.round(result.quality_score)}% | Court-ready: ${Math.round(result.courtroom_readiness)}%`)
    }
    setAssessingId(null)
  }

  const completedZones = coverageZones.filter(z => z.status === 'green').length

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 blur-lg" />
            <div className="relative w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center shadow-xl shadow-purple-500/20">
              <Camera className="w-7 h-7 text-white" />
            </div>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Forensic Photography</h1>
            <p className="text-dark-400 text-sm">AI-guided crime scene documentation & analysis</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {selectedCaseId && (
            <>
              <button
                onClick={() => navigate(`/forensics/photography/gallery/${selectedCaseId}`)}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-dark-700/50 border border-dark-600 hover:border-purple-500/50 text-white text-sm font-medium transition-all"
              >
                <Grid3x3 className="w-4 h-4" /> Gallery
              </button>
              <button
                onClick={() => navigate(`/forensics/photography/coverage/${selectedCaseId}`)}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-dark-700/50 border border-dark-600 hover:border-purple-500/50 text-white text-sm font-medium transition-all"
              >
                <Target className="w-4 h-4" /> Coverage
              </button>
            </>
          )}
        </div>
      </div>

      {/* Case & Crime Type Selection */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl bg-dark-800/50 border border-dark-700/50 p-6"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Case selector */}
          <div>
            <label className="text-xs text-dark-400 font-medium mb-2 block">Select Case / FIR</label>
            <select
              value={selectedCaseId || ''}
              onChange={e => setSelectedCaseId(Number(e.target.value) || null)}
              className="input w-full"
            >
              <option value="">Choose a case...</option>
              {cases.map((c: any) => (
                <option key={c.id} value={c.id}>{c.fir_number || c.title} — {c.title || c.description?.slice(0, 40)}</option>
              ))}
            </select>
          </div>

          {/* Crime type */}
          <div>
            <label className="text-xs text-dark-400 font-medium mb-2 block">Crime Type</label>
            <select
              value={crimeType}
              onChange={e => setCrimeType(e.target.value)}
              className="input w-full"
            >
              <option value="">Select crime type...</option>
              {CRIME_TYPES.map(ct => (
                <option key={ct} value={ct.toLowerCase()}>{ct}</option>
              ))}
            </select>
          </div>

          {/* AI Guidance button */}
          <div className="flex items-end">
            <button
              onClick={handleGenerateGuidance}
              disabled={!crimeType || guidanceLoading}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white text-sm font-medium transition-all disabled:opacity-50 shadow-lg shadow-purple-500/20"
            >
              {guidanceLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
              Get AI Photography Guidance
            </button>
          </div>
        </div>
      </motion.div>

      {/* AI Guidance Panel */}
      <AnimatePresence>
        {showGuidance && guidanceData && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="rounded-2xl bg-dark-800/50 border border-purple-500/20 overflow-hidden"
          >
            <div
              onClick={() => setShowGuidance(prev => !prev)}
              className="flex items-center justify-between px-6 py-4 cursor-pointer hover:bg-dark-700/30 transition-colors"
            >
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Brain className="w-4 h-4 text-purple-400" />
                AI Photography Guidance — {guidanceData.crime_type.toUpperCase()}
                <span className="text-xs text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded-full">
                  Min {guidanceData.minimum_shots} shots
                </span>
              </h3>
              <ChevronUp className="w-4 h-4 text-dark-400" />
            </div>
            <div className="px-6 pb-6 space-y-5">
              {/* Mandatory Angles */}
              <div>
                <h4 className="text-xs font-semibold text-purple-300 uppercase tracking-wider mb-2">Required Angles</h4>
                <div className="flex flex-wrap gap-2">
                  {guidanceData.mandatory_angles.map((angle, i) => (
                    <span key={i} className="px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-xs text-purple-200">
                      {angle}
                    </span>
                  ))}
                </div>
              </div>

              {/* Distance Ranges */}
              <div>
                <h4 className="text-xs font-semibold text-purple-300 uppercase tracking-wider mb-2">Distance Ranges</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                  {guidanceData.distance_ranges.map((dr: any, i: number) => (
                    <div key={i} className="p-3 rounded-xl bg-dark-700/50 border border-dark-600">
                      <p className="text-xs font-medium text-white">{dr.range || dr}</p>
                      {dr.purpose && <p className="text-[10px] text-dark-400 mt-1">{dr.purpose}</p>}
                    </div>
                  ))}
                </div>
              </div>

              {/* Brightness Tips */}
              <div>
                <h4 className="text-xs font-semibold text-amber-300 uppercase tracking-wider mb-2">Lighting & Brightness</h4>
                <ul className="space-y-1">
                  {guidanceData.brightness_tips.map((tip, i) => (
                    <li key={i} className="text-xs text-dark-300 flex items-start gap-2">
                      <Zap className="w-3 h-3 text-amber-400 mt-0.5 flex-shrink-0" />
                      {tip}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Shot Checklist */}
              {guidanceData.shot_checklist.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-green-300 uppercase tracking-wider mb-2">Shot Checklist</h4>
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
                    {guidanceData.shot_checklist.map((shot: any, i: number) => (
                      <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-dark-700/30">
                        <div className="w-6 h-6 rounded-full border border-dark-500 flex items-center justify-center text-[10px] text-dark-400">
                          {shot.id || i + 1}
                        </div>
                        <div className="flex-1">
                          <p className="text-xs text-white">{shot.description}</p>
                          <p className="text-[10px] text-dark-500">{shot.angle} • {shot.distance} • {shot.priority}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Common Mistakes */}
              <div>
                <h4 className="text-xs font-semibold text-red-300 uppercase tracking-wider mb-2">Avoid These Mistakes</h4>
                <ul className="space-y-1">
                  {guidanceData.common_mistakes.map((mistake, i) => (
                    <li key={i} className="text-xs text-dark-300 flex items-start gap-2">
                      <AlertTriangle className="w-3 h-3 text-red-400 mt-0.5 flex-shrink-0" />
                      {mistake}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Indian Law Requirements */}
              <div>
                <h4 className="text-xs font-semibold text-blue-300 uppercase tracking-wider mb-2">Legal Requirements (India)</h4>
                <ul className="space-y-1">
                  {guidanceData.indian_law_requirements.map((req, i) => (
                    <li key={i} className="text-xs text-dark-300 flex items-start gap-2">
                      <Shield className="w-3 h-3 text-blue-400 mt-0.5 flex-shrink-0" />
                      {req}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Upload Section */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="rounded-2xl bg-dark-800/50 border border-dark-700/50 p-6"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Upload className="w-4 h-4 text-purple-400" /> Upload / Capture Photos
          </h3>
          <select
            value={category}
            onChange={e => setCategory(e.target.value)}
            className="input text-xs py-1.5 px-3 w-auto"
          >
            <option value="">Category (optional)</option>
            <option value="overview">Overview</option>
            <option value="midrange">Mid-range</option>
            <option value="closeup">Close-up</option>
            <option value="evidence_marker">Evidence Marker</option>
            <option value="measurement">Measurement</option>
          </select>
        </div>
        <PhotoDropzone
          onFilesReady={handleFilesReady}
          disabled={!selectedCaseId}
          label={selectedCaseId ? 'Drag & drop crime scene photos, or click to browse' : 'Select a case above first'}
        />
        {uploadingCount > 0 && (
          <div className="flex items-center gap-2 mt-3 text-xs text-purple-300">
            <Loader2 className="w-3 h-3 animate-spin" />
            Uploading {uploadingCount} photo(s)...
          </div>
        )}
      </motion.div>

      {/* Coverage Status Bar */}
      {coverageZones.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="rounded-2xl bg-dark-800/50 border border-dark-700/50 p-5"
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Target className="w-4 h-4 text-green-400" /> Scene Coverage
            </h3>
            <span className="text-xs text-dark-400">
              {completedZones}/{coverageZones.length} zones complete
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
            {coverageZones.map(zone => (
              <div
                key={zone.zone_key}
                className={`p-3 rounded-xl border text-center ${
                  zone.status === 'green' ? 'bg-green-500/10 border-green-500/30' :
                  zone.status === 'yellow' ? 'bg-amber-500/10 border-amber-500/30' :
                  'bg-red-500/10 border-red-500/30'
                }`}
              >
                <p className="text-[10px] text-dark-300 truncate">{zone.zone_label}</p>
                <p className={`text-xs font-bold mt-1 ${
                  zone.status === 'green' ? 'text-green-400' :
                  zone.status === 'yellow' ? 'text-amber-400' : 'text-red-400'
                }`}>
                  {zone.actual_shots}/{zone.required_shots}
                </p>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Photos Grid */}
      {photos.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="rounded-2xl bg-dark-800/50 border border-dark-700/50 p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ImageIcon className="w-4 h-4 text-purple-400" /> Recent Photos
              <span className="text-xs text-dark-500">({photos.length})</span>
            </h3>
            {selectedCaseId && (
              <button
                onClick={() => navigate(`/forensics/photography/gallery/${selectedCaseId}`)}
                className="flex items-center gap-1.5 text-xs text-purple-400 hover:text-purple-300 transition-colors"
              >
                View All <ArrowRight className="w-3 h-3" />
              </button>
            )}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {photos.slice(0, 12).map((photo, i) => (
              <motion.div
                key={photo.photo_id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2 + i * 0.03 }}
                className="relative group rounded-xl overflow-hidden border border-dark-700/50 hover:border-purple-500/50 transition-all cursor-pointer"
                onClick={() => navigate(`/forensics/photography/annotate/${photo.photo_id}`)}
              >
                <img
                  src={`/api/forensic-photography/photos/${photo.photo_id}/thumbnail`}
                  alt={photo.original_filename}
                  className="w-full aspect-square object-cover"
                  loading="lazy"
                />
                {/* Auto-enhance status indicator */}
                {autoEnhanceResults[photo.photo_id]?.status === 'processing' && (
                  <div className="absolute top-1.5 right-1.5 px-1.5 py-0.5 rounded bg-purple-500/90 text-[9px] text-white font-bold flex items-center gap-1">
                    <Loader2 className="w-2.5 h-2.5 animate-spin" /> Analyzing
                  </div>
                )}
                {autoEnhanceResults[photo.photo_id]?.status === 'completed' && autoEnhanceResults[photo.photo_id]?.auto_enhanced && (
                  <button
                    onClick={e => { e.stopPropagation(); setComparePhotoId(photo.photo_id) }}
                    className="absolute top-1.5 right-1.5 px-1.5 py-0.5 rounded bg-amber-500/90 text-[9px] text-white font-bold flex items-center gap-1 hover:bg-amber-400 transition-colors"
                    title="Quality issues found — view enhanced version"
                  >
                    <Sparkles className="w-2.5 h-2.5" /> Enhanced
                  </button>
                )}
                {/* Quality indicator */}
                {!autoEnhanceResults[photo.photo_id]?.auto_enhanced && photo.quality_score != null && (
                  <div className={`absolute top-1.5 right-1.5 px-1.5 py-0.5 rounded text-[9px] font-bold ${
                    photo.quality_score >= 70 ? 'bg-green-500/90 text-white' :
                    photo.quality_score >= 40 ? 'bg-amber-500/90 text-white' :
                    'bg-red-500/90 text-white'
                  }`}>
                    {Math.round(photo.quality_score)}%
                  </div>
                )}
                {/* Category tag */}
                {photo.category && (
                  <div className="absolute bottom-1.5 left-1.5 px-1.5 py-0.5 rounded bg-dark-900/80 text-[9px] text-dark-300 capitalize">
                    {photo.category}
                  </div>
                )}
                {/* GPS indicator */}
                {photo.gps_latitude && (
                  <MapPin className="absolute top-1.5 left-1.5 w-3 h-3 text-blue-400" />
                )}
                {/* Hover overlay */}
                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                  <button
                    onClick={e => { e.stopPropagation(); handleAssessPhoto(photo.photo_id) }}
                    className="p-1.5 rounded-lg bg-purple-500/80 hover:bg-purple-500"
                    title="Assess Quality"
                  >
                    {assessingId === photo.photo_id ? (
                      <Loader2 className="w-3.5 h-3.5 text-white animate-spin" />
                    ) : (
                      <Eye className="w-3.5 h-3.5 text-white" />
                    )}
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Empty state */}
      {!loading && photos.length === 0 && selectedCaseId && (
        <div className="py-16 text-center">
          <Camera className="w-12 h-12 text-dark-600 mx-auto mb-3" />
          <p className="text-dark-400 text-sm">No photos yet for this case</p>
          <p className="text-dark-500 text-xs mt-1">Upload or capture crime scene photos above</p>
        </div>
      )}

      {/* Auto-Enhance Comparison Modal */}
      <AnimatePresence>
        {comparePhotoId && autoEnhanceResults[comparePhotoId] && (
          <AutoEnhanceResult
            originalUrl={`/api/forensic-photography/photos/${comparePhotoId}/file`}
            enhancedUrl={`/api/forensic-photography/photos/${autoEnhanceResults[comparePhotoId].enhanced_photo_id}/file`}
            issues={autoEnhanceResults[comparePhotoId].issues}
            onAcceptEnhanced={() => {
              toast.success('Enhanced version accepted')
              clearAutoEnhanceResult(comparePhotoId)
              setComparePhotoId(null)
              if (selectedCaseId) fetchPhotos(selectedCaseId)
            }}
            onKeepOriginal={() => {
              clearAutoEnhanceResult(comparePhotoId)
              setComparePhotoId(null)
            }}
            onRetake={() => {
              clearAutoEnhanceResult(comparePhotoId)
              setComparePhotoId(null)
              toast('Open camera or upload a new photo', { icon: '📷' })
            }}
            onClose={() => setComparePhotoId(null)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
