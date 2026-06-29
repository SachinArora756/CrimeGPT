import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import { Upload, File, Image, FileAudio, FileVideo, Eye, Loader2 } from 'lucide-react'
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
  description: string | null
  created_at: string
}

export default function EvidencePage() {
  const { caseId } = useParams()
  const [evidence, setEvidence] = useState<EvidenceItem[]>([])
  const [uploading, setUploading] = useState(false)
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceItem | null>(null)

  useEffect(() => {
    loadEvidence()
  }, [caseId])

  const loadEvidence = async () => {
    try {
      const response = await api.get(`/api/evidence/case/${caseId}`)
      setEvidence(response.data.evidence)
    } catch {
      toast.error('Failed to load evidence')
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
        toast.error(`Failed to upload: ${file.name}`)
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
      case 'image': return <Image className="w-5 h-5 text-purple-400" />
      case 'audio': return <FileAudio className="w-5 h-5 text-green-400" />
      case 'video': return <FileVideo className="w-5 h-5 text-red-400" />
      default: return <File className="w-5 h-5 text-blue-400" />
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Evidence — Case #{caseId}</h1>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div
          {...getRootProps()}
          className={`card border-2 border-dashed cursor-pointer transition-colors ${
            isDragActive ? 'border-primary-500 bg-primary-500/10' : 'border-dark-600 hover:border-dark-500'
          }`}
        >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center py-8">
          {uploading ? (
            <Loader2 className="w-12 h-12 text-primary-400 animate-spin" />
          ) : (
            <Upload className="w-12 h-12 text-dark-400" />
          )}
          <p className="text-white font-medium mt-4">
            {isDragActive ? 'Drop files here' : 'Drag & drop evidence files, or click to browse'}
          </p>
          <p className="text-dark-400 text-sm mt-2">
            Images, PDFs, audio, video — max 50MB per file
          </p>
        </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {evidence.map((item, i) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="card hover:border-primary-600/50 transition-colors cursor-pointer"
            onClick={() => setSelectedEvidence(item)}
          >
            <div className="flex items-start gap-4">
              <div className="p-3 bg-dark-900 rounded-lg">
                {getFileIcon(item.file_type)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-white font-medium truncate">{item.original_filename}</p>
                <p className="text-dark-400 text-sm mt-1">
                  {item.file_type} • {formatSize(item.file_size)} • {new Date(item.created_at).toLocaleDateString()}
                </p>
                {item.ocr_text && (
                  <p className="text-dark-300 text-xs mt-2 line-clamp-2">{item.ocr_text.slice(0, 100)}...</p>
                )}
              </div>
              <Eye className="w-4 h-4 text-dark-500 flex-shrink-0" />
            </div>
          </motion.div>
        ))}
      </div>

      {evidence.length === 0 && (
        <p className="text-center text-dark-400 py-12">No evidence uploaded yet</p>
      )}

      {selectedEvidence && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedEvidence(null)}
        >
          <div className="card max-w-2xl w-full max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">{selectedEvidence.original_filename}</h3>
              <button onClick={() => setSelectedEvidence(null)} className="text-dark-400 hover:text-white">✕</button>
            </div>
            <div className="space-y-4">
              <div>
                <p className="text-dark-400 text-sm">Type: {selectedEvidence.file_type}</p>
                <p className="text-dark-400 text-sm">Size: {formatSize(selectedEvidence.file_size)}</p>
              </div>
              {selectedEvidence.ocr_text && (
                <div>
                  <p className="text-primary-400 text-sm font-medium mb-2">OCR Extracted Text:</p>
                  <pre className="text-dark-300 text-sm bg-dark-900 p-4 rounded-lg whitespace-pre-wrap max-h-60 overflow-y-auto">
                    {selectedEvidence.ocr_text}
                  </pre>
                </div>
              )}
              {selectedEvidence.analysis_results && (
                <div>
                  <p className="text-primary-400 text-sm font-medium mb-2">Analysis Results:</p>
                  <pre className="text-dark-300 text-sm bg-dark-900 p-4 rounded-lg whitespace-pre-wrap max-h-60 overflow-y-auto">
                    {JSON.stringify(selectedEvidence.analysis_results, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
