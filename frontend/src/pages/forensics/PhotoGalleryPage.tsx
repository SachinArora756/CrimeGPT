import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Grid3x3, MapPin, Clock,
  Camera, Eye, Trash2, Search, X, ChevronLeft
} from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../../api/client'

interface PhotoItem {
  photo_id: string
  original_filename: string
  thumbnail_url: string
  category?: string
  quality_score?: number
  gps_latitude?: number
  gps_longitude?: number
  capture_timestamp?: string
  capture_source: string
  created_at: string
}

export default function PhotoGalleryPage() {
  const { caseId } = useParams()
  const navigate = useNavigate()
  const [photos, setPhotos] = useState<PhotoItem[]>([])
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'timeline' | 'map'>('grid')
  const [filterCategory, setFilterCategory] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedPhoto, setSelectedPhoto] = useState<PhotoItem | null>(null)
  const [page] = useState(1)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    if (!caseId) return
    setLoading(true)
    api.get(`/api/forensic-photography/photos/case/${caseId}`, {
      params: { page, page_size: 50, category: filterCategory || undefined },
    })
      .then(res => {
        setPhotos(res.data.photos)
        setTotal(res.data.total)
      })
      .catch(() => toast.error('Failed to load gallery'))
      .finally(() => setLoading(false))
  }, [caseId, page, filterCategory])

  const filteredPhotos = photos.filter(p =>
    !searchTerm || p.original_filename.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleDelete = async (photoId: string) => {
    if (!confirm('Delete this photo permanently?')) return
    try {
      await api.delete(`/api/forensic-photography/photos/${photoId}`)
      setPhotos(prev => prev.filter(p => p.photo_id !== photoId))
      toast.success('Photo deleted')
    } catch {
      toast.error('Failed to delete')
    }
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
              <Grid3x3 className="w-5 h-5 text-purple-400" /> Photo Gallery
            </h1>
            <p className="text-dark-400 text-xs">{total} photos • Case #{caseId}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {(['grid', 'list', 'timeline', 'map'] as const).map(mode => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`px-3 py-1.5 rounded-lg text-xs capitalize transition-colors ${
                viewMode === mode ? 'bg-purple-600 text-white' : 'bg-dark-700/50 text-dark-400 hover:text-white'
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
          <input
            type="text"
            placeholder="Search photos..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="input pl-9 text-sm w-full"
          />
        </div>
        <select
          value={filterCategory}
          onChange={e => setFilterCategory(e.target.value)}
          className="input text-xs py-2 w-auto"
        >
          <option value="">All Categories</option>
          <option value="overview">Overview</option>
          <option value="midrange">Mid-range</option>
          <option value="closeup">Close-up</option>
          <option value="evidence_marker">Evidence Marker</option>
          <option value="measurement">Measurement</option>
        </select>
      </div>

      {/* Grid View */}
      {viewMode === 'grid' && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {filteredPhotos.map((photo, i) => (
            <motion.div
              key={photo.photo_id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.02 }}
              className="relative group rounded-xl overflow-hidden border border-dark-700/50 hover:border-purple-500/50 cursor-pointer transition-all"
              onClick={() => setSelectedPhoto(photo)}
            >
              <img
                src={photo.thumbnail_url}
                alt={photo.original_filename}
                className="w-full aspect-square object-cover"
                loading="lazy"
              />
              {photo.quality_score != null && (
                <div className={`absolute top-1.5 right-1.5 px-1.5 py-0.5 rounded text-[9px] font-bold ${
                  photo.quality_score >= 70 ? 'bg-green-500/90 text-white' :
                  photo.quality_score >= 40 ? 'bg-amber-500/90 text-white' :
                  'bg-red-500/90 text-white'
                }`}>
                  {Math.round(photo.quality_score)}%
                </div>
              )}
              {photo.category && (
                <div className="absolute bottom-1.5 left-1.5 px-1.5 py-0.5 rounded bg-dark-900/80 text-[9px] text-dark-300 capitalize">
                  {photo.category}
                </div>
              )}
              {photo.capture_source === 'camera' && (
                <Camera className="absolute top-1.5 left-1.5 w-3 h-3 text-purple-400" />
              )}
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                <button
                  onClick={e => { e.stopPropagation(); navigate(`/forensics/photography/annotate/${photo.photo_id}`) }}
                  className="p-1.5 rounded-lg bg-purple-500/80"
                  title="Annotate"
                >
                  <Eye className="w-3.5 h-3.5 text-white" />
                </button>
                <button
                  onClick={e => { e.stopPropagation(); handleDelete(photo.photo_id) }}
                  className="p-1.5 rounded-lg bg-red-500/80"
                  title="Delete"
                >
                  <Trash2 className="w-3.5 h-3.5 text-white" />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* List View */}
      {viewMode === 'list' && (
        <div className="rounded-2xl bg-dark-800/50 border border-dark-700/50 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-700/30">
                <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-4 py-3">Photo</th>
                <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-4 py-3">Filename</th>
                <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-4 py-3">Category</th>
                <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-4 py-3">Quality</th>
                <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-4 py-3">Source</th>
                <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-4 py-3">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-700/30">
              {filteredPhotos.map(photo => (
                <tr
                  key={photo.photo_id}
                  onClick={() => navigate(`/forensics/photography/annotate/${photo.photo_id}`)}
                  className="hover:bg-dark-700/30 cursor-pointer"
                >
                  <td className="px-4 py-2">
                    <img src={photo.thumbnail_url} className="w-10 h-10 rounded object-cover" />
                  </td>
                  <td className="px-4 py-2 text-xs text-white truncate max-w-[180px]">{photo.original_filename}</td>
                  <td className="px-4 py-2 text-xs text-dark-300 capitalize">{photo.category || '—'}</td>
                  <td className="px-4 py-2 text-xs">
                    {photo.quality_score != null ? (
                      <span className={photo.quality_score >= 70 ? 'text-green-400' : photo.quality_score >= 40 ? 'text-amber-400' : 'text-red-400'}>
                        {Math.round(photo.quality_score)}%
                      </span>
                    ) : '—'}
                  </td>
                  <td className="px-4 py-2 text-xs text-dark-400 capitalize">{photo.capture_source}</td>
                  <td className="px-4 py-2 text-xs text-dark-500">{new Date(photo.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Timeline View */}
      {viewMode === 'timeline' && (
        <div className="space-y-4">
          {filteredPhotos
            .sort((a, b) => new Date(a.capture_timestamp || a.created_at).getTime() - new Date(b.capture_timestamp || b.created_at).getTime())
            .map((photo, i) => (
              <motion.div
                key={photo.photo_id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03 }}
                className="flex items-center gap-4 p-3 rounded-xl bg-dark-800/50 border border-dark-700/50 hover:border-purple-500/30 cursor-pointer"
                onClick={() => navigate(`/forensics/photography/annotate/${photo.photo_id}`)}
              >
                <div className="w-2 h-2 rounded-full bg-purple-500 flex-shrink-0" />
                <span className="text-[10px] text-dark-500 w-32 flex-shrink-0">
                  <Clock className="w-3 h-3 inline mr-1" />
                  {new Date(photo.capture_timestamp || photo.created_at).toLocaleString()}
                </span>
                <img src={photo.thumbnail_url} className="w-12 h-12 rounded-lg object-cover flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-white truncate">{photo.original_filename}</p>
                  <p className="text-[10px] text-dark-400 capitalize">{photo.category || 'uncategorized'}</p>
                </div>
                {photo.quality_score != null && (
                  <span className={`text-xs font-bold ${photo.quality_score >= 70 ? 'text-green-400' : 'text-amber-400'}`}>
                    {Math.round(photo.quality_score)}%
                  </span>
                )}
              </motion.div>
            ))}
        </div>
      )}

      {/* Map View */}
      {viewMode === 'map' && (
        <div className="rounded-2xl bg-dark-800/50 border border-dark-700/50 p-6">
          <div className="text-center py-12">
            <MapPin className="w-12 h-12 text-dark-600 mx-auto mb-3" />
            <p className="text-dark-400 text-sm">GPS Map View</p>
            <p className="text-dark-500 text-xs mt-1">
              {filteredPhotos.filter(p => p.gps_latitude).length} photos with GPS data
            </p>
            <div className="mt-4 space-y-2 max-h-64 overflow-y-auto">
              {filteredPhotos.filter(p => p.gps_latitude).map(photo => (
                <div key={photo.photo_id} className="flex items-center gap-3 p-2 rounded-lg bg-dark-700/30">
                  <MapPin className="w-3 h-3 text-blue-400" />
                  <span className="text-xs text-white truncate flex-1">{photo.original_filename}</span>
                  <span className="text-[10px] text-dark-400">
                    {photo.gps_latitude?.toFixed(4)}, {photo.gps_longitude?.toFixed(4)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Lightbox */}
      {selectedPhoto && (
        <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4" onClick={() => setSelectedPhoto(null)}>
          <button className="absolute top-4 right-4 p-2 rounded-full bg-dark-700/50 hover:bg-dark-600" onClick={() => setSelectedPhoto(null)}>
            <X className="w-5 h-5 text-white" />
          </button>
          <img
            src={`/api/forensic-photography/photos/${selectedPhoto.photo_id}/file`}
            alt={selectedPhoto.original_filename}
            className="max-w-full max-h-[85vh] object-contain rounded-lg"
            onClick={e => e.stopPropagation()}
          />
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-dark-800/90 rounded-xl px-4 py-2 text-xs text-dark-300">
            {selectedPhoto.original_filename} • {selectedPhoto.category || 'uncategorized'} • {new Date(selectedPhoto.created_at).toLocaleString()}
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="py-12 text-center">
          <div className="w-8 h-8 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mx-auto" />
        </div>
      )}
    </div>
  )
}
