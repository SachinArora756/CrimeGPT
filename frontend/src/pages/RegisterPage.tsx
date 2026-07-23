import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield, Eye, EyeOff, Loader2, Check, X, CheckCircle, ArrowLeft } from 'lucide-react'
import toast from 'react-hot-toast'
import apiClient from '../api/client'

const PASSWORD_RULES = [
  { label: 'At least 10 characters', test: (v: string) => v.length >= 10 },
  { label: 'One uppercase letter', test: (v: string) => /[A-Z]/.test(v) },
  { label: 'One lowercase letter', test: (v: string) => /[a-z]/.test(v) },
  { label: 'One digit', test: (v: string) => /\d/.test(v) },
  { label: 'One special character', test: (v: string) => /[!@#$%^&*()_+\-=\[\]{}|;:'",.<>?/\\~`]/.test(v) },
]

const RANKS = [
  { value: 'acp', label: 'ACP (Assistant Commissioner of Police)' },
  { value: 'sho', label: 'SHO (Station House Officer)' },
  { value: 'inspector', label: 'Inspector' },
  { value: 'sub_inspector', label: 'Sub Inspector' },
  { value: 'constable', label: 'Constable' },
]

interface FormData {
  full_name: string
  email: string
  username: string
  password: string
  confirm_password: string
  badge_number: string
  role: string
  station_id: string
  department: string
  mobile_number: string
}

export default function RegisterPage() {
  const navigate = useNavigate()
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [form, setForm] = useState<FormData>({
    full_name: '',
    email: '',
    username: '',
    password: '',
    confirm_password: '',
    badge_number: '',
    role: '',
    station_id: '',
    department: '',
    mobile_number: '',
  })

  const updateField = (field: keyof FormData, value: string) => {
    setForm({ ...form, [field]: value })
    if (errors[field]) {
      setErrors({ ...errors, [field]: '' })
    }
  }

  const allRulesPassed = PASSWORD_RULES.every((r) => r.test(form.password))
  const passwordsMatch = form.password === form.confirm_password && form.confirm_password.length > 0

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}
    if (!form.full_name.trim()) newErrors.full_name = 'Full name is required'
    if (!form.email.trim()) newErrors.email = 'Email is required'
    if (!form.username.trim()) newErrors.username = 'Username is required'
    else if (!/^[a-zA-Z0-9_]+$/.test(form.username)) newErrors.username = 'Username can only contain letters, numbers, and underscores'
    if (!allRulesPassed) newErrors.password = 'Password does not meet requirements'
    if (!passwordsMatch) newErrors.confirm_password = 'Passwords do not match'
    if (!form.badge_number.trim()) newErrors.badge_number = 'Employee/Badge ID is required'
    if (!form.role) newErrors.role = 'Please select your rank'
    if (!form.station_id.trim()) newErrors.station_id = 'Station is required'
    if (!form.department.trim()) newErrors.department = 'Department is required'
    if (form.mobile_number && !/^\+?[0-9]{10,15}$/.test(form.mobile_number)) {
      newErrors.mobile_number = 'Invalid mobile number format'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    try {
      const payload = { ...form }
      if (!payload.mobile_number) delete (payload as Record<string, unknown>).mobile_number
      await apiClient.post('/api/auth/register', payload)
      setSuccess(true)
      toast.success('Registration submitted!')
    } catch (err: unknown) {
      const error = err as { response?: { status?: number; data?: { detail?: string } } }
      if (error.response?.status === 409) {
        const detail = error.response.data?.detail || ''
        if (detail.includes('Username')) setErrors({ ...errors, username: detail })
        else if (detail.includes('Email')) setErrors({ ...errors, email: detail })
        else if (detail.includes('Badge') || detail.includes('Employee')) setErrors({ ...errors, badge_number: detail })
        else toast.error(detail)
      } else if (error.response?.status === 429) {
        toast.error('Too many registration attempts. Please try again later.')
      } else if (error.response?.status === 422) {
        toast.error('Please check your input and try again.')
      } else {
        toast.error(error.response?.data?.detail || 'Registration failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-[#0a1628]">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-md"
        >
          <div className="relative rounded-2xl overflow-hidden">
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-green-400/10 via-transparent to-transparent p-[1px]">
              <div className="w-full h-full rounded-2xl bg-[#0d1f3c]/80 backdrop-blur-2xl" />
            </div>
            <div className="relative p-8 text-center">
              <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-10 h-10 text-green-400" />
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">Registration Submitted!</h2>
              <p className="text-slate-400 text-sm mb-2">
                Please check your email for a verification link.
              </p>
              <p className="text-slate-500 text-xs mb-6">
                After verifying your email, your account will be reviewed by an administrator.
                You'll receive a notification once approved.
              </p>
              <button
                onClick={() => navigate('/login')}
                className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition-colors"
              >
                Go to Login
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-[#0a1628] py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-lg relative z-10"
      >
        {/* Header */}
        <div className="text-center mb-6">
          <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-blue-700 rounded-2xl flex items-center justify-center mx-auto shadow-lg shadow-blue-500/20">
            <Shield className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white mt-4">Officer Registration</h1>
          <p className="text-slate-400 text-sm mt-1">Create your CrimeGPT account</p>
        </div>

        {/* Form Card */}
        <div className="relative rounded-2xl overflow-hidden">
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-blue-400/10 via-transparent to-transparent p-[1px]">
            <div className="w-full h-full rounded-2xl bg-[#0d1f3c]/80 backdrop-blur-2xl" />
          </div>

          <div className="relative p-6 sm:p-8">
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Full Name */}
              <FieldWrapper label="Full Name" error={errors.full_name}>
                <input
                  type="text"
                  value={form.full_name}
                  onChange={(e) => updateField('full_name', e.target.value)}
                  className={inputClass(errors.full_name)}
                  placeholder="Inspector Sharma"
                  required
                />
              </FieldWrapper>

              {/* Email */}
              <FieldWrapper label="Email Address" error={errors.email}>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => updateField('email', e.target.value)}
                  className={inputClass(errors.email)}
                  placeholder="officer@police.gov.in"
                  required
                />
              </FieldWrapper>

              {/* Username */}
              <FieldWrapper label="Username" error={errors.username}>
                <input
                  type="text"
                  value={form.username}
                  onChange={(e) => updateField('username', e.target.value)}
                  className={inputClass(errors.username)}
                  placeholder="insp_sharma"
                  required
                />
              </FieldWrapper>

              {/* Password */}
              <FieldWrapper label="Password" error={errors.password}>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={form.password}
                    onChange={(e) => updateField('password', e.target.value)}
                    className={inputClass(errors.password) + ' pr-11'}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white transition-colors"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {form.password && (
                  <div className="mt-2 space-y-1">
                    {PASSWORD_RULES.map((rule) => (
                      <div key={rule.label} className="flex items-center gap-2 text-xs">
                        {rule.test(form.password) ? (
                          <Check className="w-3 h-3 text-green-400" />
                        ) : (
                          <X className="w-3 h-3 text-slate-500" />
                        )}
                        <span className={rule.test(form.password) ? 'text-green-400' : 'text-slate-500'}>
                          {rule.label}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </FieldWrapper>

              {/* Confirm Password */}
              <FieldWrapper label="Confirm Password" error={errors.confirm_password}>
                <input
                  type="password"
                  value={form.confirm_password}
                  onChange={(e) => updateField('confirm_password', e.target.value)}
                  className={inputClass(errors.confirm_password)}
                  required
                />
                {form.confirm_password && !passwordsMatch && (
                  <p className="text-red-400 text-xs mt-1">Passwords do not match</p>
                )}
                {passwordsMatch && form.confirm_password && (
                  <p className="text-green-400 text-xs mt-1 flex items-center gap-1">
                    <Check className="w-3 h-3" /> Passwords match
                  </p>
                )}
              </FieldWrapper>

              {/* Badge Number */}
              <FieldWrapper label="Employee / Police ID" error={errors.badge_number}>
                <input
                  type="text"
                  value={form.badge_number}
                  onChange={(e) => updateField('badge_number', e.target.value)}
                  className={inputClass(errors.badge_number)}
                  placeholder="MP-12345"
                  required
                />
              </FieldWrapper>

              {/* Rank (Role) */}
              <FieldWrapper label="Rank" error={errors.role}>
                <select
                  value={form.role}
                  onChange={(e) => updateField('role', e.target.value)}
                  className={inputClass(errors.role) + ' appearance-none'}
                  required
                >
                  <option value="">Select your rank</option>
                  {RANKS.map((r) => (
                    <option key={r.value} value={r.value}>{r.label}</option>
                  ))}
                </select>
              </FieldWrapper>

              {/* Station */}
              <FieldWrapper label="Police Station" error={errors.station_id}>
                <input
                  type="text"
                  value={form.station_id}
                  onChange={(e) => updateField('station_id', e.target.value)}
                  className={inputClass(errors.station_id)}
                  placeholder="Kotwali PS"
                  required
                />
              </FieldWrapper>

              {/* Department */}
              <FieldWrapper label="Department" error={errors.department}>
                <input
                  type="text"
                  value={form.department}
                  onChange={(e) => updateField('department', e.target.value)}
                  className={inputClass(errors.department)}
                  placeholder="Crime Branch"
                  required
                />
              </FieldWrapper>

              {/* Mobile (optional) */}
              <FieldWrapper label="Mobile Number (optional)" error={errors.mobile_number}>
                <input
                  type="tel"
                  value={form.mobile_number}
                  onChange={(e) => updateField('mobile_number', e.target.value)}
                  className={inputClass(errors.mobile_number)}
                  placeholder="+919876543210"
                />
              </FieldWrapper>

              {/* Submit */}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white font-semibold rounded-xl shadow-lg shadow-blue-600/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-6"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Registering...
                  </span>
                ) : (
                  'Register'
                )}
              </button>
            </form>

            {/* Login link */}
            <div className="mt-5 text-center">
              <button
                onClick={() => navigate('/login')}
                className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Already have an account? Sign In
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

function FieldWrapper({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm text-slate-400 mb-1.5">{label}</label>
      {children}
      {error && <p className="text-red-400 text-xs mt-1">{error}</p>}
    </div>
  )
}

function inputClass(error?: string) {
  return `w-full px-4 py-2.5 bg-white/[0.04] border rounded-xl text-white focus:outline-none focus:ring-1 transition-all ${
    error
      ? 'border-red-500/50 focus:border-red-500/60 focus:ring-red-500/20'
      : 'border-white/[0.08] focus:border-blue-500/60 focus:ring-blue-500/20 hover:border-white/[0.15]'
  }`
}
