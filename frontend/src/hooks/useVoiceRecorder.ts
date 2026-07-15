import { useState, useRef, useCallback } from 'react'
import api from '../api/client'

interface UseVoiceRecorderResult {
  isRecording: boolean
  isTranscribing: boolean
  startRecording: () => void
  stopAndTranscribe: () => void
  cancelRecording: () => void
  error: string | null
}

export function useVoiceRecorder(onTranscript: (text: string) => void): UseVoiceRecorderResult {
  const [isRecording, setIsRecording] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)

  const cleanup = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
      streamRef.current = null
    }
    mediaRecorderRef.current = null
    chunksRef.current = []
  }, [])

  const startRecording = useCallback(async () => {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : MediaRecorder.isTypeSupported('audio/mp4')
            ? 'audio/mp4'
            : ''

      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream)

      chunksRef.current = []
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      mediaRecorderRef.current = recorder
      recorder.start(250)
      setIsRecording(true)
    } catch (e: any) {
      if (e.name === 'NotAllowedError') {
        setError('Microphone permission denied. Please allow access.')
      } else {
        setError('Failed to start recording: ' + (e.message || 'Unknown error'))
      }
      cleanup()
    }
  }, [cleanup])

  const stopAndTranscribe = useCallback(() => {
    const recorder = mediaRecorderRef.current
    if (!recorder || recorder.state === 'inactive') return

    recorder.onstop = async () => {
      setIsRecording(false)
      setIsTranscribing(true)
      setError(null)

      try {
        const mimeType = recorder.mimeType || 'audio/webm'
        const blob = new Blob(chunksRef.current, { type: mimeType })

        if (blob.size < 1000) {
          setError('Recording too short. Please try again.')
          setIsTranscribing(false)
          cleanup()
          return
        }

        const formData = new FormData()
        const ext = mimeType.includes('mp4') ? '.mp4' : '.webm'
        formData.append('audio', blob, `recording${ext}`)

        const res = await api.post('/api/ai-investigation/transcribe', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })

        const text = res.data.text?.trim()
        if (text) {
          onTranscript(text)
        } else {
          setError('No speech detected. Please try again.')
        }
      } catch (e: any) {
        setError('Transcription failed: ' + (e.response?.data?.detail || e.message || 'Unknown error'))
      } finally {
        setIsTranscribing(false)
        cleanup()
      }
    }

    recorder.stop()
  }, [onTranscript, cleanup])

  const cancelRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current
    if (recorder && recorder.state !== 'inactive') {
      recorder.stop()
    }
    setIsRecording(false)
    setIsTranscribing(false)
    cleanup()
  }, [cleanup])

  return {
    isRecording,
    isTranscribing,
    startRecording,
    stopAndTranscribe,
    cancelRecording,
    error,
  }
}
