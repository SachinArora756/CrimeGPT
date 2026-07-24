import { useState, useEffect, useRef } from 'react'
import { Bell, Search, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useNotificationStore } from '../../store/notificationStore'
import api from '../../api/client'

interface SearchResult {
  type: string
  id: string | number
  title: string
  subtitle: string
  status?: string
}

export default function Header() {
  const [showDropdown, setShowDropdown] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [showSearch, setShowSearch] = useState(false)
  const [, setSearching] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const searchRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const {
    notifications,
    unreadCount,
    fetchNotifications,
    fetchUnreadCount,
    markRead,
    markAllRead,
  } = useNotificationStore()

  useEffect(() => {
    fetchUnreadCount()
    const interval = setInterval(fetchUnreadCount, 30000)
    return () => clearInterval(interval)
  }, [fetchUnreadCount])

  useEffect(() => {
    if (showDropdown) fetchNotifications()
  }, [showDropdown, fetchNotifications])

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) setShowDropdown(false)
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) setShowSearch(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  useEffect(() => {
    if (searchQuery.length < 2) { setSearchResults([]); return }
    const timer = setTimeout(async () => {
      setSearching(true)
      try {
        const res = await api.get('/api/dashboard/search', { params: { q: searchQuery } })
        const results: SearchResult[] = [
          ...(res.data.cases || []),
          ...(res.data.officers || []),
          ...(res.data.evidence || []),
        ]
        setSearchResults(results)
        setShowSearch(true)
      } catch {
        setSearchResults([])
      } finally {
        setSearching(false)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  const handleResultClick = (result: SearchResult) => {
    setShowSearch(false)
    setSearchQuery('')
    if (result.type === 'case') navigate(`/cases/${result.id}`)
    else if (result.type === 'officer') navigate(`/admin/users`)
    else if (result.type === 'evidence') navigate(`/evidence/${result.id}`)
  }

  const typeIcons: Record<string, string> = {
    case: '📁',
    officer: '👮',
    evidence: '🔍',
  }

  return (
    <header className="h-14 bg-dark-900/80 backdrop-blur-md border-b border-dark-700/50 flex items-center justify-between px-6">
      {/* Search */}
      <div className="flex items-center gap-4 flex-1" ref={searchRef}>
        <div className="relative max-w-md flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
          <input
            type="text"
            placeholder="Search cases, officers, evidence..."
            className="w-full bg-dark-800/60 border border-dark-700/50 rounded-xl pl-10 pr-4 py-2 text-sm text-white placeholder-dark-400 focus:outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/20 transition-all"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => searchResults.length > 0 && setShowSearch(true)}
          />
          {searchQuery && (
            <button onClick={() => { setSearchQuery(''); setShowSearch(false) }} className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400 hover:text-white">
              <X className="w-3.5 h-3.5" />
            </button>
          )}

          {/* Search Results Dropdown */}
          <AnimatePresence>
            {showSearch && searchResults.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -5 }}
                className="absolute top-full left-0 right-0 mt-2 bg-dark-900 border border-dark-700 rounded-xl shadow-2xl z-50 overflow-hidden max-h-80 overflow-y-auto"
              >
                {searchResults.map((r, i) => (
                  <button
                    key={`${r.type}-${r.id}-${i}`}
                    onClick={() => handleResultClick(r)}
                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-dark-800/60 transition-colors text-left border-b border-dark-800 last:border-0"
                  >
                    <span className="text-base">{typeIcons[r.type] || '📄'}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-white text-sm font-medium truncate">{r.title}</p>
                      <p className="text-dark-400 text-xs truncate">{r.subtitle}</p>
                    </div>
                    <span className="text-[10px] text-dark-500 uppercase bg-dark-800 px-1.5 py-0.5 rounded">{r.type}</span>
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Notifications */}
      <div className="flex items-center gap-3 relative" ref={dropdownRef}>
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="relative p-2 text-dark-400 hover:text-white transition-colors rounded-lg hover:bg-dark-800/60"
        >
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] bg-red-500 rounded-full text-[10px] text-white flex items-center justify-center font-bold px-1"
            >
              {unreadCount > 99 ? '99+' : unreadCount}
            </motion.span>
          )}
        </button>

        <AnimatePresence>
          {showDropdown && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              className="fixed top-14 right-6 w-80 bg-dark-900 border border-dark-700 rounded-xl shadow-2xl z-[100] overflow-hidden"
            >
              <div className="flex items-center justify-between p-4 border-b border-dark-700">
                <h3 className="text-sm font-semibold text-white">Notifications</h3>
                {unreadCount > 0 && (
                  <button onClick={markAllRead} className="text-xs text-primary-400 hover:text-primary-300">
                    Mark all read
                  </button>
                )}
              </div>
              <div className="max-h-80 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="p-8 text-center">
                    <Bell className="w-8 h-8 text-dark-600 mx-auto mb-2" />
                    <p className="text-dark-400 text-sm">No notifications yet</p>
                  </div>
                ) : (
                  notifications.slice(0, 20).map((n) => (
                    <div
                      key={n.id}
                      className={`flex items-start gap-3 p-3 border-b border-dark-800 hover:bg-dark-800/50 cursor-pointer transition-colors ${
                        !n.is_read ? 'bg-primary-600/5' : ''
                      }`}
                      onClick={() => {
                        if (!n.is_read) markRead(n.id)
                        if (n.case_id) { navigate(`/cases/${n.case_id}`); setShowDropdown(false) }
                      }}
                    >
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm ${!n.is_read ? 'text-white font-medium' : 'text-dark-300'}`}>{n.title}</p>
                        <p className="text-xs text-dark-400 mt-0.5 truncate">{n.message}</p>
                        <p className="text-[10px] text-dark-500 mt-1">{new Date(n.created_at).toLocaleString()}</p>
                      </div>
                      {!n.is_read && <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 flex-shrink-0" />}
                    </div>
                  ))
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </header>
  )
}
