import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  FolderOpen,
  FileCheck,
  AlertTriangle,
  TrendingUp,
  PlusCircle,
  ArrowRight,
} from 'lucide-react'
import api from '../api/client'

interface DashboardStats {
  total_cases: number
  active_cases: number
  closed_cases: number
  chargesheet_filed: number
}

interface RecentCase {
  id: number
  fir_number: string
  complainant_name: string
  status: string
  created_at: string
  offense_type: string | null
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    total_cases: 0,
    active_cases: 0,
    closed_cases: 0,
    chargesheet_filed: 0,
  })
  const [recentCases, setRecentCases] = useState<RecentCase[]>([])

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      const response = await api.get('/api/cases/?per_page=5')
      const cases = response.data.cases
      setRecentCases(cases)
      setStats({
        total_cases: response.data.total,
        active_cases: cases.filter((c: RecentCase) => c.status === 'investigating').length,
        closed_cases: cases.filter((c: RecentCase) => c.status === 'closed').length,
        chargesheet_filed: cases.filter((c: RecentCase) => c.status === 'chargesheet_filed').length,
      })
    } catch {
      // Dashboard will show zeros if API fails
    }
  }

  const statCards = [
    { label: 'Total Cases', value: stats.total_cases, icon: FolderOpen, color: 'text-primary-400' },
    { label: 'Active', value: stats.active_cases, icon: AlertTriangle, color: 'text-yellow-400' },
    { label: 'Chargesheet Filed', value: stats.chargesheet_filed, icon: FileCheck, color: 'text-green-400' },
    { label: 'Closed', value: stats.closed_cases, icon: TrendingUp, color: 'text-dark-400' },
  ]

  const statusColors: Record<string, string> = {
    registered: 'bg-blue-500/20 text-blue-400',
    investigating: 'bg-yellow-500/20 text-yellow-400',
    chargesheet_filed: 'bg-green-500/20 text-green-400',
    closed: 'bg-dark-500/20 text-dark-300',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-dark-400 mt-1">Investigation overview and quick actions</p>
        </div>
        <Link to="/cases/new" className="btn-primary flex items-center gap-2">
          <PlusCircle className="w-4 h-4" />
          New Case
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="card"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-dark-400 text-sm">{stat.label}</p>
                <p className="text-3xl font-bold text-white mt-1">{stat.value}</p>
              </div>
              <stat.icon className={`w-8 h-8 ${stat.color}`} />
            </div>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card"
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Recent Cases</h2>
          <Link to="/cases" className="text-primary-400 hover:text-primary-300 text-sm flex items-center gap-1">
            View all <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
        <div className="space-y-3">
          {recentCases.length === 0 ? (
            <p className="text-dark-400 text-center py-8">No cases yet. Create your first case.</p>
          ) : (
            recentCases.map((c) => (
              <Link
                key={c.id}
                to={`/cases/${c.id}`}
                className="flex items-center justify-between p-4 bg-dark-900 rounded-lg hover:bg-dark-800 transition-colors"
              >
                <div>
                  <p className="text-white font-medium">{c.fir_number}</p>
                  <p className="text-dark-400 text-sm">{c.complainant_name}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[c.status] || ''}`}>
                    {c.status.replace('_', ' ')}
                  </span>
                  <ArrowRight className="w-4 h-4 text-dark-500" />
                </div>
              </Link>
            ))
          )}
        </div>
      </motion.div>
    </div>
  )
}
