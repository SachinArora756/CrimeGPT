import { create } from 'zustand'
import api from '../api/client'

interface ReportReadiness {
  ready: boolean
  case_status: string
  completeness_score: number
  missing_items: string[]
  message: string
}

interface ReportItem {
  id: number
  case_id: number
  file_hash: string | null
  generated_by: number
  generated_at: string
  output_format: string
}

interface ForensicReportState {
  readiness: ReportReadiness | null
  reports: ReportItem[]
  loading: boolean
  generating: boolean
  error: string | null

  fetchReadiness: (caseId: string) => Promise<void>
  fetchReports: (caseId: string) => Promise<void>
  generateReport: (caseId: string, outputFormat?: string) => Promise<void>
  downloadReport: (caseId: string, docId: number) => Promise<void>
  deleteReport: (caseId: string, docId: number) => Promise<void>
  reset: () => void
}

export const useForensicReportStore = create<ForensicReportState>((set) => ({
  readiness: null,
  reports: [],
  loading: false,
  generating: false,
  error: null,

  fetchReadiness: async (caseId: string) => {
    set({ loading: true, error: null })
    try {
      const res = await api.get(`/api/report/${caseId}/readiness`)
      set({ readiness: res.data, loading: false })
    } catch (err: any) {
      set({ error: err.response?.data?.detail || 'Failed to check readiness', loading: false })
    }
  },

  fetchReports: async (caseId: string) => {
    try {
      const res = await api.get(`/api/report/${caseId}/list`)
      set({ reports: Array.isArray(res.data) ? res.data : [] })
    } catch {
      set({ reports: [] })
    }
  },

  generateReport: async (caseId: string, outputFormat = 'pdf') => {
    set({ generating: true, error: null })
    try {
      await api.post(`/api/report/${caseId}/generate`, { output_format: outputFormat }, {
        timeout: 600000,
      })
      set({ generating: false })
      const res = await api.get(`/api/report/${caseId}/list`)
      set({ reports: Array.isArray(res.data) ? res.data : [] })
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Failed to generate report'
      set({
        generating: false,
        error: err.response?.status === 409 ? null : detail,
      })
      if (err.response?.status === 409) {
        throw new Error(detail)
      }
    }
  },

  downloadReport: async (caseId: string, docId: number) => {
    try {
      const res = await api.get(`/api/report/${caseId}/download/${docId}`, {
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `PRISM_Forensic_Report.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      set({ error: err.response?.data?.detail || 'Failed to download report' })
    }
  },

  deleteReport: async (caseId: string, docId: number) => {
    try {
      await api.delete(`/api/report/${caseId}/${docId}`)
      set((state) => ({ reports: state.reports.filter((r) => r.id !== docId) }))
    } catch (err: any) {
      set({ error: err.response?.data?.detail || 'Failed to delete report' })
    }
  },

  reset: () => set({ readiness: null, reports: [], loading: false, generating: false, error: null }),
}))
