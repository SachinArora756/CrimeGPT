import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { AnimatePresence } from 'framer-motion'
import { Upload, Camera, Image as ImageIcon } from 'lucide-react'
import CameraCapture from './CameraCapture'

interface PhotoDropzoneProps {
  onFilesReady: (files: File[]) => void
  accept?: Record<string, string[]>
  maxSize?: number
  multiple?: boolean
  showCamera?: boolean
  cameraFacingMode?: 'user' | 'environment'
  disabled?: boolean
  className?: string
  label?: string
  sublabel?: string
}

export default function PhotoDropzone({
  onFilesReady,
  accept = { 'image/*': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'] },
  maxSize = 20 * 1024 * 1024,
  multiple = true,
  showCamera = true,
  cameraFacingMode = 'environment',
  disabled = false,
  className = '',
  label = 'Drag & drop photos here, or click to browse',
  sublabel = 'JPG, PNG, BMP, TIFF, WebP — Max 20MB per photo',
}: PhotoDropzoneProps) {
  const [cameraOpen, setCameraOpen] = useState(false)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFilesReady(acceptedFiles)
    }
  }, [onFilesReady])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxSize,
    multiple,
    disabled,
  })

  const handleCameraCapture = (file: File) => {
    onFilesReady([file])
  }

  return (
    <>
      <div className={`space-y-3 ${className}`}>
        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`
            relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer
            transition-all duration-200
            ${isDragActive
              ? 'border-purple-400 bg-purple-500/10'
              : 'border-dark-600 hover:border-purple-500/50 hover:bg-dark-800/30'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-3">
            <div className="w-14 h-14 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
              {isDragActive ? (
                <ImageIcon className="w-6 h-6 text-purple-400" />
              ) : (
                <Upload className="w-6 h-6 text-purple-400" />
              )}
            </div>
            <div>
              <p className="text-sm text-dark-300 font-medium">
                {isDragActive ? 'Drop photos here...' : label}
              </p>
              <p className="text-xs text-dark-500 mt-1">{sublabel}</p>
            </div>
          </div>
        </div>

        {/* Camera button */}
        {showCamera && (
          <button
            onClick={() => setCameraOpen(true)}
            disabled={disabled}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl
              border border-purple-500/30 bg-purple-500/5 hover:bg-purple-500/10
              text-purple-300 text-sm font-medium transition-all
              disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Camera className="w-4 h-4" />
            Open Camera to Capture
          </button>
        )}
      </div>

      {/* Camera Modal */}
      <AnimatePresence>
        {cameraOpen && (
          <CameraCapture
            onCapture={handleCameraCapture}
            onClose={() => setCameraOpen(false)}
            facingMode={cameraFacingMode}
          />
        )}
      </AnimatePresence>
    </>
  )
}
