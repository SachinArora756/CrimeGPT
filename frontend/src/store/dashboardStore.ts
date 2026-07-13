import { create } from 'zustand'
import api from '../api/client'
import { isStale, STALE_TIMES } from './helpers/freshness'

export interface DashboardStats {
  total_cases: number
  active_cases: number
  closed_cases: number
  chargesheet_cases: number
  total_evidence: number
  total_documents: number
  cases_by_status: Record<string, number>
  today_activity: number
  today_new_cases: number
  today_evidence: number
  today_documents: number
  cases_per_day: Array<{ date: string; count: number }>
  crime_categories: Array<{ category: string; count: number }>
  officer_workload: Array<{ name: string; role: string; cases: number }>
  completion_trend: Array<{ date: string; count: number }>
  recent_activity: Array<{ action: string; resource_type: string; resource_id: string; timestamp: string }>
}

export interface RecentCase {
  id: number
  public_id: string
  fir_number: string
  title: string | null
  complainant_name: string
  status: string
  priority: string | null
  offense_type: string | null
  created_at: string
}

interface DashboardState {
  stats: DashboardStats | null
  recentCases: RecentCase[]
  loading: boolean
  lastFetched: number | null
  fetchDashboard: (force?: boolean) => Promise<void>
  invalidate: () => void
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  stats: null,
  recentCases: [],
  loading: false,
  lastFetched: null,

  fetchDashboard: async (force = false) => {
    const state = get()
    if (!force && !isStale(state.lastFetched, STALE_TIMES.DASHBOARD)) return

    const isFirstLoad = state.stats === null
    if (isFirstLoad) set({ loading: true })

    try {
      const [statsRes, casesRes] = await Promise.all([
        api.get('/api/dashboard/stats'),
        api.get('/api/cases/?per_page=5'),
      ])
      set({
        stats: statsRes.data,
        recentCases: casesRes.data.cases,
        loading: false,
        lastFetched: Date.now(),
      })
    } catch {
      set({ loading: false })
    }
  },

  invalidate: () => {
    set({ lastFetched: null })
  },
}))
