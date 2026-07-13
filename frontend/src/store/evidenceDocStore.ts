import { create } from 'zustand'
import api from '../api/client'
import { isStale, STALE_TIMES } from './helpers/freshness'

export interface EvidenceItem {
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

export interface DocumentItem {
  id: number
  case_id: number
  doc_type: string
  file_path: string
  generated_by: number
  generated_at: string
}

interface PerCaseCache<T> {
  [caseId: string]: {
    items: T[]
    lastFetched: number
  }
}

interface EvidenceDocState {
  evidence: PerCaseCache<EvidenceItem>
  documents: PerCaseCache<DocumentItem>
  evidenceLoading: boolean
  documentsLoading: boolean

  fetchEvidence: (caseId: string, force?: boolean) => Promise<EvidenceItem[]>
  fetchDocuments: (caseId: string, force?: boolean) => Promise<DocumentItem[]>
  addEvidenceItem: (caseId: string, item: EvidenceItem) => void
  addDocumentItem: (caseId: string, item: DocumentItem) => void
  invalidateCase: (caseId: string) => void
}

const MAX_CACHE_ENTRIES = 5

function evictOldestCache<T>(cache: PerCaseCache<T>): PerCaseCache<T> {
  const entries = Object.entries(cache)
  if (entries.length <= MAX_CACHE_ENTRIES) return cache
  entries.sort((a, b) => a[1].lastFetched - b[1].lastFetched)
  const newCache = { ...cache }
  const toRemove = entries.slice(0, entries.length - MAX_CACHE_ENTRIES)
  for (const [key] of toRemove) {
    delete newCache[key]
  }
  return newCache
}

export const useEvidenceDocStore = create<EvidenceDocState>((set, get) => ({
  evidence: {},
  documents: {},
  evidenceLoading: false,
  documentsLoading: false,

  fetchEvidence: async (caseId, force = false) => {
    const state = get()
    const cached = state.evidence[caseId]

    if (!force && cached && !isStale(cached.lastFetched, STALE_TIMES.EVIDENCE)) {
      return cached.items
    }

    const isFirstLoad = !cached
    if (isFirstLoad) set({ evidenceLoading: true })

    try {
      const response = await api.get(`/api/evidence/case/${caseId}`)
      const items: EvidenceItem[] = response.data.evidence || []
      set((s) => ({
        evidence: evictOldestCache({
          ...s.evidence,
          [caseId]: { items, lastFetched: Date.now() },
        }),
        evidenceLoading: false,
      }))
      return items
    } catch {
      set({ evidenceLoading: false })
      return cached?.items || []
    }
  },

  fetchDocuments: async (caseId, force = false) => {
    const state = get()
    const cached = state.documents[caseId]

    if (!force && cached && !isStale(cached.lastFetched, STALE_TIMES.DOCUMENTS)) {
      return cached.items
    }

    const isFirstLoad = !cached
    if (isFirstLoad) set({ documentsLoading: true })

    try {
      const response = await api.get(`/api/documents/case/${caseId}`)
      const items: DocumentItem[] = Array.isArray(response.data)
        ? response.data
        : response.data.documents || []
      set((s) => ({
        documents: evictOldestCache({
          ...s.documents,
          [caseId]: { items, lastFetched: Date.now() },
        }),
        documentsLoading: false,
      }))
      return items
    } catch {
      set({ documentsLoading: false })
      return cached?.items || []
    }
  },

  addEvidenceItem: (caseId, item) => {
    set((state) => {
      const cached = state.evidence[caseId]
      if (!cached) return state
      return {
        evidence: {
          ...state.evidence,
          [caseId]: {
            ...cached,
            items: [...cached.items, item],
          },
        },
      }
    })
  },

  addDocumentItem: (caseId, item) => {
    set((state) => {
      const cached = state.documents[caseId]
      if (!cached) return state
      return {
        documents: {
          ...state.documents,
          [caseId]: {
            ...cached,
            items: [...cached.items, item],
          },
        },
      }
    })
  },

  invalidateCase: (caseId) => {
    set((state) => {
      const newEvidence = { ...state.evidence }
      const newDocuments = { ...state.documents }
      delete newEvidence[caseId]
      delete newDocuments[caseId]
      return { evidence: newEvidence, documents: newDocuments }
    })
  },
}))
