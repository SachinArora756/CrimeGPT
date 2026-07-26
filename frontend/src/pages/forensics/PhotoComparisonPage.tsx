import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ChevronLeft, Columns, Layers, Image as ImageIcon } from 'lucide-react'
import api from '../../api/client'

export default function PhotoComparisonPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [photos, setPhotos] = useState<any[]>([])
  const [leftPhoto, setLeftPhoto] = useState<string | null>(searchParams.get('left'))
  const [rightPhoto, setRightPhoto] = useState<string | null>(searchParams.get('right'))
  const [mode, setMode] = useState<'side-by-side' | 'overlay'>('side-by-side')
  const [opacity, setOpacity] = useState(0.5)
  const [caseId, setCaseId] = useState<string>(searchParams.get('case') || '')

  useEffect(() => {
    if (!caseId) return
    api.get(`/api/forensic-photography/photos/case/${caseId}`, { params: { page_size: 100 } })
      .then(res => setPhotos(res.data.photos))
      .catch(() => {})
  }, [caseId])

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="p-2 rounded-xl hover:bg-dark-700/50">
            <ChevronLeft className="w-5 h-5 text-dark-400" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <Columns className="w-5 h-5 text-purple-400" /> Photo Comparison
            </h1>
            <p className="text-dark-400 text-xs">Side-by-side and overlay comparison</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setMode('side-by-side')}
            className={`px-3 py-1.5 rounded-lg text-xs flex items-center gap-1.5 ${mode === 'side-by-side' ? 'bg-purple-600 text-white' : 'bg-dark-700/50 text-dark-400'}`}
          >
            <Columns className="w-3 h-3" /> Side by Side
          </button>
          <button
            onClick={() => setMode('overlay')}
            className={`px-3 py-1.5 rounded-lg text-xs flex items-center gap-1.5 ${mode === 'overlay' ? 'bg-purple-600 text-white' : 'bg-dark-700/50 text-dark-400'}`}
          >
            <Layers className="w-3 h-3" /> Overlay
          </button>
        </div>
      </div>

      {/* Case & Photo Selection */}
      <div className="rounded-2xl bg-dark-800/50 border border-dark-700/50 p-5">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-xs text-dark-400 mb-1.5 block">Case ID</label>
            <input
              type="number"
              value={caseId}
              onChange={e => setCaseId(e.target.value)}
              placeholder="Enter case ID"
              className="input w-full text-sm"
            />
          </div>
          <div>
            <label className="text-xs text-dark-400 mb-1.5 block">Left Photo</label>
            <select
              value={leftPhoto || ''}
              onChange={e => setLeftPhoto(e.target.value || null)}
              className="input w-full text-sm"
            >
              <option value="">Select photo...</option>
              {photos.map(p => (
                <option key={p.photo_id} value={p.photo_id}>{p.original_filename}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-dark-400 mb-1.5 block">Right Photo</label>
            <select
              value={rightPhoto || ''}
              onChange={e => setRightPhoto(e.target.value || null)}
              className="input w-full text-sm"
            >
              <option value="">Select photo...</option>
              {photos.map(p => (
                <option key={p.photo_id} value={p.photo_id}>{p.original_filename}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Comparison View */}
      {mode === 'side-by-side' && (
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-2xl bg-dark-800/50 border border-dark-700/50 overflow-hidden">
            {leftPhoto ? (
              <img
                src={`/api/forensic-photography/photos/${leftPhoto}/file`}
                alt="Left"
                className="w-full h-auto object-contain max-h-[60vh]"
              />
            ) : (
              <div className="h-80 flex items-center justify-center">
                <ImageIcon className="w-12 h-12 text-dark-600" />
              </div>
            )}
          </div>
          <div className="rounded-2xl bg-dark-800/50 border border-dark-700/50 overflow-hidden">
            {rightPhoto ? (
              <img
                src={`/api/forensic-photography/photos/${rightPhoto}/file`}
                alt="Right"
                className="w-full h-auto object-contain max-h-[60vh]"
              />
            ) : (
              <div className="h-80 flex items-center justify-center">
                <ImageIcon className="w-12 h-12 text-dark-600" />
              </div>
            )}
          </div>
        </div>
      )}

      {mode === 'overlay' && (
        <div className="rounded-2xl bg-dark-800/50 border border-dark-700/50 p-4">
          <div className="mb-4 flex items-center gap-4">
            <label className="text-xs text-dark-400">Overlay Opacity:</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={opacity}
              onChange={e => setOpacity(Number(e.target.value))}
              className="flex-1 accent-purple-500"
            />
            <span className="text-xs text-white w-12 text-right">{Math.round(opacity * 100)}%</span>
          </div>
          <div className="relative max-h-[60vh] overflow-hidden flex items-center justify-center">
            {leftPhoto && (
              <img
                src={`/api/forensic-photography/photos/${leftPhoto}/file`}
                alt="Base"
                className="max-w-full max-h-[60vh] object-contain"
              />
            )}
            {rightPhoto && (
              <img
                src={`/api/forensic-photography/photos/${rightPhoto}/file`}
                alt="Overlay"
                className="absolute inset-0 w-full h-full object-contain"
                style={{ opacity }}
              />
            )}
            {!leftPhoto && !rightPhoto && (
              <div className="h-80 flex items-center justify-center">
                <p className="text-dark-500 text-sm">Select two photos to compare</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
