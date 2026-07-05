import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Bell, CheckCheck, Trash2, FolderOpen, Upload, FileText, UserPlus, AlertTriangle } from 'lucide-react'
import api from '../api/client'

interface Notification {
  id: number
  type: string
  title: string
  message: string
  case_id: number | null
  is_read: boolean
  created_at: string
}

const TYPE_ICONS: Record<string, typeof Bell> = {
  case_created: FolderOpen,
  case_updated: FolderOpen,
  case_assigned: UserPlus,
  evidence_uploaded: Upload,
  document_generated: FileText,
  status_changed: AlertTriangle,
  system: Bell,
}

const TYPE_COLORS: Record<string, string> = {
  case_created: 'text-blue-400 bg-blue-500/10',
  case_updated: 'text-yellow-400 bg-yellow-500/10',
  case_assigned: 'text-green-400 bg-green-500/10',
  evidence_uploaded: 'text-purple-400 bg-purple-500/10',
  document_generated: 'text-cyan-400 bg-cyan-500/10',
  status_changed: 'text-orange-400 bg-orange-500/10',
  system: 'text-dark-400 bg-dark-700/50',
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { fetchNotifications() }, [])

  const fetchNotifications = async () => {
    try {
      const res = await api.get('/api/notifications/')
      setNotifications(res.data)
    } catch { /* silent */ }
    finally { setLoading(false) }
  }

  const markRead = async (id: number) => {
    try {
      await api.put(`/api/notifications/${id}/read`)
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n))
    } catch { /* silent */ }
  }

  const markAllRead = async () => {
    try {
      await api.put('/api/notifications/mark-all-read')
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
    } catch { /* silent */ }
  }

  const deleteNotification = async (id: number) => {
    try {
      await api.delete(`/api/notifications/${id}`)
      setNotifications(prev => prev.filter(n => n.id !== id))
    } catch { /* silent */ }
  }

  const unreadCount = notifications.filter(n => !n.is_read).length

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map(i => <div key={i} className="card animate-pulse h-20 bg-dark-800/50" />)}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-600/20 rounded-xl flex items-center justify-center">
              <Bell className="w-5 h-5 text-primary-400" />
            </div>
            Notifications
          </h1>
          <p className="text-dark-400 text-sm mt-1">
            {unreadCount > 0 ? `${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}` : 'All caught up'}
          </p>
        </div>
        {unreadCount > 0 && (
          <button onClick={markAllRead} className="btn-secondary flex items-center gap-2 text-sm">
            <CheckCheck className="w-4 h-4" />
            Mark All Read
          </button>
        )}
      </div>

      {notifications.length === 0 ? (
        <div className="card text-center py-16">
          <Bell className="w-12 h-12 text-dark-600 mx-auto mb-3" />
          <p className="text-dark-400">No notifications yet</p>
        </div>
      ) : (
        <div className="space-y-2">
          <AnimatePresence>
            {notifications.map((notif) => {
              const Icon = TYPE_ICONS[notif.type] || Bell
              const colorClass = TYPE_COLORS[notif.type] || TYPE_COLORS.system
              return (
                <motion.div
                  key={notif.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10, height: 0 }}
                  className={`rounded-xl border p-4 transition-all ${
                    notif.is_read
                      ? 'bg-dark-900/40 border-dark-700/30'
                      : 'bg-dark-900/80 border-primary-500/20 shadow-sm shadow-primary-500/5'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${colorClass}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className={`font-medium text-sm ${notif.is_read ? 'text-dark-300' : 'text-white'}`}>
                          {notif.title}
                        </p>
                        <div className="flex items-center gap-1.5">
                          {!notif.is_read && (
                            <div className="w-2 h-2 rounded-full bg-primary-500" />
                          )}
                          <button
                            onClick={() => deleteNotification(notif.id)}
                            className="p-1 text-dark-500 hover:text-red-400 transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                      <p className="text-dark-400 text-xs mt-0.5 line-clamp-2">{notif.message}</p>
                      <div className="flex items-center gap-3 mt-2">
                        <span className="text-dark-500 text-[10px]">{new Date(notif.created_at).toLocaleString()}</span>
                        {notif.case_id && (
                          <Link to={`/cases/${notif.case_id}`} className="text-primary-400 text-[10px] hover:underline">
                            View Case →
                          </Link>
                        )}
                        {!notif.is_read && (
                          <button onClick={() => markRead(notif.id)} className="text-dark-400 text-[10px] hover:text-white">
                            Mark read
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}
