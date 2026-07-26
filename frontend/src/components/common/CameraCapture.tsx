import { useState, useRef, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Camera, X, SwitchCamera, RotateCcw, Check, Grid3x3 } from 'lucide-react'

interface CaptureMetadata {
  capturedAt: string
  deviceInfo: string
  geolocation?: { lat: number; lng: number }
}

interface CameraCaptureProps {
  onCapture: (file: File, metadata?: CaptureMetadata) => void
  onClose?: () => void
  maxPhotos?: number
  showPreview?: boolean
  overlayGuide?: 'rule-of-thirds' | 'center' | 'none'
  quality?: number
  facingMode?: 'user' | 'environment'
  className?: string
}

export default function CameraCapture({
  onCapture,
  onClose,
  maxPhotos,
  showPreview = true,
  overlayGuide = 'rule-of-thirds',
  quality = 0.92,
  facingMode: initialFacingMode = 'environment',
  className = '',
}: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const [isActive, setIsActive] = useState(false)
  const [facingMode, setFacingMode] = useState(initialFacingMode)
  const [captureCount, setCaptureCount] = useState(0)
  const [lastCapture, setLastCapture] = useState<string | null>(null)
  const [showFlash, setShowFlash] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showGrid, setShowGrid] = useState(overlayGuide === 'rule-of-thirds')

  const startCamera = useCallback(async () => {
    try {
      setError(null)
      const constraints: MediaStreamConstraints = {
        video: {
          facingMode,
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
      }
      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setIsActive(true)
    } catch (err: any) {
      if (err.name === 'NotAllowedError') {
        setError('Camera access denied. Please allow camera permissions.')
      } else if (err.name === 'NotFoundError') {
        setError('No camera found on this device.')
      } else {
        setError(`Camera error: ${err.message}`)
      }
    }
  }, [facingMode])

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    setIsActive(false)
  }, [])

  useEffect(() => {
    startCamera()
    return () => stopCamera()
  }, [startCamera, stopCamera])

  const switchCamera = useCallback(async () => {
    stopCamera()
    setFacingMode(prev => prev === 'user' ? 'environment' : 'user')
  }, [stopCamera])

  useEffect(() => {
    if (!isActive && !error) {
      startCamera()
    }
  }, [facingMode])

  const capturePhoto = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current) return
    if (maxPhotos && captureCount >= maxPhotos) return

    const video = videoRef.current
    const canvas = canvasRef.current
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(video, 0, 0)

    setShowFlash(true)
    setTimeout(() => setShowFlash(false), 200)

    const blob = await new Promise<Blob | null>(resolve =>
      canvas.toBlob(resolve, 'image/jpeg', quality)
    )
    if (!blob) return

    const timestamp = new Date().toISOString()
    const filename = `capture_${timestamp.replace(/[:.]/g, '-')}.jpg`
    const file = new File([blob], filename, { type: 'image/jpeg' })

    let geolocation: { lat: number; lng: number } | undefined
    try {
      const pos = await new Promise<GeolocationPosition>((resolve, reject) =>
        navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 3000 })
      )
      geolocation = { lat: pos.coords.latitude, lng: pos.coords.longitude }
    } catch { /* geolocation optional */ }

    const metadata: CaptureMetadata = {
      capturedAt: timestamp,
      deviceInfo: navigator.userAgent,
      geolocation,
    }

    if (showPreview) {
      setLastCapture(URL.createObjectURL(blob))
    }

    setCaptureCount(prev => prev + 1)
    onCapture(file, metadata)
  }, [captureCount, maxPhotos, onCapture, quality, showPreview])

  const handleClose = () => {
    stopCamera()
    onClose?.()
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className={`fixed inset-0 z-50 bg-black flex flex-col ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-black/80 backdrop-blur-sm z-10">
        <div className="flex items-center gap-2">
          <Camera className="w-5 h-5 text-primary-400" />
          <span className="text-white text-sm font-medium">Crime Scene Camera</span>
          {maxPhotos && (
            <span className="text-xs text-dark-400 ml-2">
              {captureCount}/{maxPhotos}
            </span>
          )}
        </div>
        <button onClick={handleClose} className="p-2 rounded-full hover:bg-dark-700/50 transition-colors">
          <X className="w-5 h-5 text-white" />
        </button>
      </div>

      {/* Video Feed */}
      <div className="flex-1 relative overflow-hidden">
        {error ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-6">
            <Camera className="w-16 h-16 text-dark-600 mb-4" />
            <p className="text-red-400 text-sm mb-4">{error}</p>
            <button
              onClick={startCamera}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary-600 text-white text-sm"
            >
              <RotateCcw className="w-4 h-4" /> Retry
            </button>
          </div>
        ) : (
          <>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />

            {/* Rule of thirds grid overlay */}
            {showGrid && (
              <div className="absolute inset-0 pointer-events-none">
                <div className="w-full h-full grid grid-cols-3 grid-rows-3">
                  {Array.from({ length: 9 }).map((_, i) => (
                    <div key={i} className="border border-white/20" />
                  ))}
                </div>
              </div>
            )}

            {/* Center crosshair */}
            {overlayGuide === 'center' && !showGrid && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="w-16 h-16 border-2 border-white/40 rounded-full" />
                <div className="absolute w-0.5 h-8 bg-white/40" />
                <div className="absolute w-8 h-0.5 bg-white/40" />
              </div>
            )}

            {/* Flash effect */}
            <AnimatePresence>
              {showFlash && (
                <motion.div
                  initial={{ opacity: 1 }}
                  animate={{ opacity: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="absolute inset-0 bg-white z-20"
                />
              )}
            </AnimatePresence>
          </>
        )}
      </div>

      {/* Controls */}
      <div className="bg-black/80 backdrop-blur-sm px-4 py-5">
        <div className="flex items-center justify-between max-w-md mx-auto">
          {/* Last capture preview */}
          <div className="w-12 h-12">
            {lastCapture && showPreview && (
              <img src={lastCapture} alt="Last capture" className="w-12 h-12 rounded-lg object-cover border border-dark-600" />
            )}
          </div>

          {/* Capture button */}
          <button
            onClick={capturePhoto}
            disabled={!isActive || (maxPhotos ? captureCount >= maxPhotos : false)}
            className="w-16 h-16 rounded-full border-4 border-white flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed group"
          >
            <div className="w-12 h-12 rounded-full bg-white group-hover:bg-primary-200 group-active:scale-90 transition-all" />
          </button>

          {/* Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowGrid(prev => !prev)}
              className={`p-2 rounded-full transition-colors ${showGrid ? 'bg-primary-600' : 'bg-dark-700/50 hover:bg-dark-600/50'}`}
            >
              <Grid3x3 className="w-4 h-4 text-white" />
            </button>
            <button
              onClick={switchCamera}
              className="p-2 rounded-full bg-dark-700/50 hover:bg-dark-600/50 transition-colors"
            >
              <SwitchCamera className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>

        {/* Photo count indicator */}
        {captureCount > 0 && (
          <div className="text-center mt-3">
            <span className="text-xs text-green-400 flex items-center justify-center gap-1">
              <Check className="w-3 h-3" />
              {captureCount} photo{captureCount > 1 ? 's' : ''} captured
            </span>
          </div>
        )}
      </div>

      {/* Hidden canvas for capture */}
      <canvas ref={canvasRef} className="hidden" />
    </motion.div>
  )
}
