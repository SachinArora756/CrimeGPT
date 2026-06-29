import { Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useAuthStore } from './store/authStore'
import Layout from './components/layout/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import CasesPage from './pages/CasesPage'
import CaseDetailPage from './pages/CaseDetailPage'
import NewCasePage from './pages/NewCasePage'
import EvidencePage from './pages/EvidencePage'
import InvestigationPage from './pages/InvestigationPage'
import DocumentsPage from './pages/DocumentsPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: '#1e293b', color: '#f1f5f9', border: '1px solid #334155' },
        }}
      />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Layout>
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/cases" element={<CasesPage />} />
                  <Route path="/cases/new" element={<NewCasePage />} />
                  <Route path="/cases/:id" element={<CaseDetailPage />} />
                  <Route path="/evidence/:caseId" element={<EvidencePage />} />
                  <Route path="/investigation/:caseId" element={<InvestigationPage />} />
                  <Route path="/documents/:caseId" element={<DocumentsPage />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  )
}
