import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Bookmark, Trash2, Clock, Microscope, Search,
  Star, ExternalLink
} from 'lucide-react'
import api from '../../api/client'
import toast from 'react-hot-toast'

interface SavedResult {
  id: number
  execution_id: string
  title: string
  notes: string | null
  is_bookmarked: boolean
  linked_case_id: number | null
  created_at: string
}

export default function SavedResultsPage() {
  const navigate = useNavigate()
  const [results, setResults] = useState<SavedResult[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [deletingId, setDeletingId] = useState<number | null>(null)

  useEffect(() => {
    api.get('/api/forensic-toolkit/saved')
      .then(res => setResults(res.data.items || []))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const handleDelete = async (id: number) => {
    setDeletingId(id)
    try {
      await api.delete(`/api/forensic-toolkit/saved/${id}`)
      setResults(results.filter(r => r.id !== id))
      toast.success('Bookmark removed')
    } catch {
      toast.error('Failed to remove')
    } finally {
      setDeletingId(null)
    }
  }

  const filteredResults = searchTerm
    ? results.filter(r => r.title.toLowerCase().includes(searchTerm.toLowerCase()))
    : results

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="h-20 rounded-2xl bg-dark-800/50 animate-pulse" />
        <div className="space-y-3">
          {[1, 2, 3].map(i => <div key={i} className="h-20 rounded-xl bg-dark-800/50 animate-pulse" />)}
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
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 blur-lg" />
            <div className="relative w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-600 to-orange-600 flex items-center justify-center shadow-xl shadow-amber-500/20">
              <Bookmark className="w-7 h-7 text-white" />
            </div>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Saved Results</h1>
            <p className="text-dark-400 text-sm">{results.length} bookmarked forensic analysis results</p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-amber-500/10 border border-amber-500/20">
          <Star className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-xs text-amber-400 font-medium">{results.length} saved</span>
        </div>
      </div>

      {/* Search */}
      {results.length > 0 && (
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search saved results..."
            className="w-full bg-dark-800/80 border border-dark-700/50 rounded-xl pl-11 pr-4 py-3 text-sm text-white placeholder-dark-500 outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/20 transition-all"
          />
        </div>
      )}

      {/* Empty State */}
      {results.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="relative mb-6">
            <div className="absolute inset-0 rounded-2xl bg-dark-700/30 blur-xl" />
            <div className="relative w-20 h-20 rounded-2xl bg-dark-800 border border-dark-700/50 flex items-center justify-center">
              <Bookmark className="w-9 h-9 text-dark-600" />
            </div>
          </div>
          <p className="text-dark-300 text-sm font-medium">No saved results</p>
          <p className="text-dark-500 text-xs mt-1.5 text-center max-w-sm">
            Bookmark execution results from the Tool Launcher to access them quickly here
          </p>
          <button
            onClick={() => navigate('/forensics/tools')}
            className="mt-5 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary-500/10 text-primary-400 border border-primary-500/20 text-xs font-medium hover:bg-primary-500/20 transition-colors"
          >
            <Microscope className="w-3.5 h-3.5" /> Go to Tool Launcher
          </button>
        </div>
      )}

      {/* Results List */}
      <AnimatePresence>
        <div className="space-y-3">
          {filteredResults.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ delay: i * 0.04 }}
              className="group relative rounded-xl bg-dark-800/50 border border-dark-700/50 p-4 hover:border-amber-500/20 hover:shadow-lg hover:shadow-amber-500/5 transition-all cursor-pointer"
              onClick={() => navigate(`/forensics/execution/${item.execution_id}`)}
            >
              <div className="flex items-center gap-4">
                <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-amber-500/10 to-orange-500/10 border border-amber-500/20 flex items-center justify-center group-hover:scale-105 transition-transform">
                  <Microscope className="w-5 h-5 text-amber-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-white group-hover:text-amber-300 transition-colors truncate">
                      {item.title}
                    </p>
                    <ExternalLink className="w-3 h-3 text-dark-600 group-hover:text-amber-400 opacity-0 group-hover:opacity-100 transition-all" />
                  </div>
                  <div className="flex items-center gap-3 mt-1">
                    {item.notes && (
                      <p className="text-xs text-dark-400 truncate max-w-xs">{item.notes}</p>
                    )}
                    {item.linked_case_id && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-primary-500/10 text-primary-400 border border-primary-500/20">
                        Case #{item.linked_case_id}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1.5 text-xs text-dark-500">
                    <Clock className="w-3 h-3" />
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(item.id) }}
                    disabled={deletingId === item.id}
                    className="p-2.5 rounded-xl hover:bg-red-500/10 text-dark-500 hover:text-red-400 transition-all opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </AnimatePresence>

      {/* No search results */}
      {filteredResults.length === 0 && results.length > 0 && (
        <div className="text-center py-10">
          <Search className="w-8 h-8 text-dark-600 mx-auto mb-3" />
          <p className="text-dark-400 text-sm">No results match "{searchTerm}"</p>
        </div>
      )}
    </div>
  )
}
