import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Shield, Eye, EyeOff, AlertCircle, Lock, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuthStore } from '../store/authStore'

interface Particle {
  id: number
  x: number
  y: number
  size: number
  opacity: number
  speedX: number
  speedY: number
}

function ParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const particlesRef = useRef<Particle[]>([])
  const animRef = useRef<number>(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener('resize', resize)

    const count = 60
    particlesRef.current = Array.from({ length: count }, (_, i) => ({
      id: i,
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      size: Math.random() * 2 + 0.5,
      opacity: Math.random() * 0.4 + 0.1,
      speedX: (Math.random() - 0.5) * 0.3,
      speedY: (Math.random() - 0.5) * 0.3,
    }))

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      particlesRef.current.forEach((p) => {
        p.x += p.speedX
        p.y += p.speedY
        if (p.x < 0) p.x = canvas.width
        if (p.x > canvas.width) p.x = 0
        if (p.y < 0) p.y = canvas.height
        if (p.y > canvas.height) p.y = 0

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(59, 130, 246, ${p.opacity})`
        ctx.fill()
      })

      // Draw connections
      for (let i = 0; i < particlesRef.current.length; i++) {
        for (let j = i + 1; j < particlesRef.current.length; j++) {
          const a = particlesRef.current[i]
          const b = particlesRef.current[j]
          const dx = a.x - b.x
          const dy = a.y - b.y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 120) {
            ctx.beginPath()
            ctx.moveTo(a.x, a.y)
            ctx.lineTo(b.x, b.y)
            ctx.strokeStyle = `rgba(59, 130, 246, ${0.08 * (1 - dist / 120)})`
            ctx.lineWidth = 0.5
            ctx.stroke()
          }
        }
      }

      animRef.current = requestAnimationFrame(animate)
    }
    animate()

    return () => {
      window.removeEventListener('resize', resize)
      cancelAnimationFrame(animRef.current)
    }
  }, [])

  return <canvas ref={canvasRef} className="absolute inset-0 pointer-events-none" />
}

export default function OfficerLoginPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({ username: '', password: '' })
  const [rememberMe, setRememberMe] = useState(false)
  const [focused, setFocused] = useState<string | null>(null)

  const { login } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    const saved = localStorage.getItem('crimegpt_remember_username')
    if (saved) {
      setForm((f) => ({ ...f, username: saved }))
      setRememberMe(true)
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      if (rememberMe) {
        localStorage.setItem('crimegpt_remember_username', form.username)
      } else {
        localStorage.removeItem('crimegpt_remember_username')
      }
      await login(form.username, form.password, 'officer')
      toast.success('Welcome back, Officer')
      const { forcePasswordChange } = useAuthStore.getState()
      if (forcePasswordChange) {
        navigate('/change-password', { replace: true })
      } else {
        navigate('/dashboard')
      }
    } catch (err: unknown) {
      const error = err as { response?: { status?: number; data?: { detail?: string } } }
      const detail = error.response?.data?.detail || ''
      if (error.response?.status === 429) {
        setError('Too many login attempts. Please wait a minute and try again.')
      } else if (error.response?.status === 403) {
        if (detail.toLowerCase().includes('verify your email')) {
          setError('Please verify your email address before logging in. Check your inbox.')
        } else if (detail.toLowerCase().includes('pending')) {
          navigate('/pending-approval')
        } else if (detail.toLowerCase().includes('suspended')) {
          setError('Your account has been suspended. Contact your administrator.')
        } else if (detail.toLowerCase().includes('declined') || detail.toLowerCase().includes('rejected')) {
          setError('Your registration has been declined. Contact your administrator.')
        } else if (detail.toLowerCase().includes('officer') || detail.toLowerCase().includes('admin')) {
          setError(detail)
          toast.error('Redirecting to Admin Login...')
          setTimeout(() => navigate('/s9x'), 2000)
        } else {
          setError(detail || 'Access denied.')
        }
      } else {
        setError(detail || 'Invalid username or password.')
      }
    } finally {
      setLoading(false)
    }
  }

  const usernameActive = focused === 'username' || form.username.length > 0
  const passwordActive = focused === 'password' || form.password.length > 0

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-[#0a1628]">
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0a1628] via-[#0f2847] to-[#0a1628] animate-gradient-shift" />

      {/* Secondary animated orbs */}
      <motion.div
        animate={{ x: [0, 30, 0], y: [0, -20, 0], scale: [1, 1.1, 1] }}
        transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute top-1/4 -left-20 w-[400px] h-[400px] bg-blue-600/8 rounded-full blur-3xl"
      />
      <motion.div
        animate={{ x: [0, -20, 0], y: [0, 30, 0], scale: [1, 1.05, 1] }}
        transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute bottom-1/4 -right-20 w-[500px] h-[500px] bg-indigo-600/6 rounded-full blur-3xl"
      />

      {/* Particle effect */}
      <ParticleBackground />

      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="w-full max-w-[420px] relative z-10"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ duration: 0.6, delay: 0.2, type: 'spring', stiffness: 150 }}
            className="relative inline-flex"
          >
            <div className="w-[72px] h-[72px] bg-gradient-to-br from-blue-500 to-blue-700 rounded-2xl flex items-center justify-center shadow-xl shadow-blue-500/30">
              <Shield className="w-9 h-9 text-white" />
            </div>
            {/* Pulse ring */}
            <motion.div
              animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0, 0.5] }}
              transition={{ duration: 2.5, repeat: Infinity }}
              className="absolute inset-0 rounded-2xl border-2 border-blue-400/30"
            />
          </motion.div>

          <motion.h1
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="text-[28px] font-bold text-white mt-5 tracking-tight"
          >
            CrimeGPT
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="text-blue-300/60 mt-1.5 text-sm font-medium"
          >
            AI-Powered Investigation Management System
          </motion.p>
        </div>

        {/* Login Card — Glassmorphism */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="relative rounded-2xl overflow-hidden"
        >
          {/* Glass border glow */}
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-blue-400/10 via-transparent to-transparent p-[1px]">
            <div className="w-full h-full rounded-2xl bg-[#0d1f3c]/80 backdrop-blur-2xl" />
          </div>

          <div className="relative p-8">
            <h2 className="text-lg font-semibold text-white mb-1">Officer Sign In</h2>
            <p className="text-slate-400 text-sm mb-7">Access your investigation workspace</p>

            {/* Error message */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                  animate={{ opacity: 1, height: 'auto', marginBottom: 20 }}
                  exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                  className="overflow-hidden"
                >
                  <motion.div
                    initial={{ x: -8 }}
                    animate={{ x: [0, -3, 3, -2, 2, 0] }}
                    transition={{ duration: 0.4 }}
                    className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-2.5"
                  >
                    <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                    <p className="text-red-400 text-sm">{error}</p>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>

            <form onSubmit={handleSubmit} className="space-y-5" role="form" aria-label="Officer login form">
              {/* Username — Floating Label */}
              <div className="relative">
                <input
                  id="officer-username"
                  type="text"
                  className={`w-full px-4 pt-6 pb-2 bg-white/[0.04] border rounded-xl text-white placeholder-transparent focus:outline-none transition-all duration-200 ${
                    focused === 'username'
                      ? 'border-blue-500/60 ring-1 ring-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.1)]'
                      : 'border-white/[0.08] hover:border-white/[0.15]'
                  }`}
                  placeholder="Username"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  onFocus={() => setFocused('username')}
                  onBlur={() => setFocused(null)}
                  required
                  autoComplete="username"
                  aria-label="Username or Badge ID"
                />
                <label
                  htmlFor="officer-username"
                  className={`absolute left-4 transition-all duration-200 pointer-events-none ${
                    usernameActive
                      ? 'top-2 text-[11px] text-blue-400 font-medium'
                      : 'top-1/2 -translate-y-1/2 text-sm text-slate-500'
                  }`}
                >
                  Username / Badge ID
                </label>
              </div>

              {/* Password — Floating Label */}
              <div className="relative">
                <input
                  id="officer-password"
                  type={showPassword ? 'text' : 'password'}
                  className={`w-full px-4 pt-6 pb-2 pr-12 bg-white/[0.04] border rounded-xl text-white placeholder-transparent focus:outline-none transition-all duration-200 ${
                    focused === 'password'
                      ? 'border-blue-500/60 ring-1 ring-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.1)]'
                      : 'border-white/[0.08] hover:border-white/[0.15]'
                  }`}
                  placeholder="Password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  onFocus={() => setFocused('password')}
                  onBlur={() => setFocused(null)}
                  required
                  autoComplete="current-password"
                  aria-label="Password"
                />
                <label
                  htmlFor="officer-password"
                  className={`absolute left-4 transition-all duration-200 pointer-events-none ${
                    passwordActive
                      ? 'top-2 text-[11px] text-blue-400 font-medium'
                      : 'top-1/2 -translate-y-1/2 text-sm text-slate-500'
                  }`}
                >
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              {/* Remember me & Forgot password */}
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer group" htmlFor="remember-me">
                  <input
                    type="checkbox"
                    id="remember-me"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 rounded border-white/20 bg-white/5 text-blue-500 focus:ring-blue-500/30 focus:ring-offset-0 cursor-pointer"
                  />
                  <span className="text-sm text-slate-400 group-hover:text-slate-300 transition-colors">Remember me</span>
                </label>
                <button
                  type="button"
                  className="text-sm text-blue-400/70 hover:text-blue-400 transition-colors"
                  onClick={() => navigate('/forgot-password')}
                >
                  Forgot password?
                </button>
              </div>

              {/* Submit */}
              <motion.button
                type="submit"
                disabled={loading || !form.username || !form.password}
                whileHover={{ scale: loading ? 1 : 1.01 }}
                whileTap={{ scale: loading ? 1 : 0.98 }}
                className="w-full py-3.5 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white font-semibold rounded-xl shadow-lg shadow-blue-600/20 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed relative overflow-hidden"
                aria-label="Sign in"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Authenticating...
                  </span>
                ) : (
                  'Sign In'
                )}
              </motion.button>
            </form>

            {/* Register link */}
            <div className="mt-6 text-center">
              <p className="text-slate-400 text-sm">
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={() => navigate('/register')}
                  className="text-blue-400 hover:text-blue-300 font-medium transition-colors"
                >
                  Register here
                </button>
              </p>
            </div>

            {/* Footer */}
            <div className="mt-5 pt-5 border-t border-white/[0.05]">
              <div className="flex items-center gap-2 text-slate-500 text-xs justify-center">
                <Lock className="w-3.5 h-3.5" />
                <span>Authorized personnel only. All access is monitored.</span>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="text-center text-slate-600 text-[11px] mt-6 tracking-wide"
        >
          Authorized law enforcement personnel only. All access is monitored and logged.
        </motion.p>
      </motion.div>
    </div>
  )
}
