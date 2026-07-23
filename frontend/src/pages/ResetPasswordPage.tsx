import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Lock, Eye, EyeOff, Loader2, CheckCircle, XCircle, Check, X } from 'lucide-react'
import toast from 'react-hot-toast'
import apiClient from '../api/client'

const PASSWORD_RULES = [
  { label: 'At least 10 characters', test: (v: string) => v.length >= 10 },
  { label: 'One uppercase letter', test: (v: string) => /[A-Z]/.test(v) },
  { label: 'One lowercase letter', test: (v: string) => /[a-z]/.test(v) },
  { label: 'One digit', test: (v: string) => /\d/.test(v) },
  { label: 'One special character', test: (v: string) => /[!@#$%^&*()_+\-=\[\]{}|;:'",.<>?/\\~`]/.test(v) },
]

export default function ResetPasswordPage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const [form, setForm] = useState({ password: '', confirmPassword: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')

  const allRulesPassed = PASSWORD_RULES.every((r) => r.test(form.password))
  const passwordsMatch = form.password === form.confirmPassword && form.confirmPassword.length > 0

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!allRulesPassed || !passwordsMatch) return
    setLoading(true)
    setError('')
    try {
      await apiClient.post('/api/auth/reset-password', {
        token,
        new_password: form.password,
      })
      setDone(true)
      toast.success('Password reset successfully!')
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      setError(error.response?.data?.detail || 'Reset failed. The link may be expired.')
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-[#0a1628]">
        <div className="text-center">
          <XCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
          <p className="text-white">Invalid reset link.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-[#0a1628]">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="relative rounded-2xl overflow-hidden">
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-blue-400/10 via-transparent to-transparent p-[1px]">
            <div className="w-full h-full rounded-2xl bg-[#0d1f3c]/80 backdrop-blur-2xl" />
          </div>

          <div className="relative p-8">
            {!done ? (
              <>
                <div className="text-center mb-6">
                  <div className="w-14 h-14 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Lock className="w-7 h-7 text-blue-400" />
                  </div>
                  <h2 className="text-xl font-semibold text-white mb-1">Set New Password</h2>
                  <p className="text-slate-400 text-sm">Choose a strong password for your account.</p>
                </div>

                {error && (
                  <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl">
                    <p className="text-red-400 text-sm">{error}</p>
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="relative">
                    <label htmlFor="new-password" className="block text-sm text-slate-400 mb-1.5">New Password</label>
                    <input
                      id="new-password"
                      type={showPassword ? 'text' : 'password'}
                      value={form.password}
                      onChange={(e) => setForm({ ...form, password: e.target.value })}
                      className="w-full px-4 py-3 pr-11 bg-white/[0.04] border border-white/[0.08] rounded-xl text-white focus:outline-none focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/20 transition-all"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-9 text-slate-500 hover:text-white transition-colors"
                      tabIndex={-1}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>

                  {form.password && (
                    <div className="space-y-1.5">
                      {PASSWORD_RULES.map((rule) => (
                        <div key={rule.label} className="flex items-center gap-2 text-xs">
                          {rule.test(form.password) ? (
                            <Check className="w-3.5 h-3.5 text-green-400" />
                          ) : (
                            <X className="w-3.5 h-3.5 text-slate-500" />
                          )}
                          <span className={rule.test(form.password) ? 'text-green-400' : 'text-slate-500'}>
                            {rule.label}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  <div>
                    <label htmlFor="confirm-password" className="block text-sm text-slate-400 mb-1.5">Confirm Password</label>
                    <input
                      id="confirm-password"
                      type="password"
                      value={form.confirmPassword}
                      onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
                      className="w-full px-4 py-3 bg-white/[0.04] border border-white/[0.08] rounded-xl text-white focus:outline-none focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/20 transition-all"
                      required
                    />
                    {form.confirmPassword && !passwordsMatch && (
                      <p className="text-red-400 text-xs mt-1">Passwords do not match</p>
                    )}
                  </div>

                  <button
                    type="submit"
                    disabled={loading || !allRulesPassed || !passwordsMatch}
                    className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <span className="flex items-center justify-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Resetting...
                      </span>
                    ) : (
                      'Reset Password'
                    )}
                  </button>
                </form>
              </>
            ) : (
              <div className="text-center">
                <div className="w-14 h-14 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-7 h-7 text-green-400" />
                </div>
                <h2 className="text-xl font-semibold text-white mb-2">Password Reset!</h2>
                <p className="text-slate-400 text-sm mb-6">
                  Your password has been updated. You can now log in with your new password.
                </p>
                <button
                  onClick={() => navigate('/login')}
                  className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition-colors"
                >
                  Go to Login
                </button>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  )
}
