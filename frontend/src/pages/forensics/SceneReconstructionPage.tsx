import { useState, useEffect, useRef, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Box, Loader2, AlertCircle, FileVideo, FileCode, RotateCcw, Maximize2, Plus, Clock, CheckCircle2, XCircle, Trash2 } from 'lucide-react'
import { useSceneReconstructionStore } from '../../store/sceneReconstructionStore'
import SceneViewer from '../../components/scene-3d/SceneViewer'
import TimelinePlayer from '../../components/scene-3d/TimelinePlayer'
import ObjectPanel from '../../components/scene-3d/ObjectPanel'
import api from '../../api/client'

interface CaseOption {
  id: number
  public_id: string
  fir_number: string
  title: string | null
  offense_type: string | null
}

export default function SceneReconstructionPage() {
  const {
    reconstruction,
    reconstructions,
    sceneData,
    generating,
    error,
    fetchReconstruction,
    fetchReconstructionList,
    deleteReconstruction,
    generateReconstruction,
    fetchSceneData,
    exportScene,
    downloadExport,
    reset,
  } = useSceneReconstructionStore()

  const [cases, setCases] = useState<CaseOption[]>([])
  const [casesLoading, setCasesLoading] = useState(true)
  const [caseId, setCaseId] = useState<number | null>(null)
  const [currentEventIndex, setCurrentEventIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [highlightedObjects, setHighlightedObjects] = useState<string[]>([])
  const [selectedObjectId, setSelectedObjectId] = useState<string | null>(null)
  const [cameraTarget, setCameraTarget] = useState<{ position: number[]; target: number[] } | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [exporting, setExporting] = useState(false)
  const playInterval = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    api.get('/api/cases/', { params: { per_page: 100 } })
      .then(res => setCases(res.data.cases || []))
      .catch(() => {})
      .finally(() => setCasesLoading(false))
    return () => {
      if (playInterval.current) clearInterval(playInterval.current)
      reset()
    }
  }, [])

  useEffect(() => {
    if (caseId) {
      reset()
      fetchReconstruction(caseId)
      fetchReconstructionList(caseId)
    }
  }, [caseId])

  useEffect(() => {
    if (isPlaying && sceneData?.events?.length) {
      playInterval.current = setInterval(() => {
        setCurrentEventIndex(prev => {
          const next = prev + 1
          if (next >= sceneData.events.length) {
            setIsPlaying(false)
            return prev
          }
          return next
        })
      }, (sceneData.events[currentEventIndex]?.duration || 4) * 1000)
    } else if (playInterval.current) {
      clearInterval(playInterval.current)
    }
    return () => {
      if (playInterval.current) clearInterval(playInterval.current)
    }
  }, [isPlaying, currentEventIndex, sceneData])

  useEffect(() => {
    if (sceneData?.events?.[currentEventIndex]) {
      const event = sceneData.events[currentEventIndex]
      setHighlightedObjects(event.highlight_objects || [])
      if (event.camera_position && event.camera_target) {
        setCameraTarget({ position: event.camera_position, target: event.camera_target })
      }
    }
  }, [currentEventIndex, sceneData])

  const handleCaseSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = Number(e.target.value)
    if (id) setCaseId(id)
  }

  const handleGenerate = async () => {
    if (!caseId) return
    await generateReconstruction(caseId)
  }

  const handleLoadReconstruction = async (reconstructionId: string) => {
    await fetchSceneData(reconstructionId)
  }

  const handleDelete = async (e: React.MouseEvent, reconstructionId: string) => {
    e.stopPropagation()
    if (!confirm('Delete this reconstruction? This cannot be undone.')) return
    await deleteReconstruction(reconstructionId)
  }

  const handleViewScene = async () => {
    if (reconstruction?.reconstruction_id && reconstruction.status === 'completed') {
      await fetchSceneData(reconstruction.reconstruction_id)
    }
  }

  const handleObjectClick = useCallback((id: string) => {
    setSelectedObjectId(id)
    const obj = sceneData?.objects?.find(o => o.id === id)
    if (obj) {
      const pos = obj.position || [0, 0, 0]
      setCameraTarget({ position: [pos[0] + 3, pos[1] + 2, pos[2] + 3], target: pos })
    }
  }, [sceneData])

  const handleExport = async (format: 'html' | 'mp4') => {
    if (!reconstruction?.reconstruction_id) return
    setExporting(true)
    await exportScene(reconstruction.reconstruction_id, format)
    setExporting(false)
    downloadExport(reconstruction.reconstruction_id, format)
  }

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z')
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  // Case selection screen
  if (!caseId) {
    return (
      <div className="min-h-[calc(100vh-4rem)] bg-gray-950 p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-lg mx-auto mt-20"
        >
          <div className="text-center mb-8">
            <div className="inline-flex p-4 rounded-2xl bg-purple-900/30 mb-4">
              <Box size={40} className="text-purple-400" />
            </div>
            <h1 className="text-2xl font-bold text-white">3D Crime Scene Reconstruction</h1>
            <p className="text-gray-400 mt-2">
              Generate an AI-powered 3D reconstruction from case evidence, photos, and diary entries
            </p>
          </div>

          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <label className="block text-sm font-medium text-gray-300 mb-2">Select Case</label>
            {casesLoading ? (
              <div className="flex items-center gap-2 text-gray-400 text-sm py-3">
                <Loader2 className="w-4 h-4 animate-spin" />
                Loading cases...
              </div>
            ) : (
              <select
                onChange={handleCaseSelect}
                defaultValue=""
                className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none appearance-none cursor-pointer"
              >
                <option value="" disabled>Choose a case...</option>
                {cases.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.fir_number ? `FIR: ${c.fir_number}` : `Case #${c.id}`} — {c.title || c.offense_type || 'Untitled'}
                  </option>
                ))}
              </select>
            )}
            {cases.length === 0 && !casesLoading && (
              <p className="text-gray-500 text-sm mt-2">No cases found. Create a case first.</p>
            )}
          </div>
        </motion.div>
      </div>
    )
  }

  // Pre-scene view with history sidebar
  if (!sceneData || !sceneData.scene_layout) {
    const selectedCase = cases.find(c => c.id === caseId)
    return (
      <div className="min-h-[calc(100vh-4rem)] bg-gray-950 p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-5xl mx-auto mt-6"
        >
          {/* Header */}
          <div className="flex items-center gap-3 mb-6">
            <Box size={24} className="text-purple-400" />
            <div className="flex-1">
              <h1 className="text-xl font-bold text-white">3D Reconstruction</h1>
              <p className="text-gray-500 text-sm">
                {selectedCase ? `${selectedCase.fir_number || `Case #${caseId}`} — ${selectedCase.title || selectedCase.offense_type || ''}` : `Case #${caseId}`}
              </p>
            </div>
            <button
              onClick={() => { reset(); setCaseId(null) }}
              className="px-3 py-1.5 text-xs text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
            >
              Change Case
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded-lg flex items-center gap-2">
              <AlertCircle size={16} className="text-red-400" />
              <span className="text-sm text-red-300">{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: History sidebar */}
            <div className="lg:col-span-1">
              <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-white">Saved Reconstructions</h2>
                  <span className="text-xs text-gray-500">{reconstructions.length}</span>
                </div>

                <div className="max-h-[400px] overflow-y-auto">
                  {reconstructions.length === 0 ? (
                    <div className="p-6 text-center">
                      <Box size={24} className="text-gray-700 mx-auto mb-2" />
                      <p className="text-gray-500 text-xs">No reconstructions yet</p>
                    </div>
                  ) : (
                    <div className="divide-y divide-gray-800">
                      {reconstructions.map((rec) => (
                        <div
                          key={rec.reconstruction_id}
                          onClick={() => rec.status === 'completed' && handleLoadReconstruction(rec.reconstruction_id)}
                          className={`w-full p-3 text-left transition-colors flex items-center gap-3 group ${
                            rec.status === 'completed'
                              ? 'hover:bg-gray-800/60 cursor-pointer'
                              : 'opacity-60'
                          }`}
                        >
                          <div className="flex-shrink-0">
                            {rec.status === 'completed' ? (
                              <CheckCircle2 size={16} className="text-emerald-400" />
                            ) : rec.status === 'failed' ? (
                              <XCircle size={16} className="text-red-400" />
                            ) : (
                              <Loader2 size={16} className="text-purple-400 animate-spin" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium text-white truncate">
                              {rec.metadata?.scene_type?.replace('_', ' ') || 'Scene'}
                            </p>
                            <p className="text-[10px] text-gray-500 flex items-center gap-1 mt-0.5">
                              <Clock size={10} />
                              {formatDate(rec.created_at)}
                            </p>
                          </div>
                          <button
                            onClick={(e) => handleDelete(e, rec.reconstruction_id)}
                            className="flex-shrink-0 p-1 rounded hover:bg-red-900/30 text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                            title="Delete"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right: Main action area */}
            <div className="lg:col-span-2">
              {generating ? (
                <div className="bg-gray-900 rounded-xl p-8 border border-gray-800 text-center">
                  <Loader2 size={40} className="text-purple-400 mx-auto mb-4 animate-spin" />
                  <p className="text-white font-medium">Generating 3D Scene...</p>
                  <p className="text-gray-400 text-sm mt-2">
                    AI is analyzing photos, evidence, and diary entries to build the reconstruction
                  </p>
                  <div className="mt-4 w-full bg-gray-800 rounded-full h-1.5">
                    <motion.div
                      className="bg-purple-500 h-1.5 rounded-full"
                      initial={{ width: '5%' }}
                      animate={{ width: '85%' }}
                      transition={{ duration: 60, ease: 'linear' }}
                    />
                  </div>
                </div>
              ) : reconstruction && reconstruction.status === 'completed' ? (
                <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 text-center">
                  <CheckCircle2 size={32} className="text-emerald-400 mx-auto mb-3" />
                  <p className="text-emerald-300 font-medium mb-1">Reconstruction ready!</p>
                  <p className="text-gray-500 text-xs mb-5">Click below to view the 3D scene</p>
                  <div className="flex items-center justify-center gap-3">
                    <button
                      onClick={handleViewScene}
                      className="px-6 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-medium transition-colors"
                    >
                      View 3D Scene
                    </button>
                    <button
                      onClick={handleGenerate}
                      className="px-4 py-3 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm transition-colors"
                    >
                      <RotateCcw size={14} className="inline mr-1.5" />
                      Regenerate
                    </button>
                  </div>
                </div>
              ) : reconstruction && reconstruction.status === 'failed' ? (
                <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 text-center">
                  <AlertCircle size={32} className="text-red-400 mx-auto mb-3" />
                  <p className="text-red-300 mb-4">Last generation failed</p>
                  <button
                    onClick={handleGenerate}
                    className="px-6 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-medium transition-colors"
                  >
                    <RotateCcw size={16} className="inline mr-2" />
                    Retry Generation
                  </button>
                </div>
              ) : (
                <div className="bg-gray-900 rounded-xl p-8 border border-gray-800 text-center">
                  <Box size={48} className="text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-300 mb-2">Generate a new 3D reconstruction</p>
                  <p className="text-gray-500 text-sm mb-6">
                    The AI will analyze all forensic photos, evidence, and case diary to generate a 3D scene
                  </p>
                  <button
                    onClick={handleGenerate}
                    className="px-8 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-medium transition-colors inline-flex items-center gap-2"
                  >
                    <Plus size={18} />
                    Generate 3D Reconstruction
                  </button>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    )
  }

  // Full 3D viewer
  return (
    <div className={`flex flex-col ${isFullscreen ? 'fixed inset-0 z-50' : 'h-[calc(100vh-4rem)]'} bg-gray-950`}>
      <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <Box size={18} className="text-purple-400" />
          <h1 className="text-sm font-semibold text-white">3D Crime Scene — Case #{caseId}</h1>
          {sceneData?.metadata?.scene_type && (
            <span className="px-2 py-0.5 bg-gray-800 rounded text-xs text-gray-400">
              {sceneData.metadata.scene_type.replace('_', ' ')}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => { reset(); fetchReconstruction(caseId); fetchReconstructionList(caseId) }}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded text-xs transition-colors"
          >
            <RotateCcw size={14} />
            Back to List
          </button>
          <button
            onClick={() => handleExport('html')}
            disabled={exporting}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded text-xs transition-colors"
          >
            <FileCode size={14} />
            Export HTML
          </button>
          <button
            onClick={() => handleExport('mp4')}
            disabled={exporting}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded text-xs transition-colors"
          >
            <FileVideo size={14} />
            Export MP4
          </button>
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 hover:bg-gray-700 rounded transition-colors"
          >
            <Maximize2 size={16} className="text-gray-400" />
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 relative">
          {sceneData && (
            <SceneViewer
              layout={sceneData.scene_layout}
              objects={sceneData.objects || []}
              highlightedObjects={highlightedObjects}
              cameraTarget={cameraTarget}
              onObjectClick={handleObjectClick}
            />
          )}
        </div>

        <ObjectPanel
          objects={sceneData?.objects || []}
          selectedId={selectedObjectId}
          onSelect={handleObjectClick}
        />
      </div>

      <TimelinePlayer
        events={sceneData?.events || []}
        currentIndex={currentEventIndex}
        isPlaying={isPlaying}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onSeek={setCurrentEventIndex}
        onNext={() => setCurrentEventIndex(i => Math.min(i + 1, (sceneData?.events?.length || 1) - 1))}
        onPrev={() => setCurrentEventIndex(i => Math.max(i - 1, 0))}
      />
    </div>
  )
}
