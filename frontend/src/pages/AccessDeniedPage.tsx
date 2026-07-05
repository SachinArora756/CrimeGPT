import { Link } from 'react-router-dom'
import { ShieldOff, ArrowLeft } from 'lucide-react'
import { useAuthStore } from '../store/authStore'

export default function AccessDeniedPage() {
  const { isAuthenticated, isAdmin, logout } = useAuthStore()

  const loginPath = '/login'
  const dashboardPath = isAdmin() ? '/admin' : '/dashboard'

  return (
    <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center">
        <div className="w-20 h-20 bg-red-500/10 rounded-2xl flex items-center justify-center mx-auto mb-6 border border-red-500/20">
          <ShieldOff className="w-10 h-10 text-red-400" />
        </div>
        <h1 className="text-3xl font-bold text-white mb-2">403 — Access Denied</h1>
        <p className="text-dark-400 mb-8">
          You do not have permission to access this resource. This incident has been logged.
        </p>
        <div className="flex items-center justify-center gap-3">
          {isAuthenticated ? (
            <>
              <Link
                to={dashboardPath}
                className="btn-primary inline-flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" /> Back to Dashboard
              </Link>
              <button
                onClick={() => logout()}
                className="btn-secondary"
              >
                Sign Out
              </button>
            </>
          ) : (
            <Link to={loginPath} className="btn-primary inline-flex items-center gap-2">
              <ArrowLeft className="w-4 h-4" /> Go to Login
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}
