import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useParams, Link } from 'react-router-dom'
import {
  Shield, Badge, MapPin, Building2, Clock, FolderOpen,
  CheckCircle, AlertTriangle, TrendingUp, Activity, Mail,
  ArrowLeft, Star, Award,
} from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import api from '../api/client'
import { useAuthStore } from '../store/authStore'

interface OfficerProfile {
  id: number
  username: string
  email: string
  full_name: string
  role: string
  station_id: string | null
  badge_number: string | null
  department: string | null
  phone: string | null
  is_active: boolean
  last_login: string | null
  created_at: string
}

interface OfficerStats {
  total_cases: number
  active_cases: number
  closed_cases: number
  high_priority_cases: number
  total_evidence: number
  total_documents: number
  cases_by_status: Record<string, number>
  recent_cases: Array<{
    id: number
    public_id: string
    fir_number: string
    title: string | null
    status: string
    priority: string
    complainant_name: string
    created_at: string
  }>
}

const ROLE_COLORS: Record<string, string> = {
  super_admin: 'from-red-600 to-red-800',
  commissioner: 'from-purple-600 to-purple-800',
  acp: 'from-blue-600 to-blue-800',
  sho: 'from-cyan-600 to-cyan-800',
  inspector: 'from-green-600 to-green-800',
  sub_inspector: 'from-yellow-600 to-yellow-800',
  constable: 'from-orange-600 to-orange-800',
}

const ROLE_BADGE_COLORS: Record<string, string> = {
  super_admin: 'bg-red-500/10 text-red-400 border-red-500/20',
  commissioner: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  acp: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  sho: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  inspector: 'bg-green-500/10 text-green-400 border-green-500/20',
  sub_inspector: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  constable: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
}

const STATUS_COLORS: Record<string, string> = {
  registered: '#3b82f6',
  investigating: '#f59e0b',
  chargesheet_filed: '#10b981',
  closed: '#64748b',
}

const PRIORITY_BADGE: Record<string, string> = {
  critical: 'bg-red-500/10 text-red-400',
  high: 'bg-orange-500/10 text-orange-400',
  medium: 'bg-yellow-500/10 text-yellow-400',
  low: 'bg-green-500/10 text-green-400',
}

const STATUS_BADGE: Record<string, string> = {
  registered: 'bg-blue-500/20 text-blue-400',
  investigating: 'bg-yellow-500/20 text-yellow-400',
  chargesheet_filed: 'bg-green-500/20 text-green-400',
  closed: 'bg-dark-500/20 text-dark-300',
}

export default function OfficerProfilePage() {
  const { userId } = useParams()
  const { user: currentUser } = useAuthStore()
  const [profile, setProfile] = useState<OfficerProfile | null>(null)
  const [stats, setStats] = useState<OfficerStats | null>(null)
  const [loading, setLoading] = useState(true)

  const targetId = userId || currentUser?.id

  useEffect(() => {
    if (!targetId) return
    const fetchProfile = async () => {
      try {
        const [profileRes, statsRes] = await Promise.all([
          api.get(`/api/users/${targetId}/profile`),
          api.get(`/api/users/${targetId}/stats`),
        ])
        setProfile(profileRes.data)
        setStats(statsRes.data)
      } catch {
        if (!userId && currentUser) {
          setProfile({
            id: currentUser.id,
            username: currentUser.username,
            email: currentUser.email || '',
            full_name: currentUser.full_name,
            role: currentUser.role,
            station_id: currentUser.station_id || null,
            badge_number: currentUser.badge_number || null,
            department: currentUser.department || null,
            phone: null,
            is_active: true,
            last_login: null,
            created_at: '',
          })
        }
      } finally {
        setLoading(false)
      }
    }
    fetchProfile()
  }, [targetId])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="card animate-pulse h-48 bg-dark-800/50" />
        <div className="grid grid-cols-4 gap-4">
          {[1,2,3,4].map(i => <div key={i} className="card animate-pulse h-24 bg-dark-800/50" />)}
        </div>
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="text-center py-20">
        <Shield className="w-16 h-16 text-dark-600 mx-auto mb-4" />
        <p className="text-dark-400 text-lg">Officer profile not found</p>
        <Link to="/dashboard" className="btn-primary mt-4 inline-flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>
      </div>
    )
  }

  const roleLabel = profile.role.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  const statusPieData = stats?.cases_by_status
    ? Object.entries(stats.cases_by_status).map(([name, value]) => ({
        name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value,
        color: STATUS_COLORS[name] || '#64748b',
      }))
    : []

  const clearanceRate = stats && stats.total_cases > 0
    ? Math.round((stats.closed_cases / stats.total_cases) * 100)
    : 0

  return (
    <div className="space-y-6">
      {/* Back Navigation */}
      <Link to="/dashboard" className="inline-flex items-center gap-2 text-dark-400 hover:text-white transition-colors text-sm">
        <ArrowLeft className="w-4 h-4" /> Back to Dashboard
      </Link>

      {/* Profile Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative rounded-2xl overflow-hidden border border-dark-700/50"
      >
        {/* Gradient Background */}
        <div className={`absolute inset-0 bg-gradient-to-r ${ROLE_COLORS[profile.role] || 'from-primary-600 to-primary-800'} opacity-10`} />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-dark-900/95" />

        <div className="relative p-8 flex items-start gap-6">
          {/* Avatar */}
          <div className={`w-24 h-24 rounded-2xl bg-gradient-to-br ${ROLE_COLORS[profile.role] || 'from-primary-500 to-primary-700'} flex items-center justify-center shadow-2xl`}>
            <span className="text-3xl font-bold text-white">
              {profile.full_name.split(' ').map(n => n[0]).join('').slice(0, 2)}
            </span>
          </div>

          {/* Info */}
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-bold text-white">{profile.full_name}</h1>
              {profile.is_active && (
                <span className="flex items-center gap-1 text-green-400 text-xs bg-green-500/10 px-2 py-0.5 rounded-full">
                  <CheckCircle className="w-3 h-3" /> Active
                </span>
              )}
            </div>

            <div className="flex items-center gap-3 mt-2">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold border ${ROLE_BADGE_COLORS[profile.role] || ''}`}>
                <Shield className="w-3.5 h-3.5" />
                {roleLabel}
              </span>
              {profile.badge_number && (
                <span className="flex items-center gap-1.5 text-dark-300 text-sm">
                  <Badge className="w-4 h-4 text-yellow-500" />
                  Badge #{profile.badge_number}
                </span>
              )}
            </div>

            <div className="flex items-center gap-5 mt-4 text-sm text-dark-400">
              {profile.department && (
                <span className="flex items-center gap-1.5">
                  <Building2 className="w-4 h-4 text-dark-500" />
                  {profile.department}
                </span>
              )}
              {profile.station_id && (
                <span className="flex items-center gap-1.5">
                  <MapPin className="w-4 h-4 text-dark-500" />
                  Station: {profile.station_id}
                </span>
              )}
              {profile.email && (
                <span className="flex items-center gap-1.5">
                  <Mail className="w-4 h-4 text-dark-500" />
                  {profile.email}
                </span>
              )}
              {profile.last_login && (
                <span className="flex items-center gap-1.5">
                  <Clock className="w-4 h-4 text-dark-500" />
                  Last seen: {new Date(profile.last_login).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>

          {/* Performance Indicator */}
          {stats && (
            <div className="text-right">
              <div className="inline-flex flex-col items-center bg-dark-800/80 rounded-xl p-4 border border-dark-700/50">
                <Award className="w-6 h-6 text-yellow-400 mb-1" />
                <p className="text-2xl font-bold text-white">{clearanceRate}%</p>
                <p className="text-[10px] text-dark-400 uppercase tracking-wider">Clearance Rate</p>
              </div>
            </div>
          )}
        </div>
      </motion.div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { label: 'Total Cases', value: stats.total_cases, icon: FolderOpen, color: 'text-blue-400', bg: 'bg-blue-500/10' },
            { label: 'Active', value: stats.active_cases, icon: Activity, color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
            { label: 'Closed', value: stats.closed_cases, icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/10' },
            { label: 'High Priority', value: stats.high_priority_cases, icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/10' },
            { label: 'Evidence', value: stats.total_evidence, icon: Star, color: 'text-purple-400', bg: 'bg-purple-500/10' },
            { label: 'Documents', value: stats.total_documents, icon: TrendingUp, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
          ].map((card, i) => (
            <motion.div
              key={card.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="rounded-xl bg-dark-900/80 border border-dark-700/50 p-4"
            >
              <div className={`w-8 h-8 rounded-lg ${card.bg} flex items-center justify-center mb-2`}>
                <card.icon className={`w-4 h-4 ${card.color}`} />
              </div>
              <p className="text-xl font-bold text-white">{card.value}</p>
              <p className="text-dark-400 text-[10px] uppercase tracking-wide mt-0.5">{card.label}</p>
            </motion.div>
          ))}
        </div>
      )}

      {/* Case Distribution + Recent Cases */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pie Chart */}
        {statusPieData.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="card"
          >
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-purple-400" /> Case Distribution
            </h3>
            <div className="w-40 h-40 mx-auto">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={statusPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={65} innerRadius={35}>
                    {statusPieData.map((entry, index) => (
                      <Cell key={index} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px', fontSize: '12px' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-2 mt-4">
              {statusPieData.map((item) => (
                <div key={item.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded" style={{ backgroundColor: item.color }} />
                    <span className="text-dark-300 text-xs">{item.name}</span>
                  </div>
                  <span className="text-white font-medium text-xs">{item.value}</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Recent Cases */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card lg:col-span-2"
        >
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <FolderOpen className="w-4 h-4 text-blue-400" /> Recent Cases
          </h3>
          {stats?.recent_cases && stats.recent_cases.length > 0 ? (
            <div className="space-y-2">
              {stats.recent_cases.map((c) => (
                <Link
                  key={c.id}
                  to={`/cases/${c.public_id}`}
                  className="flex items-center justify-between p-3 bg-dark-800/40 rounded-xl hover:bg-dark-800/70 transition-colors border border-dark-700/30"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-medium truncate">
                      {c.title || c.fir_number}
                    </p>
                    <p className="text-dark-500 text-xs mt-0.5">
                      {c.fir_number} • {c.complainant_name}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 ml-3">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_BADGE[c.status] || ''}`}>
                      {c.status.replace(/_/g, ' ')}
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${PRIORITY_BADGE[c.priority] || PRIORITY_BADGE.medium}`}>
                      {c.priority}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <FolderOpen className="w-10 h-10 text-dark-600 mx-auto mb-2" />
              <p className="text-dark-400 text-sm">No cases assigned yet</p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
