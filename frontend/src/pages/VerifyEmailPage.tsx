import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { CheckCircle, XCircle, Loader2, Mail } from 'lucide-react'
import apiClient from '../api/client'

export default function VerifyEmailPage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!token) {
      setStatus('error')
      setMessage('Invalid verification link.')
      return
    }

    const verify = async () => {
      try {
        const res = await apiClient.post('/api/auth/verify-email', { token })
        setStatus('success')
        setMessage(res.data.message || 'Email verified successfully. Your account is pending administrator approval.')
      } catch (err: unknown) {
        const error = err as { response?: { data?: { detail?: string } } }
        setStatus('error')
        setMessage(error.response?.data?.detail || 'Verification failed. The link may be expired or invalid.')
      }
    }
    verify()
  }, [token])

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

          <div className="relative p-8 text-center">
            {status === 'loading' && (
              <>
                <Loader2 className="w-16 h-16 text-blue-400 animate-spin mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-white mb-2">Verifying your email...</h2>
                <p className="text-slate-400 text-sm">Please wait while we confirm your email address.</p>
              </>
            )}

            {status === 'success' && (
              <>
                <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-10 h-10 text-green-400" />
                </div>
                <h2 className="text-xl font-semibold text-white mb-2">Email Verified!</h2>
                <p className="text-slate-400 text-sm mb-6">{message}</p>
                <button
                  onClick={() => navigate('/login')}
                  className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition-colors"
                >
                  Go to Login
                </button>
              </>
            )}

            {status === 'error' && (
              <>
                <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <XCircle className="w-10 h-10 text-red-400" />
                </div>
                <h2 className="text-xl font-semibold text-white mb-2">Verification Failed</h2>
                <p className="text-slate-400 text-sm mb-6">{message}</p>
                <div className="flex gap-3 justify-center">
                  <button
                    onClick={() => navigate('/login')}
                    className="px-6 py-2.5 bg-white/5 hover:bg-white/10 text-white font-medium rounded-xl border border-white/10 transition-colors"
                  >
                    Go to Login
                  </button>
                </div>
              </>
            )}

            <div className="mt-6 pt-5 border-t border-white/[0.05]">
              <div className="flex items-center gap-2 text-slate-500 text-xs justify-center">
                <Mail className="w-3.5 h-3.5" />
                <span>CrimeGPT - AI Investigation System</span>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
