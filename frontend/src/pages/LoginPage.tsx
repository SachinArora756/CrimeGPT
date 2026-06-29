import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield, Eye, EyeOff } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuthStore } from '../store/authStore'

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    username: '',
    password: '',
    email: '',
    full_name: '',
    role: 'inspector',
    station_id: '',
    badge_number: '',
  })

  const { login, register } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      if (isRegister) {
        await register({
          username: form.username,
          password: form.password,
          email: form.email,
          full_name: form.full_name,
          role: form.role,
          station_id: form.station_id || undefined,
          badge_number: form.badge_number || undefined,
        })
        toast.success('Registration successful')
      } else {
        await login(form.username, form.password)
        toast.success('Welcome back')
      }
      navigate('/')
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      toast.error(error.response?.data?.detail || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-600 rounded-2xl mb-4">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">CrimeGPT</h1>
          <p className="text-dark-400 mt-2">AI-Powered Investigation Operating System</p>
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold text-white mb-6">
            {isRegister ? 'Create Account' : 'Sign In'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1">Username</label>
              <input
                type="text"
                className="input"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                required
              />
            </div>

            {isRegister && (
              <>
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-1">Full Name</label>
                  <input
                    type="text"
                    className="input"
                    value={form.full_name}
                    onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-1">Email</label>
                  <input
                    type="email"
                    className="input"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-1">Role</label>
                  <select
                    className="input"
                    value={form.role}
                    onChange={(e) => setForm({ ...form, role: e.target.value })}
                  >
                    <option value="inspector">Inspector</option>
                    <option value="sub_inspector">Sub Inspector</option>
                    <option value="constable">Constable</option>
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-dark-300 mb-1">Station ID</label>
                    <input
                      type="text"
                      className="input"
                      value={form.station_id}
                      onChange={(e) => setForm({ ...form, station_id: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-dark-300 mb-1">Badge No.</label>
                    <input
                      type="text"
                      className="input"
                      value={form.badge_number}
                      onChange={(e) => setForm({ ...form, badge_number: e.target.value })}
                    />
                  </div>
                </div>
              </>
            )}

            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="input pr-10"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400 hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3 disabled:opacity-50"
            >
              {loading ? 'Processing...' : isRegister ? 'Create Account' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => setIsRegister(!isRegister)}
              className="text-primary-400 hover:text-primary-300 text-sm"
            >
              {isRegister ? 'Already have an account? Sign in' : "Don't have an account? Register"}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
