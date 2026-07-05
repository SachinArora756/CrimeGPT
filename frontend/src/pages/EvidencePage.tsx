import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import {
  Upload, File, Image, FileAudio, FileVideo, Eye, Loader2,
  Shield, Hash, Clock, X, CheckCircle, Brain, FileText,
} from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../api/client'

interface EvidenceItem {
  id: number
  case_id: number
  file_path: string
  original_filename: string
  file_type: string
  file_size: number
  ocr_text: string | null
  analysis_results: Record<string, unknown> | null
  file_hash: string | null
  description: string | null
  tags: string[] | null
  chain_of_custody: Array<Record<string, unknown>> | null
  created_at: string
}

function sanitizeForDisplay(val: unknown): unknown {
  if (typeof val === 'string') {
    if (/^\/(data|uploads|tmp|var|storage|mnt|app|home|root)\//.test(val)) {
      const filename = val.split('/').pop() || 'file'
      return `[Evidence File: ${filename}]`
    }
    return val
  }
  if (Array.isArray(val)) return val.map(sanitizeForDisplay)
  if (val && typeof val === 'object') {
    const sanitized: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(val as Record<string, unknown>)) {
      if (k === 'file_path' || k === 'image_path' || k === 'output_path') {
        sanitized[k] = '[secured]'
      } else {
        sanitized[k] = sanitizeForDisplay(v)
      }
    }
    return sanitized
  }
  return val
}

export default function EvidencePage() {
  const { caseId } = useParams()
  const [evidence, setEvidence] = useState<EvidenceItem[]>([])
  const [uploading, setUploading] = useState(false)
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceItem | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadEvidence() }, [caseId])

  const loadEvidence = async () => {
    try {
      const response = await api.get(`/api/evidence/case/${caseId}`)
      setEvidence(response.data.evidence || [])
    } catch {
      toast.error('Failed to load evidence')
    } finally {
      setLoading(false)
    }
  }

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setUploading(true)
    for (const file of acceptedFiles) {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('description', `Uploaded: ${file.name}`)
      try {
        await api.post(`/api/evidence/upload/${caseId}`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        toast.success(`Uploaded: ${file.name}`)
      } catch {
        toast.error(`Failed: ${file.name}`)
      }
    }
    setUploading(false)
    loadEvidence()
  }, [caseId])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'],
      'application/pdf': ['.pdf'],
      'audio/*': ['.mp3', '.wav', '.m4a'],
      'video/*': ['.mp4', '.avi', '.mov'],
    },
    maxSize: 50 * 1024 * 1024,
  })

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'image': return <Image className="w-6 h-6 text-purple-400" />
      case 'audio': return <FileAudio className="w-6 h-6 text-green-400" />
      case 'video': return <FileVideo className="w-6 h-6 text-red-400" />
      case 'pdf': return <FileText className="w-6 h-6 text-orange-400" />
      default: return <File className="w-6 h-6 text-blue-400" />
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-600/20 rounded-xl flex items-center justify-center">
              <Shield className="w-5 h-5 text-purple-400" />
            </div>
            Evidence Manager
          </h1>
          <p className="text-dark-400 text-sm mt-1">{evidence.length} items collected</p>
        </div>
        <Link to={`/cases/${caseId}`} className="btn-secondary text-sm">← Back to Case</Link>
      </div>

      {/* Upload Zone */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <div
          {...getRootProps()}
          className={`relative overflow-hidden rounded-2xl border-2 border-dashed cursor-pointer transition-all ${
            isDragActive
              ? 'border-primary-500 bg-primary-500/5 scale-[1.01]'
              : 'border-dark-600 hover:border-dark-500 hover:bg-dark-900/50'
          }`}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center py-10">
            {uploading ? (
              <Loader2 className="w-12 h-12 text-primary-400 animate-spin" />
            ) : (
              <div className="w-16 h-16 bg-primary-500/10 rounded-2xl flex items-center justify-center mb-3">
                <Upload className="w-8 h-8 text-primary-400" />
              </div>
            )}
            <p className="text-white font-medium mt-2">
              {isDragActive ? 'Drop evidence files here' : 'Drag & drop evidence, or click to browse'}
            </p>
            <p className="text-dark-400 text-sm mt-1">
              Images, PDFs, Audio, Video — Max 50MB per file
            </p>
            <div className="flex gap-3 mt-4">
              {['JPG', 'PNG', 'PDF', 'MP4', 'MP3'].map(ext => (
                <span key={ext} className="px-2 py-0.5 bg-dark-800 rounded text-[10px] text-dark-400 font-mono">{ext}</span>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Evidence Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1,2,3].map(i => <div key={i} className="card animate-pulse h-40 bg-dark-800/50" />)}
        </div>
      ) : evidence.length === 0 ? (
        <div className="text-center py-16">
          <Shield className="w-12 h-12 text-dark-600 mx-auto mb-3" />
          <p className="text-dark-400">No evidence uploaded yet</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {evidence.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="group rounded-xl bg-dark-900/80 border border-dark-700 hover:border-primary-600/40 transition-all cursor-pointer overflow-hidden"
              onClick={() => setSelectedEvidence(item)}
            >
              {/* File type indicator */}
              <div className={`h-1 w-full ${
                item.file_type === 'image' ? 'bg-purple-500' :
                item.file_type === 'video' ? 'bg-red-500' :
                item.file_type === 'audio' ? 'bg-green-500' : 'bg-blue-500'
              }`} />

              <div className="p-4">
                <div className="flex items-start gap-3">
                  <div className="p-2.5 bg-dark-800 rounded-xl">
                    {getFileIcon(item.file_type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-medium truncate">{item.original_filename}</p>
                    <div className="flex items-center gap-2 mt-1 text-xs text-dark-400">
                      <span className="uppercase">{item.file_type}</span>
                      <span>•</span>
                      <span>{formatSize(item.file_size)}</span>
                    </div>
                  </div>
                  <Eye className="w-4 h-4 text-dark-500 group-hover:text-primary-400 transition-colors" />
                </div>

                {/* Metadata */}
                <div className="mt-3 space-y-1.5">
                  {item.file_hash && (
                    <div className="flex items-center gap-1.5 text-[10px] text-dark-500">
                      <Hash className="w-3 h-3" />
                      <span className="font-mono truncate">{item.file_hash.slice(0, 16)}...</span>
                      <CheckCircle className="w-3 h-3 text-green-500 ml-auto" />
                    </div>
                  )}
                  <div className="flex items-center gap-1.5 text-[10px] text-dark-500">
                    <Clock className="w-3 h-3" />
                    <span>{new Date(item.created_at).toLocaleString()}</span>
                  </div>
                </div>

                {/* Tags */}
                {item.tags && item.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {item.tags.slice(0, 3).map((tag, ti) => (
                      <span key={ti} className="px-1.5 py-0.5 bg-primary-500/10 text-primary-400 rounded text-[10px]">{tag}</span>
                    ))}
                  </div>
                )}

                {/* OCR/AI indicator */}
                <div className="flex items-center gap-2 mt-3 pt-2 border-t border-dark-800">
                  {item.ocr_text && (
                    <span className="flex items-center gap-1 text-[10px] text-cyan-400 bg-cyan-500/10 px-1.5 py-0.5 rounded">
                      <FileText className="w-3 h-3" /> OCR
                    </span>
                  )}
                  {item.analysis_results && (
                    <span className="flex items-center gap-1 text-[10px] text-purple-400 bg-purple-500/10 px-1.5 py-0.5 rounded">
                      <Brain className="w-3 h-3" /> AI Analyzed
                    </span>
                  )}
                  {!item.ocr_text && !item.analysis_results && (
                    <span className="text-[10px] text-dark-500">Pending analysis</span>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Detail Modal */}
      <AnimatePresence>
        {selectedEvidence && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50"
            onClick={() => setSelectedEvidence(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-dark-900 border border-dark-700 rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="sticky top-0 bg-dark-900 border-b border-dark-700 p-4 flex items-center justify-between z-10">
                <div className="flex items-center gap-3">
                  {getFileIcon(selectedEvidence.file_type)}
                  <div>
                    <h3 className="text-white font-semibold text-sm">{selectedEvidence.original_filename}</h3>
                    <p className="text-dark-400 text-xs">{selectedEvidence.file_type} • {formatSize(selectedEvidence.file_size)}</p>
                  </div>
                </div>
                <button onClick={() => setSelectedEvidence(null)} className="p-2 text-dark-400 hover:text-white rounded-lg hover:bg-dark-800">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-4 space-y-4">
                {/* Metadata */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-dark-800/60 rounded-xl">
                    <p className="text-[10px] text-dark-500 uppercase">File Hash (SHA-256)</p>
                    <p className="text-xs text-dark-200 font-mono mt-1 break-all">{selectedEvidence.file_hash || 'N/A'}</p>
                  </div>
                  <div className="p-3 bg-dark-800/60 rounded-xl">
                    <p className="text-[10px] text-dark-500 uppercase">Timestamp</p>
                    <p className="text-xs text-dark-200 mt-1">{new Date(selectedEvidence.created_at).toLocaleString()}</p>
                  </div>
                  <div className="p-3 bg-dark-800/60 rounded-xl">
                    <p className="text-[10px] text-dark-500 uppercase">Integrity</p>
                    <p className="text-xs text-green-400 mt-1 flex items-center gap-1">
                      <CheckCircle className="w-3 h-3" /> Verified
                    </p>
                  </div>
                  <div className="p-3 bg-dark-800/60 rounded-xl">
                    <p className="text-[10px] text-dark-500 uppercase">Size</p>
                    <p className="text-xs text-dark-200 mt-1">{formatSize(selectedEvidence.file_size)}</p>
                  </div>
                </div>

                {/* OCR */}
                {selectedEvidence.ocr_text && (
                  <div>
                    <h4 className="text-sm font-medium text-white flex items-center gap-2 mb-2">
                      <FileText className="w-4 h-4 text-cyan-400" /> OCR Extracted Text
                    </h4>
                    <pre className="text-dark-300 text-xs bg-dark-800/80 p-4 rounded-xl whitespace-pre-wrap max-h-48 overflow-y-auto border border-dark-700">
                      {selectedEvidence.ocr_text}
                    </pre>
                  </div>
                )}

                {/* AI Analysis */}
                {selectedEvidence.analysis_results && (
                  <div>
                    <h4 className="text-sm font-medium text-white flex items-center gap-2 mb-2">
                      <Brain className="w-4 h-4 text-purple-400" /> AI Analysis Results
                    </h4>
                    <pre className="text-dark-300 text-xs bg-dark-800/80 p-4 rounded-xl whitespace-pre-wrap max-h-48 overflow-y-auto border border-dark-700">
                      {JSON.stringify(sanitizeForDisplay(selectedEvidence.analysis_results), null, 2)}
                    </pre>
                  </div>
                )}

                {/* Chain of Custody */}
                {selectedEvidence.chain_of_custody && selectedEvidence.chain_of_custody.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-white flex items-center gap-2 mb-2">
                      <Shield className="w-4 h-4 text-yellow-400" /> Chain of Custody
                    </h4>
                    <div className="space-y-2">
                      {selectedEvidence.chain_of_custody.map((entry, i) => (
                        <div key={i} className="p-2 bg-dark-800/60 rounded-lg text-xs text-dark-300">
                          {JSON.stringify(sanitizeForDisplay(entry))}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
