import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Clock, ArrowLeft } from 'lucide-react'

export default function PendingApprovalPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-[#0a1628]">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="relative rounded-2xl overflow-hidden">
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-amber-400/10 via-transparent to-transparent p-[1px]">
            <div className="w-full h-full rounded-2xl bg-[#0d1f3c]/80 backdrop-blur-2xl" />
          </div>

          <div className="relative p-8 text-center">
            <div className="w-16 h-16 bg-amber-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <Clock className="w-10 h-10 text-amber-400" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">Pending Approval</h2>
            <p className="text-slate-400 text-sm mb-3">
              Your registration is currently under review by an administrator.
            </p>
            <p className="text-slate-500 text-xs mb-6">
              You will receive an email notification once your account has been approved.
              This process typically takes 1-2 business days.
            </p>

            <button
              onClick={() => navigate('/login')}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-white/5 hover:bg-white/10 text-white font-medium rounded-xl border border-white/10 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Login
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
