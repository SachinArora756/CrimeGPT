import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { ShieldCheck, Eye, EyeOff, Lock, AlertCircle, Fingerprint, Loader2, Wifi, Server } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuthStore } from '../store/authStore'

function MatrixBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
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

    const columns = Math.floor(canvas.width / 20)
    const drops: number[] = Array(columns).fill(1)
    const chars = '01アイウエオカキクケコサシスセソタチツテト'.split('')

    const draw = () => {
      ctx.fillStyle = 'rgba(5, 5, 15, 0.08)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      ctx.fillStyle = 'rgba(220, 38, 38, 0.06)'
      ctx.font = '12px monospace'

      for (let i = 0; i < drops.length; i++) {
        const char = chars[Math.floor(Math.random() * chars.length)]
        ctx.fillText(char, i * 20, drops[i] * 20)
        if (drops[i] * 20 > canvas.height && Math.random() > 0.98) {
          drops[i] = 0
        }
        drops[i]++
      }

      animRef.current = requestAnimationFrame(draw)
    }
    draw()

    return () => {
      window.removeEventListener('resize', resize)
      cancelAnimationFrame(animRef.current)
    }
  }, [])

  return <canvas ref={canvasRef} className="absolute inset-0 pointer-events-none opacity-60" />
}

function SecurityStatusPanel() {
  const [uptime] = useState(() => {
    const start = new Date('2026-01-01T00:00:00Z')
    const now = new Date()
    const diffMs = now.getTime() - start.getTime()
    const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
    return `${days}d ${hours}h`
  })

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.6, duration: 0.5 }}
      className="absolute top-6 left-6 hidden lg:block"
    >
      <div className="bg-black/40 backdrop-blur-lg border border-white/[0.05] rounded-lg p-3 space-y-2 min-w-[200px]">
        <div className="flex items-center gap-2 text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-2">
          <Server className="w-3 h-3" />
          System Status
        </div>
        <StatusItem label="TLS" value="1.3" ok />
        <StatusItem label="Encryption" value="AES-256-GCM" ok />
        <StatusItem label="Uptime" value={uptime} ok />
        <StatusItem label="Audit Log" value="ACTIVE" ok />
        <StatusItem label="Rate Limit" value="ENFORCED" ok />
      </div>
    </motion.div>
  )
}

function StatusItem({ label, value, ok }: { label: string; value: string; ok: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4 py-0.5">
      <span className="text-[10px] text-slate-600 font-mono">{label}</span>
      <div className="flex items-center gap-1.5">
        <div className={`w-1.5 h-1.5 rounded-full ${ok ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
        <span className={`text-[10px] font-mono ${ok ? 'text-green-500/80' : 'text-red-500/80'}`}>{value}</span>
      </div>
    </div>
  )
}

export default function AdminLoginPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({ username: '', password: '' })
  const [focused, setFocused] = useState<string | null>(null)

  const { login } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await login(form.username, form.password, 'admin')
      toast.success('Administrative access granted')
      const { forcePasswordChange } = useAuthStore.getState()
      if (forcePasswordChange) {
        navigate('/change-password', { replace: true })
      } else {
        navigate('/admin')
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      setError(error.response?.data?.detail || 'Authentication failed.')
    } finally {
      setLoading(false)
    }
  }

  const usernameActive = focused === 'username' || form.username.length > 0
  const passwordActive = focused === 'password' || form.password.length > 0

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-[#050510]">
      {/* Matrix rain background */}
      <MatrixBackground />

      {/* Gradient overlays */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#050510]/50 to-[#050510]" />
      <motion.div
        animate={{ opacity: [0.3, 0.6, 0.3] }}
        transition={{ duration: 4, repeat: Infinity }}
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-red-900/10 rounded-full blur-[100px]"
      />

      {/* Security status panel */}
      <SecurityStatusPanel />

      {/* Connection indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="absolute top-6 right-6 hidden lg:flex items-center gap-2 text-[10px] font-mono text-green-600"
      >
        <Wifi className="w-3 h-3" />
        <span>SECURE CONNECTION</span>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="w-full max-w-[420px] relative z-10"
      >
        {/* Warning Banner */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-5 p-3 bg-red-500/5 border border-red-500/15 rounded-xl flex items-center gap-3"
          role="alert"
        >
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse flex-shrink-0" />
          <p className="text-red-400/80 text-[11px] font-mono">
            RESTRICTED AREA — All access attempts are forensically logged
          </p>
        </motion.div>

        {/* Logo */}
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0, rotate: -90 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ duration: 0.6, delay: 0.2, type: 'spring', stiffness: 120 }}
            className="relative inline-flex"
          >
            {/* Animated ring */}
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 30, repeat: Infinity, ease: 'linear' }}
              className="absolute -inset-2 rounded-2xl border border-dashed border-red-500/20"
            />
            <motion.div
              animate={{ rotate: -360 }}
              transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
              className="absolute -inset-3 rounded-2xl border border-dotted border-red-500/10"
            />
            <div className="w-[72px] h-[72px] bg-gradient-to-br from-red-900/90 to-slate-950 rounded-2xl flex items-center justify-center border border-red-500/20 shadow-xl shadow-red-900/20 relative">
              <ShieldCheck className="w-9 h-9 text-red-400" />
              {/* Glow */}
              <div className="absolute inset-0 rounded-2xl bg-red-500/5 animate-pulse" />
            </div>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="text-2xl font-bold text-white mt-6 tracking-tight"
          >
            System Administration
          </motion.h1>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="flex items-center justify-center gap-2 mt-2"
          >
            <div className="h-px w-8 bg-gradient-to-r from-transparent to-red-500/30" />
            <p className="text-red-400/60 text-[10px] font-bold uppercase tracking-[0.2em]">Restricted Access</p>
            <div className="h-px w-8 bg-gradient-to-l from-transparent to-red-500/30" />
          </motion.div>
        </div>

        {/* Login Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="relative rounded-2xl overflow-hidden"
        >
          {/* Glass border */}
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-red-500/10 via-transparent to-transparent p-[1px]">
            <div className="w-full h-full rounded-2xl bg-[#0a0a1a]/90 backdrop-blur-2xl" />
          </div>

          <div className="relative p-8">
            <div className="flex items-center gap-2.5 mb-6">
              <Fingerprint className="w-5 h-5 text-slate-600" />
              <h2 className="text-base font-semibold text-slate-300">Administrator Authentication</h2>
            </div>

            {/* Error */}
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
                    animate={{ x: [0, -4, 4, -2, 2, 0] }}
                    transition={{ duration: 0.4 }}
                    className="p-3 bg-red-500/8 border border-red-500/20 rounded-xl flex items-start gap-2.5"
                  >
                    <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                    <p className="text-red-400 text-sm font-mono">{error}</p>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>

            <form onSubmit={handleSubmit} className="space-y-5" role="form" aria-label="Administrator login form">
              {/* Username */}
              <div className="relative">
                <input
                  id="admin-username"
                  type="text"
                  className={`w-full px-4 pt-6 pb-2 bg-black/40 border rounded-xl text-white font-mono placeholder-transparent focus:outline-none transition-all duration-200 ${
                    focused === 'username'
                      ? 'border-red-500/40 ring-1 ring-red-500/10 shadow-[0_0_20px_rgba(220,38,38,0.05)]'
                      : 'border-white/[0.06] hover:border-white/[0.12]'
                  }`}
                  placeholder="Username"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  onFocus={() => setFocused('username')}
                  onBlur={() => setFocused(null)}
                  required
                  autoComplete="username"
                  aria-label="Administrator ID"
                />
                <label
                  htmlFor="admin-username"
                  className={`absolute left-4 transition-all duration-200 pointer-events-none font-mono ${
                    usernameActive
                      ? 'top-2 text-[10px] text-red-400/80 uppercase tracking-wider'
                      : 'top-1/2 -translate-y-1/2 text-sm text-slate-600'
                  }`}
                >
                  Administrator ID
                </label>
              </div>

              {/* Password */}
              <div className="relative">
                <input
                  id="admin-password"
                  type={showPassword ? 'text' : 'password'}
                  className={`w-full px-4 pt-6 pb-2 pr-12 bg-black/40 border rounded-xl text-white font-mono placeholder-transparent focus:outline-none transition-all duration-200 ${
                    focused === 'password'
                      ? 'border-red-500/40 ring-1 ring-red-500/10 shadow-[0_0_20px_rgba(220,38,38,0.05)]'
                      : 'border-white/[0.06] hover:border-white/[0.12]'
                  }`}
                  placeholder="Password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  onFocus={() => setFocused('password')}
                  onBlur={() => setFocused(null)}
                  required
                  autoComplete="current-password"
                  aria-label="Security passphrase"
                />
                <label
                  htmlFor="admin-password"
                  className={`absolute left-4 transition-all duration-200 pointer-events-none font-mono ${
                    passwordActive
                      ? 'top-2 text-[10px] text-red-400/80 uppercase tracking-wider'
                      : 'top-1/2 -translate-y-1/2 text-sm text-slate-600'
                  }`}
                >
                  Security Passphrase
                </label>
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-600 hover:text-white transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              {/* Submit */}
              <motion.button
                type="submit"
                disabled={loading || !form.username || !form.password}
                whileHover={{ scale: loading ? 1 : 1.01 }}
                whileTap={{ scale: loading ? 1 : 0.98 }}
                className="w-full py-3.5 bg-gradient-to-r from-red-900/90 to-red-800/90 hover:from-red-800 hover:to-red-700 text-white font-semibold rounded-xl border border-red-700/30 shadow-lg shadow-red-900/15 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed mt-1"
                aria-label="Authenticate"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Verifying Credentials...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <Lock className="w-4 h-4" />
                    Authenticate
                  </span>
                )}
              </motion.button>
            </form>

            {/* Legal footer */}
            <div className="mt-7 pt-5 border-t border-white/[0.04]">
              <p className="text-slate-700 text-[10px] text-center font-mono leading-relaxed">
                Unauthorized access is a criminal offense under the Information Technology Act, 2000.
                <br />All sessions are cryptographically signed and forensically audited.
              </p>
            </div>
          </div>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.9 }}
          className="text-center text-slate-700 text-[10px] mt-6 font-mono uppercase tracking-wider"
        >
          CrimeGPT v1.0 — Secure Administrative Interface
        </motion.p>
      </motion.div>
    </div>
  )
}
