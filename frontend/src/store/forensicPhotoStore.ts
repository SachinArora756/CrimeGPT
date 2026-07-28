import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import api from '../api/client'

interface ForensicPhoto {
  photo_id: string
  original_filename: string
  file_size: number
  file_hash_sha256: string
  mime_type: string
  width?: number
  height?: number
  gps_latitude?: number
  gps_longitude?: number
  capture_timestamp?: string
  device_make?: string
  device_model?: string
  category?: string
  scene_zone?: string
  tags?: string[]
  description?: string
  quality_score?: number
  quality_assessment?: any
  ai_detected_objects?: any
  courtroom_readiness?: number
  ai_suggestions?: string[]
  capture_source: string
  is_original: boolean
  created_at: string
}

interface CoverageZone {
  id: number
  case_id: number
  zone_key: string
  zone_label: string
  required_shots: number
  actual_shots: number
  status: string
}

interface GuidanceData {
  crime_type: string
  minimum_shots: number
  shot_checklist: any[]
  mandatory_angles: string[]
  distance_ranges: any[]
  brightness_tips: string[]
  special_requirements: string[]
  common_mistakes: string[]
  indian_law_requirements: string[]
}

interface QualityResult {
  photo_id: string
  quality_score: number
  courtroom_readiness: number
  technical_metrics: any
  ai_assessment?: any
  suggestions: string[]
}

interface AutoEnhanceStatus {
  photo_id: string
  status: 'pending' | 'processing' | 'completed' | 'no_issues'
  auto_enhanced: boolean
  quality_score: number | null
  issues: Array<{ type: string; severity: string; score?: number; brightness?: number }>
  enhanced_photo_id: string | null
}

interface ForensicPhotoStore {
  photos: ForensicPhoto[]
  selectedPhoto: ForensicPhoto | null
  coverageZones: CoverageZone[]
  guidanceData: GuidanceData | null
  loading: boolean
  uploadingCount: number
  autoEnhanceResults: Record<string, AutoEnhanceStatus>

  setSelectedPhoto: (photo: ForensicPhoto | null) => void
  fetchPhotos: (caseId: number, page?: number) => Promise<void>
  uploadPhotos: (caseId: number, files: File[], category?: string, sceneZone?: string) => Promise<ForensicPhoto[]>
  capturePhoto: (caseId: number, imageData: string, latitude?: number, longitude?: number, deviceInfo?: string) => Promise<ForensicPhoto | null>
  assessQuality: (photoId: string) => Promise<QualityResult | null>
  checkAutoEnhanceStatus: (photoId: string) => Promise<AutoEnhanceStatus | null>
  pollAutoEnhance: (photoIds: string[]) => void
  clearAutoEnhanceResult: (photoId: string) => void
  fetchGuidance: (crimeType: string, sceneDescription?: string) => Promise<void>
  fetchCoverage: (caseId: number) => Promise<void>
  initCoverage: (caseId: number, crimeType: string) => Promise<void>
  detectObjects: (photoId: string) => Promise<any>
  enhancePhoto: (photoId: string, type: string, params: any) => Promise<string | null>
  reset: () => void
}

export const useForensicPhotoStore = create<ForensicPhotoStore>()(
  persist(
    (set, get) => ({
      photos: [],
      selectedPhoto: null,
      coverageZones: [],
      guidanceData: null,
      loading: false,
      uploadingCount: 0,
      autoEnhanceResults: {},

      setSelectedPhoto: (photo) => set({ selectedPhoto: photo }),

      fetchPhotos: async (caseId, page = 1) => {
        set({ loading: true })
        try {
          const res = await api.get(`/api/forensic-photography/photos/case/${caseId}`, {
            params: { page, page_size: 50 },
          })
          set({ photos: res.data.photos })
        } catch (err) {
          console.error('Failed to fetch photos:', err)
        } finally {
          set({ loading: false })
        }
      },

      uploadPhotos: async (caseId, files, category, sceneZone) => {
        set({ uploadingCount: files.length })
        try {
          const formData = new FormData()
          files.forEach(f => formData.append('files', f))
          if (category) formData.append('category', category)
          if (sceneZone) formData.append('scene_zone', sceneZone)

          const res = await api.post(`/api/forensic-photography/photos/upload/${caseId}`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
          })
          const newPhotos = res.data
          set(state => ({ photos: [...newPhotos, ...state.photos] }))
          return newPhotos
        } catch (err) {
          console.error('Upload failed:', err)
          return []
        } finally {
          set({ uploadingCount: 0 })
        }
      },

      capturePhoto: async (caseId, imageData, latitude, longitude, deviceInfo) => {
        try {
          const res = await api.post(`/api/forensic-photography/photos/capture/${caseId}`, {
            image_data: imageData,
            latitude,
            longitude,
            device_info: deviceInfo,
          })
          const photo = res.data
          set(state => ({ photos: [photo, ...state.photos] }))
          return photo
        } catch (err) {
          console.error('Capture save failed:', err)
          return null
        }
      },

      assessQuality: async (photoId) => {
        try {
          const res = await api.post(`/api/forensic-photography/quality/assess/${photoId}`)
          const result = res.data
          set(state => ({
            photos: state.photos.map(p =>
              p.photo_id === photoId
                ? { ...p, quality_score: result.quality_score, courtroom_readiness: result.courtroom_readiness, ai_suggestions: result.suggestions }
                : p
            ),
          }))
          return result
        } catch (err) {
          console.error('Quality assessment failed:', err)
          return null
        }
      },

      checkAutoEnhanceStatus: async (photoId) => {
        try {
          const res = await api.get(`/api/forensic-photography/photos/${photoId}/auto-enhance-status`)
          const status = res.data as AutoEnhanceStatus
          set(state => ({
            autoEnhanceResults: { ...state.autoEnhanceResults, [photoId]: status },
          }))
          return status
        } catch {
          return null
        }
      },

      pollAutoEnhance: (photoIds) => {
        const poll = async () => {
          const pending = [...photoIds]
          let attempts = 0
          while (pending.length > 0 && attempts < 20) {
            await new Promise(r => setTimeout(r, 3000))
            attempts++
            for (let i = pending.length - 1; i >= 0; i--) {
              const status = await get().checkAutoEnhanceStatus(pending[i])
              if (status && (status.status === 'completed' || status.status === 'no_issues')) {
                pending.splice(i, 1)
              }
            }
          }
        }
        poll()
      },

      clearAutoEnhanceResult: (photoId) => {
        set(state => {
          const updated = { ...state.autoEnhanceResults }
          delete updated[photoId]
          return { autoEnhanceResults: updated }
        })
      },

      fetchGuidance: async (crimeType, sceneDescription) => {
        try {
          const res = await api.post('/api/forensic-photography/guidance/generate', {
            crime_type: crimeType,
            scene_description: sceneDescription,
          })
          set({ guidanceData: res.data })
        } catch (err) {
          console.error('Failed to fetch guidance:', err)
        }
      },

      fetchCoverage: async (caseId) => {
        try {
          const res = await api.get(`/api/forensic-photography/coverage/${caseId}`)
          set({ coverageZones: res.data.zones })
        } catch (err) {
          console.error('Failed to fetch coverage:', err)
        }
      },

      initCoverage: async (caseId, crimeType) => {
        try {
          const formData = new FormData()
          formData.append('crime_type', crimeType)
          const res = await api.post(`/api/forensic-photography/coverage/${caseId}/zones`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
          })
          set({ coverageZones: res.data })
        } catch (err) {
          console.error('Failed to init coverage:', err)
        }
      },

      detectObjects: async (photoId) => {
        try {
          const res = await api.post(`/api/forensic-photography/detect-objects/${photoId}`)
          return res.data
        } catch (err) {
          console.error('Object detection failed:', err)
          return null
        }
      },

      enhancePhoto: async (photoId, type, params) => {
        try {
          const res = await api.post(`/api/forensic-photography/enhance/${photoId}`, {
            enhancement_type: type,
            parameters: params,
          })
          return res.data.enhanced_photo_id
        } catch (err) {
          console.error('Enhancement failed:', err)
          return null
        }
      },

      reset: () => set({ photos: [], selectedPhoto: null, coverageZones: [], guidanceData: null, loading: false, uploadingCount: 0, autoEnhanceResults: {} }),
    }),
    {
      name: 'crimegpt_forensic_photo',
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({ guidanceData: state.guidanceData }),
    }
  )
)
