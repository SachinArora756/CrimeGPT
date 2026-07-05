import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Eye, Trash2, Clock, Shield } from 'lucide-react'
import api from '../../api/client'
import toast from 'react-hot-toast'

interface WatchlistItem {
  id: number
  criminal_id: number
  criminal_name: string
  criminal_profile_id: string
  reason: string
  priority: string
  alert_on_match: boolean
  is_active: boolean
  created_at: string
}

export default function WatchlistPage() {
  const navigate = useNavigate()
  const [items, setItems] = useState<WatchlistItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchWatchlist()
  }, [])

  const fetchWatchlist = async () => {
    try {
      const response = await api.get('/api/criminal-intelligence/watchlist')
      setItems(response.data)
    } catch (error) {
      console.error('Failed to fetch watchlist:', error)
    } finally {
      setLoading(false)
    }
  }

  const removeFromWatchlist = async (id: number) => {
    try {
      await api.delete(`/api/criminal-intelligence/watchlist/${id}`)
      setItems(items.filter(i => i.id !== id))
      toast.success('Removed from watchlist')
    } catch {
      toast.error('Failed to remove')
    }
  }

  const priorityColors: Record<string, string> = {
    low: 'text-green-400 bg-green-500/10 border-green-500/20',
    medium: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    high: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
    critical: 'text-red-400 bg-red-500/10 border-red-500/20',
  }

  if (loading) {
    return (
      <div className="space-y-4 p-6">
        <div className="h-8 w-48 skeleton" />
        {[1, 2, 3].map(i => <div key={i} className="h-24 skeleton" />)}
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-red-600 to-red-800 flex items-center justify-center shadow-lg shadow-red-500/20">
          <Eye className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Criminal Watchlist</h1>
          <p className="text-dark-400 text-sm">High-priority targets under surveillance • {items.length} active entries</p>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-16">
          <Eye className="w-16 h-16 text-dark-600 mx-auto mb-4" />
          <p className="text-dark-400">No criminals on watchlist</p>
          <p className="text-dark-500 text-sm mt-1">Add criminals from their profile page</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="rounded-xl bg-dark-900/80 border border-dark-700/50 p-4 flex items-center gap-4 hover:border-red-500/30 transition-colors"
            >
              <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center">
                <Shield className="w-5 h-5 text-red-400" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => navigate(`/criminal-intel/profiles/${item.criminal_profile_id}`)}
                    className="text-sm font-medium text-white hover:text-emerald-400 transition-colors"
                  >
                    {item.criminal_name}
                  </button>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-medium uppercase border ${priorityColors[item.priority]}`}>
                    {item.priority}
                  </span>
                  {item.alert_on_match && (
                    <span className="text-[9px] text-amber-400 bg-amber-500/10 px-1.5 rounded border border-amber-500/20">
                      AUTO-ALERT
                    </span>
                  )}
                </div>
                <p className="text-xs text-dark-400 mt-1">{item.reason}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-dark-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> {new Date(item.created_at).toLocaleDateString()}
                </span>
                <button
                  onClick={() => removeFromWatchlist(item.id)}
                  className="p-2 rounded-lg hover:bg-red-500/10 text-dark-400 hover:text-red-400 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
