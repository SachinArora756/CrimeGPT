import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Lock, Eye, EyeOff, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../api/client'
import { useAuthStore } from '../store/authStore'

const ADMIN_ROLES = ['super_admin']

interface PasswordRule {
  label: string
  test: (pw: string) => boolean
}

const PASSWORD_RULES: PasswordRule[] = [
  { label: 'At least 10 characters', test: (pw) => pw.length >= 10 },
  { label: 'One uppercase letter (A-Z)', test: (pw) => /[A-Z]/.test(pw) },
  { label: 'One lowercase letter (a-z)', test: (pw) => /[a-z]/.test(pw) },
  { label: 'One digit (0-9)', test: (pw) => /\d/.test(pw) },
  { label: 'One special character (!@#$%...)', test: (pw) => /[!@#$%^&*()_+\-=\[\]{}|;:'",.<>?/\\~`]/.test(pw) },
  { label: 'No 3+ repeating characters', test: (pw) => !/(.)\1{2,}/.test(pw) },
]

export default function ChangePasswordPage() {
  const navigate = useNavigate()
  const { forcePasswordChange, clearForcePasswordChange, validateSession, refreshAccessToken, logout, user } = useAuthStore()
  const [showCurrent, setShowCurrent] = useState(false)
  const [showNew, setShowNew] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })

  const allRulesPassed = PASSWORD_RULES.every((r) => r.test(form.new_password))
  const passwordsMatch = form.new_password === form.confirm_password && form.confirm_password.length > 0
  const containsUsername = user && form.new_password.toLowerCase().includes(user.username.toLowerCase())

  const canSubmit =
    form.current_password.length > 0 &&
    allRulesPassed &&
    passwordsMatch &&
    !containsUsername

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return

    setLoading(true)
    try {
      await api.post('/api/auth/change-password', {
        current_password: form.current_password,
        new_password: form.new_password,
      })
      toast.success('Password changed successfully')
      clearForcePasswordChange()
      await refreshAccessToken()
      await validateSession()
      const dest = user && ADMIN_ROLES.includes(user.role) ? '/admin' : '/dashboard'
      navigate(dest)
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string | Array<{ msg: string }> } } }
      const detail = error.response?.data?.detail
      if (typeof detail === 'string') {
        toast.error(detail)
      } else if (Array.isArray(detail)) {
        toast.error(detail[0]?.msg || 'Validation failed')
      } else {
        toast.error('Failed to change password')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={forcePasswordChange ? 'min-h-screen bg-dark-950 flex items-center justify-center p-4' : 'max-w-lg mx-auto py-8'}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-lg"
      >
        {forcePasswordChange && (
          <div className="mb-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-xl flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-yellow-400 font-medium">Password Change Required</p>
              <p className="text-dark-300 text-sm mt-1">
                Your administrator has reset your password. You must set a new password before continuing.
              </p>
            </div>
          </div>
        )}

        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-primary-600/20 rounded-xl flex items-center justify-center">
              <Lock className="w-5 h-5 text-primary-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Change Password</h1>
              <p className="text-dark-400 text-sm">Set a strong, unique password</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1">Current Password</label>
              <div className="relative">
                <input
                  type={showCurrent ? 'text' : 'password'}
                  className="input pr-10"
                  value={form.current_password}
                  onChange={(e) => setForm({ ...form, current_password: e.target.value })}
                  required
                  autoFocus
                />
                <button
                  type="button"
                  onClick={() => setShowCurrent(!showCurrent)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400 hover:text-white"
                >
                  {showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1">New Password</label>
              <div className="relative">
                <input
                  type={showNew ? 'text' : 'password'}
                  className="input pr-10"
                  value={form.new_password}
                  onChange={(e) => setForm({ ...form, new_password: e.target.value })}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowNew(!showNew)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400 hover:text-white"
                >
                  {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1">Confirm New Password</label>
              <div className="relative">
                <input
                  type={showConfirm ? 'text' : 'password'}
                  className="input pr-10"
                  value={form.confirm_password}
                  onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400 hover:text-white"
                >
                  {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {form.confirm_password && !passwordsMatch && (
                <p className="text-red-400 text-xs mt-1">Passwords do not match</p>
              )}
            </div>

            {form.new_password.length > 0 && (
              <div className="bg-dark-900 rounded-lg p-4 space-y-2">
                <p className="text-dark-300 text-xs font-medium uppercase tracking-wide mb-2">Password Requirements</p>
                {PASSWORD_RULES.map((rule) => {
                  const passed = rule.test(form.new_password)
                  return (
                    <div key={rule.label} className="flex items-center gap-2">
                      {passed ? (
                        <CheckCircle className="w-3.5 h-3.5 text-green-400" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5 text-dark-500" />
                      )}
                      <span className={`text-xs ${passed ? 'text-green-400' : 'text-dark-400'}`}>
                        {rule.label}
                      </span>
                    </div>
                  )
                })}
                {containsUsername && (
                  <div className="flex items-center gap-2">
                    <XCircle className="w-3.5 h-3.5 text-red-400" />
                    <span className="text-xs text-red-400">Must not contain your username</span>
                  </div>
                )}
              </div>
            )}

            <button
              type="submit"
              disabled={!canSubmit || loading}
              className="btn-primary w-full py-3 disabled:opacity-50"
            >
              {loading ? 'Changing Password...' : 'Change Password'}
            </button>

            {!forcePasswordChange ? (
              <button
                type="button"
                onClick={() => navigate(-1)}
                className="btn-secondary w-full py-3"
              >
                Cancel
              </button>
            ) : (
              <button
                type="button"
                onClick={() => { logout(); navigate('/login'); }}
                className="btn-secondary w-full py-3 text-slate-400"
              >
                Sign Out
              </button>
            )}
          </form>
        </div>
      </motion.div>
    </div>
  )
}
