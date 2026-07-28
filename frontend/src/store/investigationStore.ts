import { create } from 'zustand'

export interface Classification {
  type: string
  mime_type: string
  confidence: number
  ai_enhanced?: boolean
  description?: string
  detected_elements?: string[]
}

export interface ToolProgress {
  tool_key: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  confidence?: number
  execution_time_ms?: number
  output?: any
}

export interface ChecklistItem {
  category: string
  state: 'completed' | 'not_found' | 'needs_manual_review' | 'not_applicable'
  findings_count: number
  confidence: number
  details: string
}

export interface CompletenessData {
  scores: {
    evidence_collection_score: number
    evidence_analysis_score: number
    evidence_verification_score: number
    overall_completeness: number
  }
  missing_analyses: string[]
  recommendations: string[]
}

export interface CorrelationItem {
  source_evidence_id: number
  target_evidence_id: number
  correlation_type: string
  confidence: number
  source_filename?: string
  target_filename?: string
  details?: any
}

export interface PassResult {
  pass_number: number
  pass_name: string
  tool_key: string
  status: string
  confidence: number | null
  findings_summary: string
  execution_time_ms: number
}

export interface Hypothesis {
  id: string
  title: string
  description: string
  confidence: number
  supporting_evidence: string[]
  contradicting_evidence: string[]
  status: string
}

export interface Contradiction {
  id: string
  description: string
  evidence_a: string
  evidence_b: string
  severity: string
  resolution_suggestion?: string
}

export interface ConfidenceDashboard {
  overall_confidence: number
  evidence_strength: number
  hypothesis_coverage: number
  contradiction_severity: number
  recommendations: string[]
}

export interface OsintInvestigation {
  id: number
  identifier_type: string
  identifier_value: string
  findings: Record<string, any>
  officer_notes: string | null
  overall_status: string
  finding_statuses: Record<string, string> | null
  linked_criminal_id: number | null
  searched_by: number
  ai_model_used: string | null
  ai_generation_time_ms: number | null
  created_at: string
  updated_at: string
}

interface IeaeState {
  sessionId: string | null
  uploadedFiles: { name: string; classification?: Classification; url?: string }[]
  toolProgress: ToolProgress[]
  checklist: { items: ChecklistItem[]; completed_count: number; needs_review_count: number } | null
  completeness: CompletenessData | null
  correlations: CorrelationItem[]
  passResults: PassResult[]
  aiPlanReasoning: string
  report: string
  isInvestigating: boolean
  isUploading: boolean
  error: string
}

interface IidseState {
  sessionId: string | null
  uploadedFiles: { name: string; url?: string }[]
  hypotheses: Hypothesis[]
  contradictions: Contradiction[]
  confidenceDashboard: ConfidenceDashboard | null
  report: string
  toolCount: { completed: number; total: number }
  activeTab: 'hypotheses' | 'contradictions' | 'confidence' | 'report'
  isInvestigating: boolean
  isUploading: boolean
  error: string
}

interface OsintState {
  currentInvestigation: OsintInvestigation | null
  officerNotes: string
  selectedType: string
  searchValue: string
}

interface InvestigationStore {
  ieae: IeaeState
  iidse: IidseState
  osint: OsintState

  setIeae: (patch: Partial<IeaeState>) => void
  setIidse: (patch: Partial<IidseState>) => void
  setOsint: (patch: Partial<OsintState>) => void
  clearIeae: () => void
  clearIidse: () => void
  clearOsint: () => void
}

const INITIAL_IEAE: IeaeState = {
  sessionId: null,
  uploadedFiles: [],
  toolProgress: [],
  checklist: null,
  completeness: null,
  correlations: [],
  passResults: [],
  aiPlanReasoning: '',
  report: '',
  isInvestigating: false,
  isUploading: false,
  error: '',
}

const INITIAL_IIDSE: IidseState = {
  sessionId: null,
  uploadedFiles: [],
  hypotheses: [],
  contradictions: [],
  confidenceDashboard: null,
  report: '',
  toolCount: { completed: 0, total: 0 },
  activeTab: 'hypotheses',
  isInvestigating: false,
  isUploading: false,
  error: '',
}

const INITIAL_OSINT: OsintState = {
  currentInvestigation: null,
  officerNotes: '',
  selectedType: 'phone',
  searchValue: '',
}

export const useInvestigationStore = create<InvestigationStore>()(
  (set) => ({
    ieae: { ...INITIAL_IEAE },
    iidse: { ...INITIAL_IIDSE },
    osint: { ...INITIAL_OSINT },

    setIeae: (patch) => set((s) => ({ ieae: { ...s.ieae, ...patch } })),
    setIidse: (patch) => set((s) => ({ iidse: { ...s.iidse, ...patch } })),
    setOsint: (patch) => set((s) => ({ osint: { ...s.osint, ...patch } })),
    clearIeae: () => set({ ieae: { ...INITIAL_IEAE } }),
    clearIidse: () => set({ iidse: { ...INITIAL_IIDSE } }),
    clearOsint: () => set({ osint: { ...INITIAL_OSINT } }),
  })
)
