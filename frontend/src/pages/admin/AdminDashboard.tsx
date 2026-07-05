import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Link, useNavigate } from 'react-router-dom'
import {
  Users, FolderOpen, HardDrive, Activity, CheckCircle, XCircle,
  Shield, FileText, TrendingUp,
} from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import api from '../../api/client'

interface Stats {
  total_users: number
  active_users: number
  total_cases: number
  cases_by_status: Record<string, number>
  total_evidence: number
  total_documents: number
}

interface SystemHealth {
  database: string
  qdrant: string
  storage: string
}

interface AdminCase {
  id: number
  public_id: string
  fir_number: string
  title: string | null
  complainant_name: string
  status: string
  priority: string
  offense_type: string | null
  station_id: string | null
  created_at: string
  assigned_officer: { id: number; full_name: string; role: string; station_id: string; department: string } | null
  created_by: { id: number; full_name: string; role: string; station_id: string; department: string } | null
}

const STATUS_COLORS: Record<string, string> = {
  registered: '#3b82f6',
  investigating: '#f59e0b',
  chargesheet_filed: '#10b981',
  closed: '#64748b',
}

export default function AdminDashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<Stats | null>(null)
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [cases, setCases] = useState<AdminCase[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, healthRes, casesRes] = await Promise.all([
          api.get('/api/admin/stats'),
          api.get('/api/admin/system-health'),
          api.get('/api/admin/cases?per_page=10'),
        ])
        setStats(statsRes.data)
        setHealth(healthRes.data)
        setCases(casesRes.data.cases || [])
      } catch (err) {
        console.error('Failed to fetch admin data', err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card animate-pulse h-28 bg-dark-800/50" />
          ))}
        </div>
      </div>
    )
  }

  const statusPieData = stats?.cases_by_status
    ? Object.entries(stats.cases_by_status).map(([name, value]) => ({
        name: name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value,
        color: STATUS_COLORS[name] || '#64748b',
      }))
    : []

  const priorityColors: Record<string, string> = {
    critical: 'text-red-400 bg-red-500/10',
    high: 'text-orange-400 bg-orange-500/10',
    medium: 'text-yellow-400 bg-yellow-500/10',
    low: 'text-green-400 bg-green-500/10',
  }

  const statusBadge: Record<string, string> = {
    registered: 'bg-blue-500/20 text-blue-400',
    investigating: 'bg-yellow-500/20 text-yellow-400',
    chargesheet_filed: 'bg-green-500/20 text-green-400',
    closed: 'bg-dark-500/20 text-dark-300',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Admin Command Center</h1>
          <p className="text-dark-400 text-sm mt-1">System overview and case management</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: 'Total Users', value: stats?.total_users ?? 0, icon: Users, color: 'text-blue-400', bg: 'bg-blue-500/10' },
          { label: 'Active Users', value: stats?.active_users ?? 0, icon: Activity, color: 'text-green-400', bg: 'bg-green-500/10' },
          { label: 'Total Cases', value: stats?.total_cases ?? 0, icon: FolderOpen, color: 'text-purple-400', bg: 'bg-purple-500/10' },
          { label: 'Evidence', value: stats?.total_evidence ?? 0, icon: HardDrive, color: 'text-orange-400', bg: 'bg-orange-500/10' },
          { label: 'Documents', value: stats?.total_documents ?? 0, icon: FileText, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
          { label: 'System Health', value: health?.database === 'healthy' ? '✓' : '✗', icon: Shield, color: health?.database === 'healthy' ? 'text-green-400' : 'text-red-400', bg: health?.database === 'healthy' ? 'bg-green-500/10' : 'bg-red-500/10' },
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

      {/* System Health + Cases by Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Shield className="w-4 h-4 text-green-400" /> System Health
          </h3>
          <div className="space-y-3">
            {[
              { label: 'PostgreSQL', status: health?.database },
              { label: 'Qdrant Vector DB', status: health?.qdrant },
              { label: 'File Storage', status: health?.storage },
            ].map((svc) => (
              <div key={svc.label} className="flex items-center justify-between py-2 border-b border-dark-800 last:border-0">
                <span className="text-dark-300 text-sm">{svc.label}</span>
                {svc.status === 'healthy' ? (
                  <span className="flex items-center gap-1 text-green-400 text-xs">
                    <CheckCircle className="w-3.5 h-3.5" /> Online
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-red-400 text-xs">
                    <XCircle className="w-3.5 h-3.5" /> Offline
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="card col-span-2">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-purple-400" /> Case Distribution
          </h3>
          <div className="flex items-center gap-6">
            <div className="w-40 h-40">
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
            <div className="space-y-2 flex-1">
              {statusPieData.map((item) => (
                <div key={item.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded" style={{ backgroundColor: item.color }} />
                    <span className="text-dark-300 text-sm">{item.name}</span>
                  </div>
                  <span className="text-white font-medium text-sm">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Cases Table */}
      <div className="card p-0 overflow-hidden">
        <div className="p-4 border-b border-dark-700 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <FolderOpen className="w-4 h-4 text-blue-400" /> All Cases — Officer Assignment
          </h3>
          <Link to="/admin/users" className="text-xs text-primary-400 hover:text-primary-300">Manage Users →</Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-dark-900/80">
              <tr>
                <th className="text-left text-dark-400 text-xs font-medium px-4 py-3">Case</th>
                <th className="text-left text-dark-400 text-xs font-medium px-4 py-3">Created By</th>
                <th className="text-left text-dark-400 text-xs font-medium px-4 py-3">Assigned Officer</th>
                <th className="text-left text-dark-400 text-xs font-medium px-4 py-3">Station</th>
                <th className="text-left text-dark-400 text-xs font-medium px-4 py-3">Status</th>
                <th className="text-left text-dark-400 text-xs font-medium px-4 py-3">Priority</th>
                <th className="text-left text-dark-400 text-xs font-medium px-4 py-3">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-800">
              {cases.map((c) => (
                <tr key={c.id} className="hover:bg-dark-800/30 transition-colors cursor-pointer" onClick={() => navigate(`/admin/cases/${c.public_id}`)}>
                  <td className="px-4 py-3">
                    <div>
                      <p className="text-white text-sm font-medium">{c.title || c.fir_number}</p>
                      <p className="text-dark-500 text-xs">{c.fir_number} • {c.complainant_name}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {c.created_by ? (
                      <div>
                        <p className="text-dark-200 text-xs">{c.created_by.full_name}</p>
                        <p className="text-dark-500 text-[10px] capitalize">{c.created_by.role.replace('_', ' ')}</p>
                      </div>
                    ) : (
                      <span className="text-dark-500 text-xs">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {c.assigned_officer ? (
                      <div>
                        <p className="text-dark-200 text-xs font-medium">{c.assigned_officer.full_name}</p>
                        <p className="text-dark-500 text-[10px] capitalize">{c.assigned_officer.role.replace('_', ' ')} • {c.assigned_officer.department || '—'}</p>
                      </div>
                    ) : (
                      <span className="text-dark-500 text-xs">Unassigned</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-dark-300 text-xs">{c.station_id || '—'}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${statusBadge[c.status] || ''}`}>
                      {c.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${priorityColors[c.priority] || priorityColors.medium}`}>
                      {c.priority}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-dark-400 text-xs">
                    {c.created_at ? new Date(c.created_at).toLocaleDateString() : '—'}
                  </td>
                </tr>
              ))}
              {cases.length === 0 && (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-dark-400 text-sm">No cases</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
