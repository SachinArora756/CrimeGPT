export const STALE_TIMES = {
  DASHBOARD: 2 * 60 * 1000,
  CASES_LIST: 60 * 1000,
  CASE_DETAIL: 60 * 1000,
  EVIDENCE: 60 * 1000,
  DOCUMENTS: 60 * 1000,
  NOTIFICATIONS: 30 * 1000,
} as const

export function isStale(lastFetched: number | null, staleTime: number): boolean {
  if (!lastFetched) return true
  return Date.now() - lastFetched > staleTime
}
