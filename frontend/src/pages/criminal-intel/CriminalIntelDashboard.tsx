import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Skull, AlertTriangle, Eye, Users, TrendingUp,
  Search, Shield, Fingerprint, MapPin, Clock
} from 'lucide-react'
import api from '../../api/client'

interface RecentCriminal {
  criminal_id: string
  full_name: string
  danger_level: string
  wanted_status: string
  created_at: string
}

interface Stats {
  total: number
  wanted: number
  most_wanted: number
  by_danger_level: Record<string, number>
  top_gangs: Array<{ name: string; count: number }>
  top_categories: Array<{ category: string; count: number }>
  recent_additions: number
}

export default function CriminalIntelDashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<Stats | null>(null)
  const [recentCriminals, setRecentCriminals] = useState<RecentCriminal[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const [statsRes, recentRes] = await Promise.all([
        api.get('/api/criminal-intelligence/stats'),
        api.get('/api/criminal-intelligence/?page=1&per_page=5'),
      ])
      setStats(statsRes.data)
      setRecentCriminals(recentRes.data.items || [])
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/criminal-intel/profiles?search=${encodeURIComponent(searchQuery)}`)
    }
  }

  const dangerColors: Record<string, string> = {
    low: 'text-green-400 bg-green-500/10 border-green-500/20',
    medium: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    high: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
    extreme: 'text-red-400 bg-red-500/10 border-red-500/20',
  }

  const wantedColors: Record<string, string> = {
    not_wanted: 'text-dark-400',
    wanted: 'text-amber-400',
    most_wanted: 'text-red-400',
    surrendered: 'text-blue-400',
    arrested: 'text-green-400',
    absconding: 'text-purple-400',
  }

  if (loading) {
    return (
      <div className="space-y-4 p-6 animate-fade-in">
        <div className="h-8 w-64 skeleton" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-28 skeleton" />)}
        </div>
        <div className="h-96 skeleton" />
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-600 to-emerald-800 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Skull className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Criminal Intelligence Hub</h1>
            <p className="text-dark-400 text-sm">Central criminal intelligence repository & search system</p>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="relative">
        <div className="flex items-center gap-3 bg-dark-800/80 border border-dark-700/50 rounded-xl px-4 py-3 focus-within:border-emerald-500/50 transition-colors">
          <Search className="w-5 h-5 text-dark-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search criminals by name, ID, gang, alias, vehicle number..."
            className="flex-1 bg-transparent text-white placeholder-dark-400 outline-none text-sm"
          />
          <button
            type="submit"
            className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium rounded-lg transition-colors"
          >
            Search
          </button>
        </div>
      </form>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Criminals', value: stats?.total ?? 0, icon: Users, color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' },
          { label: 'Wanted', value: stats?.wanted ?? 0, icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' },
          { label: 'Most Wanted', value: stats?.most_wanted ?? 0, icon: Shield, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' },
          { label: 'On Watchlist', value: 0, icon: Eye, color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20' },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className={`rounded-xl bg-dark-900/80 border ${stat.border} p-5`}
          >
            <div className={`w-10 h-10 rounded-lg ${stat.bg} flex items-center justify-center mb-3`}>
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
            </div>
            <p className="text-2xl font-bold text-white">{stat.value}</p>
            <p className="text-dark-400 text-xs mt-1">{stat.label}</p>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Danger Level Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="rounded-xl bg-dark-900/80 border border-dark-700/50 p-5"
        >
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" /> Danger Level Distribution
          </h3>
          <div className="space-y-3">
            {Object.entries(stats?.by_danger_level ?? {}).map(([level, count]) => (
              <div key={level} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-medium uppercase border ${dangerColors[level]}`}>
                    {level}
                  </span>
                </div>
                <span className="text-white text-sm font-medium">{count}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Top Gangs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="rounded-xl bg-dark-900/80 border border-dark-700/50 p-5"
        >
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Users className="w-4 h-4 text-emerald-400" /> Top Criminal Gangs
          </h3>
          <div className="space-y-3">
            {(stats?.top_gangs ?? []).slice(0, 6).map((gang, i) => (
              <div key={gang.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-dark-500 text-xs w-4">{i + 1}.</span>
                  <span className="text-dark-200 text-sm">{gang.name}</span>
                </div>
                <span className="text-emerald-400 text-sm font-medium">{gang.count}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Top Crime Categories */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="rounded-xl bg-dark-900/80 border border-dark-700/50 p-5"
        >
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-red-400" /> Crime Categories
          </h3>
          <div className="space-y-3">
            {(stats?.top_categories ?? []).slice(0, 6).map((cat, i) => (
              <div key={cat.category} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-dark-500 text-xs w-4">{i + 1}.</span>
                  <span className="text-dark-200 text-sm capitalize">{cat.category.replace('_', ' ')}</span>
                </div>
                <span className="text-red-400 text-sm font-medium">{cat.count}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Recent Additions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="rounded-xl bg-dark-900/80 border border-dark-700/50 overflow-hidden"
      >
        <div className="px-5 py-4 border-b border-dark-700/50 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-dark-400" /> Recent Additions
          </h3>
          <button
            onClick={() => navigate('/criminal-intel/profiles')}
            className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors"
          >
            View All →
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-dark-900/50">
              <tr>
                <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">ID</th>
                <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">Name</th>
                <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">Danger</th>
                <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">Status</th>
                <th className="text-left text-dark-400 text-xs font-medium px-5 py-3">Added</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-800/50">
              {recentCriminals.map((criminal) => (
                <tr
                  key={criminal.criminal_id}
                  onClick={() => navigate(`/criminal-intel/profiles/${criminal.criminal_id}`)}
                  className="hover:bg-dark-800/50 cursor-pointer transition-colors"
                >
                  <td className="px-5 py-3 text-sm font-mono text-emerald-400">{criminal.criminal_id}</td>
                  <td className="px-5 py-3 text-sm text-white">{criminal.full_name}</td>
                  <td className="px-5 py-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-medium uppercase border ${dangerColors[criminal.danger_level]}`}>
                      {criminal.danger_level}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <span className={`text-xs font-medium ${wantedColors[criminal.wanted_status]}`}>
                      {criminal.wanted_status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-xs text-dark-400">
                    {new Date(criminal.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          onClick={() => navigate('/forensics/tools')}
          className="flex items-center gap-3 p-4 rounded-xl bg-dark-800/50 border border-dark-700/50 hover:border-emerald-500/30 transition-all group"
        >
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center group-hover:bg-emerald-500/20 transition-colors">
            <Fingerprint className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="text-left">
            <p className="text-sm font-medium text-white">Face/Fingerprint Search</p>
            <p className="text-xs text-dark-400">Search criminal database with biometrics</p>
          </div>
        </button>
        <button
          onClick={() => navigate('/criminal-intel/profiles')}
          className="flex items-center gap-3 p-4 rounded-xl bg-dark-800/50 border border-dark-700/50 hover:border-emerald-500/30 transition-all group"
        >
          <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center group-hover:bg-purple-500/20 transition-colors">
            <Search className="w-5 h-5 text-purple-400" />
          </div>
          <div className="text-left">
            <p className="text-sm font-medium text-white">Advanced Search</p>
            <p className="text-xs text-dark-400">Filter by gang, category, location</p>
          </div>
        </button>
        <button
          onClick={() => navigate('/criminal-intel/watchlist')}
          className="flex items-center gap-3 p-4 rounded-xl bg-dark-800/50 border border-dark-700/50 hover:border-emerald-500/30 transition-all group"
        >
          <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center group-hover:bg-red-500/20 transition-colors">
            <MapPin className="w-5 h-5 text-red-400" />
          </div>
          <div className="text-left">
            <p className="text-sm font-medium text-white">Watchlist Alerts</p>
            <p className="text-xs text-dark-400">Monitor high-priority targets</p>
          </div>
        </button>
      </div>
    </div>
  )
}
