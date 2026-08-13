import { create } from 'zustand'
import api from '../api/client'

interface SceneLayout {
  width: number
  length: number
  height: number
  ground_type: string
  walls: any[]
  lighting: {
    time_of_day: string
    ambient_intensity: number
    main_light_position: number[]
  }
}

interface SceneObject {
  id: string
  type: string
  position: number[]
  rotation: number[]
  scale: number[]
  label: string
  color: string
  evidence_id: number | null
  photo_id: string | null
}

interface TimelineEvent {
  time: string
  description: string
  camera_position: number[]
  camera_target: number[]
  highlight_objects: string[]
  duration: number
}

interface Surface {
  id: string
  type: string
  position: number[]
  rotation: number[]
  size: number[]
  texture_photo_id: string | null
}

interface Reconstruction {
  reconstruction_id: string
  status: string
  metadata: any
  export_html_path: string | null
  export_video_path: string | null
  created_at: string
  updated_at: string
}

interface SceneData {
  reconstruction_id: string
  scene_layout: SceneLayout
  objects: SceneObject[]
  surfaces: Surface[]
  events: TimelineEvent[]
  metadata: any
}

interface ReconstructionListItem {
  reconstruction_id: string
  status: string
  metadata: any
  created_at: string
}

interface SceneReconstructionStore {
  reconstruction: Reconstruction | null
  reconstructions: ReconstructionListItem[]
  sceneData: SceneData | null
  generating: boolean
  loading: boolean
  error: string

  fetchReconstruction: (caseId: number) => Promise<void>
  fetchReconstructionList: (caseId: number) => Promise<void>
  generateReconstruction: (caseId: number) => Promise<string | null>
  pollStatus: (reconstructionId: string) => void
  fetchSceneData: (reconstructionId: string) => Promise<void>
  exportScene: (reconstructionId: string, format: 'html' | 'mp4') => Promise<string | null>
  downloadExport: (reconstructionId: string, format: 'html' | 'mp4') => void
  reset: () => void
}

export const useSceneReconstructionStore = create<SceneReconstructionStore>()(
  (set, get) => ({
    reconstruction: null,
    reconstructions: [],
    sceneData: null,
    generating: false,
    loading: false,
    error: '',

    fetchReconstructionList: async (caseId) => {
      try {
        const res = await api.get(`/api/scene-reconstruction/list/${caseId}`)
        set({ reconstructions: res.data.reconstructions || [] })
      } catch {
        set({ reconstructions: [] })
      }
    },

    fetchReconstruction: async (caseId) => {
      set({ loading: true, error: '' })
      try {
        const res = await api.get(`/api/scene-reconstruction/case/${caseId}`)
        set({ reconstruction: res.data.reconstruction, loading: false })
      } catch {
        set({ loading: false })
      }
    },

    generateReconstruction: async (caseId) => {
      set({ generating: true, error: '' })
      try {
        const res = await api.post(`/api/scene-reconstruction/generate/${caseId}`)
        const id = res.data.reconstruction_id
        set({ generating: true, reconstruction: { reconstruction_id: id, status: 'pending', metadata: null, export_html_path: null, export_video_path: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString() } })
        get().pollStatus(id)
        return id
      } catch (err: any) {
        set({ generating: false, error: err.response?.data?.detail || 'Failed to start generation' })
        return null
      }
    },

    pollStatus: (reconstructionId) => {
      const poll = async () => {
        let attempts = 0
        while (attempts < 60) {
          await new Promise(r => setTimeout(r, 3000))
          attempts++
          try {
            const res = await api.get(`/api/scene-reconstruction/status/${reconstructionId}`)
            const status = res.data.status
            set(state => ({
              reconstruction: state.reconstruction
                ? { ...state.reconstruction, status, metadata: res.data.metadata }
                : null,
            }))
            if (status === 'completed' || status === 'failed') {
              set({ generating: false })
              if (status === 'completed') {
                get().fetchSceneData(reconstructionId)
              }
              if (status === 'failed') {
                set({ error: 'Scene generation failed. Try again.' })
              }
              break
            }
          } catch {
            break
          }
        }
      }
      poll()
    },

    fetchSceneData: async (reconstructionId) => {
      set({ loading: true })
      try {
        const res = await api.get(`/api/scene-reconstruction/${reconstructionId}/data`)
        const data = res.data
        const sceneData: SceneData = {
          reconstruction_id: data.reconstruction_id,
          scene_layout: data.scene_layout || { width: 10, length: 10, height: 3, ground_type: 'floor', walls: [], lighting: { time_of_day: 'day', ambient_intensity: 0.4, main_light_position: [5, 8, 5] } },
          objects: Array.isArray(data.objects) ? data.objects : [],
          surfaces: Array.isArray(data.surfaces) ? data.surfaces : [],
          events: Array.isArray(data.events) ? data.events : [],
          metadata: data.metadata || {},
        }
        set({ sceneData, loading: false })
      } catch {
        set({ loading: false, error: 'Failed to load scene data' })
      }
    },

    exportScene: async (reconstructionId, format) => {
      try {
        const res = await api.post(`/api/scene-reconstruction/${reconstructionId}/export/${format}`)
        return res.data.path
      } catch (err: any) {
        set({ error: err.response?.data?.detail || `Export ${format} failed` })
        return null
      }
    },

    downloadExport: (reconstructionId, format) => {
      const url = `/api/scene-reconstruction/${reconstructionId}/download/${format}`
      window.open(url, '_blank')
    },

    reset: () => set({ reconstruction: null, reconstructions: [], sceneData: null, generating: false, loading: false, error: '' }),
  })
)
