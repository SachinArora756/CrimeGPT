import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useAuthStore } from './store/authStore'
import ErrorBoundary from './components/ErrorBoundary'
import Layout from './components/layout/Layout'

function lazyRetry(importFn: () => Promise<{ default: React.ComponentType }>) {
  return lazy(() =>
    importFn().catch(() => {
      const hasReloaded = sessionStorage.getItem('chunk_reload')
      if (!hasReloaded) {
        sessionStorage.setItem('chunk_reload', '1')
        window.location.reload()
        return new Promise(() => {})
      }
      sessionStorage.removeItem('chunk_reload')
      return importFn()
    })
  )
}

const OfficerLoginPage = lazyRetry(() => import('./pages/OfficerLoginPage'))
const AdminLoginPage = lazyRetry(() => import('./pages/AdminLoginPage'))
const AccessDeniedPage = lazyRetry(() => import('./pages/AccessDeniedPage'))
const DashboardPage = lazyRetry(() => import('./pages/DashboardPage'))
const CasesPage = lazyRetry(() => import('./pages/CasesPage'))
const CaseDetailPage = lazyRetry(() => import('./pages/CaseDetailPage'))
const NewCasePage = lazyRetry(() => import('./pages/NewCasePage'))
const EvidencePage = lazyRetry(() => import('./pages/EvidencePage'))
const InvestigationPage = lazyRetry(() => import('./pages/InvestigationPage'))
const DocumentsPage = lazyRetry(() => import('./pages/DocumentsPage'))
const ChangePasswordPage = lazyRetry(() => import('./pages/ChangePasswordPage'))
const OfficerProfilePage = lazyRetry(() => import('./pages/OfficerProfilePage'))
const LegalRecommendationsPage = lazyRetry(() => import('./pages/LegalRecommendationsPage'))
const NotificationsPage = lazyRetry(() => import('./pages/NotificationsPage'))
const CaseDiaryPage = lazyRetry(() => import('./pages/CaseDiaryPage'))
const MyDocumentsPage = lazyRetry(() => import('./pages/MyDocumentsPage'))
const MyEvidencePage = lazyRetry(() => import('./pages/MyEvidencePage'))
const AdminDashboard = lazyRetry(() => import('./pages/admin/AdminDashboard'))
const UserManagement = lazyRetry(() => import('./pages/admin/UserManagement'))
const AuditLogs = lazyRetry(() => import('./pages/admin/AuditLogs'))
const KnowledgeBase = lazyRetry(() => import('./pages/admin/KnowledgeBase'))

const CriminalIntelDashboard = lazyRetry(() => import('./pages/criminal-intel/CriminalIntelDashboard'))
const CriminalProfilesPage = lazyRetry(() => import('./pages/criminal-intel/CriminalProfilesPage'))
const CriminalProfileDetailPage = lazyRetry(() => import('./pages/criminal-intel/CriminalProfileDetailPage'))
const WatchlistPage = lazyRetry(() => import('./pages/criminal-intel/WatchlistPage'))
const AddCriminalPage = lazyRetry(() => import('./pages/criminal-intel/AddCriminalPage'))

const ForensicsDashboard = lazyRetry(() => import('./pages/forensics/ForensicsDashboard'))
const ToolLauncherPage = lazyRetry(() => import('./pages/forensics/ToolLauncherPage'))
const ToolExecutionPage = lazyRetry(() => import('./pages/forensics/ToolExecutionPage'))
const ExecutionHistoryPage = lazyRetry(() => import('./pages/forensics/ExecutionHistoryPage'))
const SavedResultsPage = lazyRetry(() => import('./pages/forensics/SavedResultsPage'))
const AIInvestigationPage = lazyRetry(() => import('./pages/forensics/AIInvestigationPage'))

function PageLoader() {
  return (
    <div className="space-y-4 p-6 animate-fade-in">
      <div className="h-8 w-48 skeleton" />
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="h-24 skeleton" />
        ))}
      </div>
      <div className="h-64 skeleton" />
    </div>
  )
}

function SessionGate({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, sessionValidated, validateSession, logout, updateActivity, isSessionExpired } = useAuthStore()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    if (isAuthenticated && isSessionExpired()) {
      logout()
      setReady(true)
      return
    }
    if (isAuthenticated && !sessionValidated) {
      validateSession().finally(() => setReady(true))
    } else {
      setReady(true)
    }
  }, [])

  useEffect(() => {
    if (!isAuthenticated) return

    const onActivity = () => updateActivity()
    const events = ['click', 'keydown', 'scroll', 'mousemove', 'touchstart']
    events.forEach(e => window.addEventListener(e, onActivity, { passive: true }))

    const interval = setInterval(() => {
      if (isSessionExpired()) {
        logout()
        window.location.replace('/login')
      }
    }, 60_000)

    return () => {
      events.forEach(e => window.removeEventListener(e, onActivity))
      clearInterval(interval)
    }
  }, [isAuthenticated, updateActivity, isSessionExpired, logout])

  if (!ready) return <PageLoader />
  return <>{children}</>
}

function getHomePath(isAdminUser: boolean, portal: string | null): string {
  if (isAdminUser && portal === 'admin') return '/admin'
  return '/dashboard'
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isAdmin, forcePasswordChange, portal } = useAuthStore()

  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (forcePasswordChange) return <Navigate to="/change-password" replace />
  if (!isAdmin() || portal !== 'admin') return <Navigate to="/dashboard" replace />

  return <>{children}</>
}

function OfficerRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isAdmin, isOfficer, forcePasswordChange, portal } = useAuthStore()

  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (forcePasswordChange) return <Navigate to="/change-password" replace />
  if (!isOfficer() || portal !== 'officer') {
    if (isAdmin() && portal === 'admin') return <Navigate to="/admin" replace />
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function ForensicsRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, hasMinRole, forcePasswordChange } = useAuthStore()

  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (forcePasswordChange) return <Navigate to="/change-password" replace />
  if (!hasMinRole('sub_inspector')) return <Navigate to="/403" replace />

  return <>{children}</>
}

function RootRedirect() {
  const { isAuthenticated, isAdmin, forcePasswordChange, portal } = useAuthStore()

  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (forcePasswordChange) return <Navigate to="/change-password" replace />
  return <Navigate to={getHomePath(isAdmin(), portal)} replace />
}

function PublicOnlyRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, logout } = useAuthStore()
  const wasAuthOnMount = useRef(isAuthenticated)

  useEffect(() => {
    if (wasAuthOnMount.current) {
      logout()
    }
  }, [])

  if (wasAuthOnMount.current && isAuthenticated) return null

  return <>{children}</>
}

function ChangePasswordRoute() {
  const { isAuthenticated, forcePasswordChange, isAdmin, portal } = useAuthStore()
  const location = useLocation()

  if (!isAuthenticated) return <Navigate to="/login" replace />

  const isVoluntary = location.state?.voluntary === true
  if (!forcePasswordChange && !isVoluntary) {
    return <Navigate to={getHomePath(isAdmin(), portal)} replace />
  }

  return <Suspense fallback={<PageLoader />}><ChangePasswordPage /></Suspense>
}

export default function App() {
  return (
    <ErrorBoundary>
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: '#1e293b', color: '#f1f5f9', border: '1px solid #334155' },
        }}
      />
      <SessionGate>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* Public auth routes */}
            <Route path="/login" element={<PublicOnlyRoute><OfficerLoginPage /></PublicOnlyRoute>} />
            <Route path="/s9x" element={<PublicOnlyRoute><AdminLoginPage /></PublicOnlyRoute>} />

            {/* Access Denied */}
            <Route path="/403" element={<AccessDeniedPage />} />

            {/* Force password change */}
            <Route path="/change-password" element={<ChangePasswordRoute />} />

            {/* Root redirect */}
            <Route path="/" element={<RootRedirect />} />

            {/* Admin-only routes */}
            <Route path="/admin" element={<AdminRoute><Layout><AdminDashboard /></Layout></AdminRoute>} />
            <Route path="/admin/users" element={<AdminRoute><Layout><UserManagement /></Layout></AdminRoute>} />
            <Route path="/admin/audit" element={<AdminRoute><Layout><AuditLogs /></Layout></AdminRoute>} />
            <Route path="/admin/knowledge-base" element={<AdminRoute><Layout><KnowledgeBase /></Layout></AdminRoute>} />
            {/* Admin case routes — admin can view all case data */}
            <Route path="/admin/cases/:id" element={<AdminRoute><Layout><CaseDetailPage /></Layout></AdminRoute>} />
            <Route path="/admin/evidence/:caseId" element={<AdminRoute><Layout><EvidencePage /></Layout></AdminRoute>} />
            <Route path="/admin/investigation/:caseId" element={<AdminRoute><Layout><InvestigationPage /></Layout></AdminRoute>} />
            <Route path="/admin/documents/:caseId" element={<AdminRoute><Layout><DocumentsPage /></Layout></AdminRoute>} />
            <Route path="/admin/legal/:caseId" element={<AdminRoute><Layout><LegalRecommendationsPage /></Layout></AdminRoute>} />
            <Route path="/admin/diary/:caseId" element={<AdminRoute><Layout><CaseDiaryPage /></Layout></AdminRoute>} />
            <Route path="/admin/*" element={<AdminRoute><Navigate to="/admin" replace /></AdminRoute>} />

            {/* Officer-only routes */}
            <Route path="/dashboard" element={<OfficerRoute><Layout><DashboardPage /></Layout></OfficerRoute>} />
            <Route path="/cases" element={<OfficerRoute><Layout><CasesPage /></Layout></OfficerRoute>} />
            <Route path="/cases/new" element={<OfficerRoute><Layout><NewCasePage /></Layout></OfficerRoute>} />
            <Route path="/cases/:id" element={<OfficerRoute><Layout><CaseDetailPage /></Layout></OfficerRoute>} />
            <Route path="/evidence/:caseId" element={<OfficerRoute><Layout><EvidencePage /></Layout></OfficerRoute>} />
            <Route path="/investigation/:caseId" element={<OfficerRoute><Layout><InvestigationPage /></Layout></OfficerRoute>} />
            <Route path="/documents/:caseId" element={<OfficerRoute><Layout><DocumentsPage /></Layout></OfficerRoute>} />
            <Route path="/legal/:caseId" element={<OfficerRoute><Layout><LegalRecommendationsPage /></Layout></OfficerRoute>} />
            <Route path="/diary/:caseId" element={<OfficerRoute><Layout><CaseDiaryPage /></Layout></OfficerRoute>} />
            <Route path="/my-documents" element={<OfficerRoute><Layout><MyDocumentsPage /></Layout></OfficerRoute>} />
            <Route path="/my-evidence" element={<OfficerRoute><Layout><MyEvidencePage /></Layout></OfficerRoute>} />
            <Route path="/notifications" element={<OfficerRoute><Layout><NotificationsPage /></Layout></OfficerRoute>} />
            <Route path="/settings/password" element={<OfficerRoute><Layout><ChangePasswordPage /></Layout></OfficerRoute>} />
            <Route path="/profile" element={<OfficerRoute><Layout><OfficerProfilePage /></Layout></OfficerRoute>} />
            <Route path="/profile/:userId" element={<OfficerRoute><Layout><OfficerProfilePage /></Layout></OfficerRoute>} />

            {/* Criminal Intelligence routes */}
            <Route path="/criminal-intel" element={<ForensicsRoute><Layout><CriminalIntelDashboard /></Layout></ForensicsRoute>} />
            <Route path="/criminal-intel/profiles" element={<ForensicsRoute><Layout><CriminalProfilesPage /></Layout></ForensicsRoute>} />
            <Route path="/criminal-intel/profiles/new" element={<ForensicsRoute><Layout><AddCriminalPage /></Layout></ForensicsRoute>} />
            <Route path="/criminal-intel/profiles/:criminalId" element={<ForensicsRoute><Layout><CriminalProfileDetailPage /></Layout></ForensicsRoute>} />
            <Route path="/criminal-intel/watchlist" element={<ForensicsRoute><Layout><WatchlistPage /></Layout></ForensicsRoute>} />

            {/* Digital Forensics Toolkit routes */}
            <Route path="/forensics" element={<ForensicsRoute><Layout><ForensicsDashboard /></Layout></ForensicsRoute>} />
            <Route path="/forensics/tools" element={<ForensicsRoute><Layout><ToolLauncherPage /></Layout></ForensicsRoute>} />
            <Route path="/forensics/execute/:toolKey" element={<ForensicsRoute><Layout><ToolExecutionPage /></Layout></ForensicsRoute>} />
            <Route path="/forensics/execution/:executionId" element={<ForensicsRoute><Layout><ToolExecutionPage /></Layout></ForensicsRoute>} />
            <Route path="/forensics/history" element={<ForensicsRoute><Layout><ExecutionHistoryPage /></Layout></ForensicsRoute>} />
            <Route path="/forensics/saved" element={<ForensicsRoute><Layout><SavedResultsPage /></Layout></ForensicsRoute>} />
            <Route path="/forensics/ai-investigate" element={<ForensicsRoute><Layout><AIInvestigationPage /></Layout></ForensicsRoute>} />

            {/* Catch-all — redirect to dashboard or login, never expose unknown routes */}
            <Route path="*" element={<RootRedirect />} />
          </Routes>
        </Suspense>
      </SessionGate>
    </ErrorBoundary>
  )
}
