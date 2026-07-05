import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  FolderOpen,
  FileCheck,
  AlertTriangle,
  PlusCircle,
  ArrowRight,
  HardDrive,
  FileText,
  Activity,
  TrendingUp,
  Brain,
  Shield,
  Clock,
  Zap,
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar, Legend,
} from 'recharts'
import api from '../api/client'
import { useAuthStore } from '../store/authStore'

interface DashboardStats {
  total_cases: number
  active_cases: number
  closed_cases: number
  chargesheet_cases: number
  total_evidence: number
  total_documents: number
  cases_by_status: Record<string, number>
  today_activity: number
  today_new_cases: number
  today_evidence: number
  today_documents: number
  cases_per_day: Array<{ date: string; count: number }>
  crime_categories: Array<{ category: string; count: number }>
  officer_workload: Array<{ name: string; role: string; cases: number }>
  completion_trend: Array<{ date: string; count: number }>
  recent_activity: Array<{ action: string; resource_type: string; resource_id: string; timestamp: string }>
}

interface RecentCase {
  id: number
  public_id: string
  fir_number: string
  title: string | null
  complainant_name: string
  status: string
  priority: string | null
  offense_type: string | null
  created_at: string
}

const CHART_COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#8b5cf6', '#ef4444', '#06b6d4', '#f97316', '#ec4899']
const STATUS_COLORS: Record<string, string> = {
  registered: '#3b82f6',
  investigating: '#f59e0b',
  chargesheet_filed: '#10b981',
  closed: '#64748b',
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentCases, setRecentCases] = useState<RecentCase[]>([])
  const [loading, setLoading] = useState(true)
  const { user } = useAuthStore()

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      const [statsRes, casesRes] = await Promise.all([
        api.get('/api/dashboard/stats'),
        api.get('/api/cases/?per_page=5'),
      ])
      setStats(statsRes.data)
      setRecentCases(casesRes.data.cases)
    } catch {
      // fallback
    } finally {
      setLoading(false)
    }
  }

  const statusPieData = stats?.cases_by_status
    ? Object.entries(stats.cases_by_status).map(([name, value]) => ({
        name: name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value,
        color: STATUS_COLORS[name] || '#64748b',
      }))
    : []

  const priorityColors: Record<string, string> = {
    critical: 'text-red-400 bg-red-500/10 border-red-500/30',
    high: 'text-orange-400 bg-orange-500/10 border-orange-500/30',
    medium: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
    low: 'text-green-400 bg-green-500/10 border-green-500/30',
  }

  const statusColors: Record<string, string> = {
    registered: 'bg-blue-500/20 text-blue-400',
    investigating: 'bg-yellow-500/20 text-yellow-400',
    chargesheet_filed: 'bg-green-500/20 text-green-400',
    closed: 'bg-dark-500/20 text-dark-300',
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div key={i} className="card animate-pulse h-28 bg-dark-800/50" />
          ))}
        </div>
      </div>
    )
  }

  const roleLabel = user?.role?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-primary-600/20 via-primary-700/10 to-dark-900 border border-primary-600/20 p-6"
      >
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-primary-500/5 via-transparent to-transparent" />
        <div className="relative flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-lg shadow-primary-500/20">
              <span className="text-2xl font-bold text-white">
                {user?.full_name?.charAt(0) || 'O'}
              </span>
            </div>
            <div>
              <p className="text-dark-400 text-sm">Welcome back,</p>
              <h1 className="text-2xl font-bold text-white">{user?.full_name || 'Officer'}</h1>
              <div className="flex items-center gap-3 mt-1">
                <span className="inline-flex items-center gap-1 text-xs text-primary-400 bg-primary-500/10 px-2 py-0.5 rounded-full border border-primary-500/20">
                  <Shield className="w-3 h-3" /> {roleLabel}
                </span>
                {user?.station_id && (
                  <span className="text-xs text-dark-400">Station: {user.station_id}</span>
                )}
                {user?.department && (
                  <span className="text-xs text-dark-400">• {user.department}</span>
                )}
                {user?.badge_number && (
                  <span className="text-xs text-dark-400">• Badge: {user.badge_number}</span>
                )}
              </div>
            </div>
          </div>
          <Link to="/cases/new" className="btn-primary flex items-center gap-2 shadow-lg shadow-primary-500/20">
            <PlusCircle className="w-4 h-4" />
            New Case
          </Link>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Cases', value: stats?.total_cases ?? 0, icon: FolderOpen, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20', link: '/cases' },
          { label: 'Active Cases', value: stats?.active_cases ?? 0, icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', link: '/cases' },
          { label: 'Closed Cases', value: stats?.closed_cases ?? 0, icon: FileCheck, color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20', link: '/cases' },
          { label: 'Chargesheet Filed', value: stats?.chargesheet_cases ?? 0, icon: Zap, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20', link: '/cases' },
          { label: 'Evidence Items', value: stats?.total_evidence ?? 0, icon: HardDrive, color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20', link: '/my-evidence' },
          { label: 'Documents', value: stats?.total_documents ?? 0, icon: FileText, color: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/20', link: '/my-documents' },
          { label: "Today's Activity", value: stats?.today_activity ?? 0, icon: Activity, color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20', link: '/cases' },
          { label: 'AI Analyzed', value: stats?.active_cases ?? 0, icon: Brain, color: 'text-pink-400', bg: 'bg-pink-500/10', border: 'border-pink-500/20', link: '/cases' },
        ].map((stat, i) => (
          <Link key={stat.label} to={stat.link}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className={`relative overflow-hidden rounded-xl bg-dark-900/80 border ${stat.border} p-4 hover:scale-[1.02] hover:shadow-lg hover:shadow-primary-500/5 transition-all cursor-pointer`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-dark-400 text-xs font-medium uppercase tracking-wide">{stat.label}</p>
                  <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                </div>
                <div className={`w-10 h-10 rounded-xl ${stat.bg} flex items-center justify-center`}>
                  <stat.icon className={`w-5 h-5 ${stat.color}`} />
                </div>
              </div>
            </motion.div>
          </Link>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cases Per Day - Area Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-primary-400" />
              Cases Per Day
            </h2>
            <span className="text-xs text-dark-400">Last 30 days</span>
          </div>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats?.cases_per_day || []}>
                <defs>
                  <linearGradient id="caseGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} tickFormatter={(v) => v.slice(5)} />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
                  labelStyle={{ color: '#94a3b8' }}
                  itemStyle={{ color: '#3b82f6' }}
                />
                <Area type="monotone" dataKey="count" stroke="#3b82f6" fill="url(#caseGradient)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Crime Category Distribution - Pie Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card"
        >
          <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
            <Shield className="w-4 h-4 text-purple-400" />
            Crime Category Distribution
          </h2>
          <div className="h-52 flex items-center">
            {stats?.crime_categories && stats.crime_categories.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats.crime_categories}
                    dataKey="count"
                    nameKey="category"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    innerRadius={40}
                    paddingAngle={2}
                  >
                    {stats.crime_categories.map((_, index) => (
                      <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
                    labelStyle={{ color: '#94a3b8' }}
                  />
                  <Legend
                    wrapperStyle={{ fontSize: '11px' }}
                    formatter={(value) => <span className="text-dark-300">{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-dark-400 text-sm text-center w-full">No data yet</p>
            )}
          </div>
        </motion.div>
      </div>

      {/* Second Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Investigation Status - Pie */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="card"
        >
          <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
            <Clock className="w-4 h-4 text-yellow-400" />
            Investigation Status
          </h2>
          <div className="h-52">
            {statusPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={statusPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} innerRadius={35}>
                    {statusPieData.map((entry, index) => (
                      <Cell key={index} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }} />
                  <Legend wrapperStyle={{ fontSize: '11px' }} formatter={(value) => <span className="text-dark-300">{value}</span>} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-dark-400 text-sm text-center py-20">No data</p>
            )}
          </div>
        </motion.div>

        {/* Officer Workload - Bar Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="card"
        >
          <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-green-400" />
            Officer Workload
          </h2>
          <div className="h-52">
            {stats?.officer_workload && stats.officer_workload.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats.officer_workload} layout="vertical" margin={{ left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis type="number" tick={{ fontSize: 10, fill: '#64748b' }} allowDecimals={false} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} width={100} />
                  <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }} />
                  <Bar dataKey="cases" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-dark-400 text-sm text-center py-20">No data</p>
            )}
          </div>
        </motion.div>
      </div>

      {/* Case Completion Trend */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="card"
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <FileCheck className="w-4 h-4 text-green-400" />
            Case Completion Trend
          </h2>
          <span className="text-xs text-dark-400">Cases closed per day (30 days)</span>
        </div>
        <div className="h-44">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={stats?.completion_trend || []}>
              <defs>
                <linearGradient id="completionGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} tickFormatter={(v) => v.slice(5)} />
              <YAxis tick={{ fontSize: 10, fill: '#64748b' }} allowDecimals={false} />
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }} />
              <Area type="monotone" dataKey="count" stroke="#10b981" fill="url(#completionGradient)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Recent Cases & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="card lg:col-span-2"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-white">Recent Cases</h2>
            <Link to="/cases" className="text-primary-400 hover:text-primary-300 text-sm flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="space-y-2">
            {recentCases.length === 0 ? (
              <p className="text-dark-400 text-center py-8">No cases yet. Create your first case.</p>
            ) : (
              recentCases.map((c) => (
                <Link
                  key={c.id}
                  to={`/cases/${c.public_id}`}
                  className="flex items-center justify-between p-3 bg-dark-900/60 rounded-xl hover:bg-dark-800 transition-all hover:scale-[1.01] border border-transparent hover:border-dark-700"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-primary-500" />
                    <div>
                      <p className="text-white text-sm font-medium">
                        {c.title || c.fir_number}
                      </p>
                      <p className="text-dark-400 text-xs mt-0.5">
                        {c.fir_number} • {c.complainant_name} {c.offense_type ? `• ${c.offense_type}` : ''}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {c.priority && c.priority !== 'medium' && (
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium border ${priorityColors[c.priority] || ''}`}>
                        {c.priority}
                      </span>
                    )}
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${statusColors[c.status] || ''}`}>
                      {c.status.replace('_', ' ')}
                    </span>
                    <ArrowRight className="w-3 h-3 text-dark-500" />
                  </div>
                </Link>
              ))
            )}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
          className="card"
        >
          <h2 className="text-base font-semibold text-white mb-4">Quick Actions</h2>
          <div className="space-y-2">
            <Link
              to="/cases/new"
              className="flex items-center gap-3 p-3 bg-dark-900/60 rounded-xl hover:bg-dark-800 transition-all border border-transparent hover:border-primary-600/30"
            >
              <div className="w-8 h-8 bg-blue-500/10 rounded-lg flex items-center justify-center">
                <PlusCircle className="w-4 h-4 text-blue-400" />
              </div>
              <span className="text-dark-200 text-sm">Register New FIR</span>
            </Link>
            <Link
              to="/cases"
              className="flex items-center gap-3 p-3 bg-dark-900/60 rounded-xl hover:bg-dark-800 transition-all border border-transparent hover:border-purple-600/30"
            >
              <div className="w-8 h-8 bg-purple-500/10 rounded-lg flex items-center justify-center">
                <FolderOpen className="w-4 h-4 text-purple-400" />
              </div>
              <span className="text-dark-200 text-sm">Browse All Cases</span>
            </Link>
          </div>

          {/* Today's Summary */}
          <div className="mt-6 pt-4 border-t border-dark-700">
            <h3 className="text-xs font-medium text-dark-400 uppercase tracking-wide mb-3">Today's Activity</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-dark-300">New Cases</span>
                <span className="text-white font-medium">{stats?.today_new_cases || 0}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-dark-300">Evidence Uploaded</span>
                <span className="text-white font-medium">{stats?.today_evidence || 0}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-dark-300">Documents Generated</span>
                <span className="text-white font-medium">{stats?.today_documents || 0}</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
