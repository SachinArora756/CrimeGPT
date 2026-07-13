import { create } from 'zustand'
import api from '../api/client'
import { isStale, STALE_TIMES } from './helpers/freshness'

export interface CaseListItem {
  id: number
  public_id: string
  fir_number: string
  title: string | null
  complainant_name: string
  accused_name: string | null
  status: string
  priority: string | null
  offense_type: string | null
  station_id: string | null
  assigned_officer_id: number | null
  incident_date: string | null
  created_at: string
  updated_at: string
}

export interface CaseDetail {
  id: number
  public_id: string
  fir_number: string
  title: string | null
  complainant_name: string
  complainant_contact: string | null
  complainant_address: string | null
  accused_name: string | null
  incident_date: string | null
  incident_time: string | null
  incident_location: string | null
  description: string
  status: string
  priority: string | null
  assigned_officer_id: number | null
  created_by_id: number | null
  sections_applied: string[] | null
  offense_type: string | null
  station_id: string | null
  victims: Array<Record<string, unknown>> | null
  accused_persons: Array<Record<string, unknown>> | null
  witnesses: Array<Record<string, unknown>> | null
  investigation_team: Array<Record<string, unknown>> | null
  ai_confidence: number | null
  risk_score: number | null
  created_at: string
  updated_at: string
}

interface CaseDetailCache {
  [publicId: string]: {
    data: CaseDetail
    lastFetched: number
  }
}

interface ListParams {
  page: number
  search: string
  statusFilter: string
}

interface CaseState {
  cases: CaseListItem[]
  total: number
  page: number
  search: string
  statusFilter: string
  loading: boolean
  lastFetched: number | null
  lastParams: string | null

  details: CaseDetailCache

  fetchCases: (params?: { page?: number; search?: string; status?: string; force?: boolean }) => Promise<void>
  setPage: (page: number) => void
  setSearch: (search: string) => void
  setStatusFilter: (status: string) => void

  fetchCaseDetail: (publicId: string, force?: boolean) => Promise<CaseDetail | null>
  updateCaseInStore: (publicId: string, updates: Partial<CaseDetail>) => void
  invalidateCase: (publicId: string) => void
  invalidateList: () => void
}

const MAX_DETAIL_CACHE = 10

function evictOldest(cache: CaseDetailCache): CaseDetailCache {
  const entries = Object.entries(cache)
  if (entries.length <= MAX_DETAIL_CACHE) return cache
  entries.sort((a, b) => a[1].lastFetched - b[1].lastFetched)
  const toRemove = entries.slice(0, entries.length - MAX_DETAIL_CACHE)
  const newCache = { ...cache }
  for (const [key] of toRemove) {
    delete newCache[key]
  }
  return newCache
}

function serializeParams(params: ListParams): string {
  return `${params.page}|${params.search}|${params.statusFilter}`
}

export const useCaseStore = create<CaseState>((set, get) => ({
  cases: [],
  total: 0,
  page: 1,
  search: '',
  statusFilter: '',
  loading: false,
  lastFetched: null,
  lastParams: null,
  details: {},

  fetchCases: async (params) => {
    const state = get()
    const page = params?.page ?? state.page
    const search = params?.search ?? state.search
    const statusFilter = params?.status ?? state.statusFilter
    const force = params?.force ?? false

    const currentParams = serializeParams({ page, search, statusFilter })
    const sameParams = currentParams === state.lastParams

    if (!force && sameParams && !isStale(state.lastFetched, STALE_TIMES.CASES_LIST)) return

    const isFirstLoad = state.cases.length === 0
    if (isFirstLoad || !sameParams) set({ loading: true })

    try {
      const reqParams: Record<string, string | number> = { page, per_page: 15 }
      if (statusFilter) reqParams.status = statusFilter
      if (search) reqParams.search = search

      const response = await api.get('/api/cases/', { params: reqParams })
      set({
        cases: response.data.cases,
        total: response.data.total,
        page,
        search,
        statusFilter,
        loading: false,
        lastFetched: Date.now(),
        lastParams: currentParams,
      })
    } catch {
      set({ loading: false })
    }
  },

  setPage: (page) => set({ page }),
  setSearch: (search) => set({ search }),
  setStatusFilter: (statusFilter) => set({ statusFilter }),

  fetchCaseDetail: async (publicId, force = false) => {
    const state = get()
    const cached = state.details[publicId]

    if (!force && cached && !isStale(cached.lastFetched, STALE_TIMES.CASE_DETAIL)) {
      return cached.data
    }

    try {
      const response = await api.get(`/api/cases/${publicId}`)
      const data: CaseDetail = response.data
      set((s) => ({
        details: evictOldest({
          ...s.details,
          [publicId]: { data, lastFetched: Date.now() },
        }),
      }))
      return data
    } catch {
      return null
    }
  },

  updateCaseInStore: (publicId, updates) => {
    set((state) => {
      const newState: Partial<CaseState> = {}

      if (state.details[publicId]) {
        newState.details = {
          ...state.details,
          [publicId]: {
            ...state.details[publicId],
            data: { ...state.details[publicId].data, ...updates },
          },
        }
      }

      const caseIndex = state.cases.findIndex((c) => c.public_id === publicId)
      if (caseIndex !== -1) {
        const newCases = [...state.cases]
        newCases[caseIndex] = { ...newCases[caseIndex], ...updates } as CaseListItem
        newState.cases = newCases
      }

      return newState
    })
  },

  invalidateCase: (publicId) => {
    set((state) => {
      const newDetails = { ...state.details }
      delete newDetails[publicId]
      return { details: newDetails }
    })
  },

  invalidateList: () => {
    set({ lastFetched: null, lastParams: null })
  },
}))
