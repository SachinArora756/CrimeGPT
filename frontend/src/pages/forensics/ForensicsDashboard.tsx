import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Microscope, Activity, CheckCircle, XCircle, Clock, Loader2,
  TrendingUp, Zap, BarChart3, ArrowRight, Shield,
  Brain, Layers
} from 'lucide-react'
import api from '../../api/client'

interface DashboardStats {
  total_executions: number
  completed: number
  failed: number
  success_rate: number
  avg_execution_time_ms: number
  by_tool: Record<string, number>
  by_status: Record<string, number>
}

interface RecentExecution {
  execution_id: string
  tool_key: string
  status: string
  input_filename: string | null
  confidence_score: number | null
  execution_time_ms: number | null
  created_at: string
}

export default function ForensicsDashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recent, setRecent] = useState<RecentExecution[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/api/forensic-toolkit/dashboard/stats'),
      api.get('/api/forensic-toolkit/dashboard/recent'),
    ]).then(([statsRes, recentRes]) => {
      setStats(statsRes.data)
      setRecent(recentRes.data)
    }).catch(console.error).finally(() => setLoading(false))
  }, [])

  const statusColors: Record<string, string> = {
    completed: 'text-green-400',
    failed: 'text-red-400',
    running: 'text-amber-400',
    pending: 'text-dark-400',
  }

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="h-20 rounded-2xl bg-dark-800/50 animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-32 rounded-xl bg-dark-800/50 animate-pulse" />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-64 rounded-xl bg-dark-800/50 animate-pulse" />
          <div className="h-64 rounded-xl bg-dark-800/50 animate-pulse" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 blur-lg" />
            <div className="relative w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center shadow-xl shadow-purple-500/20">
              <Microscope className="w-7 h-7 text-white" />
            </div>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Tool Logs</h1>
            <p className="text-dark-400 text-sm">AI-powered forensic analysis & investigation toolkit</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/forensics/ai-investigate')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-purple-600/80 to-blue-600/80 hover:from-purple-500 hover:to-blue-500 text-white text-sm font-medium transition-all shadow-lg shadow-purple-500/10 border border-purple-500/20"
          >
            <Brain className="w-4 h-4" /> AI Copilot
          </button>
          <button
            onClick={() => navigate('/forensics/tools')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white text-sm font-medium transition-all shadow-lg shadow-primary-500/20"
          >
            <Zap className="w-4 h-4" /> Launch Tool
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Executions', value: stats?.total_executions ?? 0, icon: Activity, color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20', glow: 'shadow-purple-500/5' },
          { label: 'Successful', value: stats?.completed ?? 0, icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20', glow: 'shadow-green-500/5' },
          { label: 'Failed', value: stats?.failed ?? 0, icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20', glow: 'shadow-red-500/5' },
          { label: 'Avg Duration', value: stats?.avg_execution_time_ms ? `${(stats.avg_execution_time_ms / 1000).toFixed(1)}s` : '0s', icon: Clock, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20', glow: 'shadow-amber-500/5' },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className={`relative rounded-2xl bg-dark-800/50 border ${stat.border} p-5 shadow-xl ${stat.glow} overflow-hidden group hover:scale-[1.02] transition-transform`}
          >
            <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-white/[0.02] to-transparent rounded-bl-full" />
            <div className={`w-11 h-11 rounded-xl ${stat.bg} border ${stat.border} flex items-center justify-center mb-3`}>
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
            </div>
            <p className="text-2xl font-bold text-white">{stat.value}</p>
            <p className="text-dark-500 text-xs mt-1">{stat.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Success Rate Ring */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="rounded-2xl bg-dark-800/50 border border-dark-700/50 p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-purple-400" /> Success Rate
            </h3>
            <span className="text-[10px] text-dark-500 px-2 py-1 rounded bg-dark-700">All time</span>
          </div>
          <div className="flex items-center justify-center py-4">
            <div className="relative w-36 h-36">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" fill="none" stroke="rgb(30 41 59 / 0.5)" strokeWidth="8" />
                <circle
                  cx="50" cy="50" r="40" fill="none"
                  stroke="url(#successGradient)"
                  strokeWidth="8"
                  strokeDasharray={`${(stats?.success_rate ?? 0) * 2.51} 251`}
                  strokeLinecap="round"
                  className="transition-all duration-1000"
                />
                <defs>
                  <linearGradient id="successGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="rgb(168 85 247)" />
                    <stop offset="100%" stopColor="rgb(59 130 246)" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold text-white">{Math.round(stats?.success_rate ?? 0)}%</span>
                <span className="text-[10px] text-dark-500 mt-0.5">success</span>
              </div>
            </div>
          </div>
          <div className="flex items-center justify-center gap-6 mt-2">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-green-400" />
              <span className="text-xs text-dark-400">Completed: {stats?.completed ?? 0}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-red-400" />
              <span className="text-xs text-dark-400">Failed: {stats?.failed ?? 0}</span>
            </div>
          </div>
        </motion.div>

        {/* Tool Usage */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.45 }}
          className="rounded-2xl bg-dark-800/50 border border-dark-700/50 p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-primary-400" /> Tool Usage
            </h3>
            <div className="flex items-center gap-1.5">
              <Layers className="w-3 h-3 text-dark-500" />
              <span className="text-[10px] text-dark-500">{Object.keys(stats?.by_tool ?? {}).length} tools used</span>
            </div>
          </div>
          <div className="space-y-3 max-h-52 overflow-y-auto pr-2">
            {Object.entries(stats?.by_tool ?? {}).sort(([, a], [, b]) => b - a).slice(0, 10).map(([tool, count], i) => {
              const maxCount = Math.max(...Object.values(stats?.by_tool ?? { x: 1 }))
              const pct = (count / maxCount) * 100
              return (
                <motion.div
                  key={tool}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + i * 0.03 }}
                  className="flex items-center gap-3 group"
                >
                  <span className="text-xs text-dark-300 flex-1 truncate capitalize group-hover:text-white transition-colors">
                    {tool.replace(/_/g, ' ')}
                  </span>
                  <div className="w-32 h-2 bg-dark-700 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-primary-600 to-primary-400 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ delay: 0.6 + i * 0.03, duration: 0.5 }}
                    />
                  </div>
                  <span className="text-xs text-white font-medium w-8 text-right">{count}</span>
                </motion.div>
              )
            })}
          </div>
        </motion.div>
      </div>

      {/* Recent Executions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.55 }}
        className="rounded-2xl bg-dark-800/50 border border-dark-700/50 overflow-hidden shadow-xl"
      >
        <div className="px-6 py-4 border-b border-dark-700/50 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-dark-400" /> Recent Executions
          </h3>
          <button
            onClick={() => navigate('/forensics/history')}
            className="flex items-center gap-1.5 text-xs text-primary-400 hover:text-primary-300 transition-colors group"
          >
            View All <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-700/30">
                <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-6 py-3">Tool</th>
                <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-6 py-3">Input</th>
                <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-6 py-3">Status</th>
                <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-6 py-3">Confidence</th>
                <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-6 py-3">Duration</th>
                <th className="text-left text-dark-500 text-[10px] font-semibold uppercase tracking-wider px-6 py-3">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-700/30">
              {recent.map((exec, i) => (
                <motion.tr
                  key={exec.execution_id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.6 + i * 0.03 }}
                  onClick={() => navigate(`/forensics/execution/${exec.execution_id}`)}
                  className="hover:bg-dark-700/30 cursor-pointer transition-colors group"
                >
                  <td className="px-6 py-3.5">
                    <span className="text-sm text-white font-medium capitalize group-hover:text-primary-300 transition-colors">
                      {exec.tool_key.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-3.5 text-xs text-dark-300 truncate max-w-[180px]">
                    {exec.input_filename || <span className="text-dark-600">—</span>}
                  </td>
                  <td className="px-6 py-3.5">
                    <span className={`inline-flex items-center gap-1 text-xs font-medium capitalize ${statusColors[exec.status]}`}>
                      {exec.status === 'completed' && <CheckCircle className="w-3 h-3" />}
                      {exec.status === 'failed' && <XCircle className="w-3 h-3" />}
                      {exec.status === 'running' && <Loader2 className="w-3 h-3 animate-spin" />}
                      {exec.status}
                    </span>
                  </td>
                  <td className="px-6 py-3.5 text-xs">
                    {exec.confidence_score != null ? (
                      <span className={`font-medium ${
                        exec.confidence_score >= 0.8 ? 'text-green-400' :
                        exec.confidence_score >= 0.5 ? 'text-amber-400' : 'text-red-400'
                      }`}>
                        {Math.round(exec.confidence_score * 100)}%
                      </span>
                    ) : <span className="text-dark-600">—</span>}
                  </td>
                  <td className="px-6 py-3.5 text-xs text-dark-400 font-mono">
                    {exec.execution_time_ms ? `${(exec.execution_time_ms / 1000).toFixed(1)}s` : '—'}
                  </td>
                  <td className="px-6 py-3.5 text-xs text-dark-500">
                    {new Date(exec.created_at).toLocaleDateString()}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
        {recent.length === 0 && (
          <div className="py-12 text-center">
            <Shield className="w-10 h-10 text-dark-600 mx-auto mb-3" />
            <p className="text-dark-400 text-sm">No executions yet</p>
            <p className="text-dark-500 text-xs mt-1">Launch a forensic tool to get started</p>
          </div>
        )}
      </motion.div>
    </div>
  )
}
