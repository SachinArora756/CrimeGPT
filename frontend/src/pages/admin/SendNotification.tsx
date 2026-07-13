import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Bell, Send, Users, User, Search, CheckCircle, Loader2, Megaphone, X } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../../api/client'

interface OfficerUser {
  id: number
  full_name: string
  username: string
  role: string
  station_id: string | null
  is_active: boolean
}

type SendMode = 'individual' | 'broadcast'

export default function SendNotification() {
  const [mode, setMode] = useState<SendMode>('individual')
  const [users, setUsers] = useState<OfficerUser[]>([])
  const [selectedUsers, setSelectedUsers] = useState<OfficerUser[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [title, setTitle] = useState('')
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [loadingUsers, setLoadingUsers] = useState(true)
  const [broadcastRole, setBroadcastRole] = useState('')
  const [broadcastStation, setBroadcastStation] = useState('')
  const [sentHistory, setSentHistory] = useState<Array<{ title: string; count: number; time: string }>>([])

  useEffect(() => { fetchUsers() }, [])

  const fetchUsers = async () => {
    try {
      const res = await api.get('/api/admin/users', { params: { per_page: 100 } })
      setUsers(res.data.users.filter((u: OfficerUser) => u.is_active))
    } catch {
      toast.error('Failed to load users')
    } finally {
      setLoadingUsers(false)
    }
  }

  const filteredUsers = users.filter(u => {
    const q = searchQuery.toLowerCase()
    return (
      u.full_name.toLowerCase().includes(q) ||
      u.username.toLowerCase().includes(q) ||
      (u.station_id && u.station_id.toLowerCase().includes(q)) ||
      u.role.toLowerCase().includes(q)
    )
  })

  const toggleUser = (user: OfficerUser) => {
    setSelectedUsers(prev =>
      prev.find(u => u.id === user.id)
        ? prev.filter(u => u.id !== user.id)
        : [...prev, user]
    )
  }

  const selectAll = () => {
    setSelectedUsers(filteredUsers)
  }

  const clearSelection = () => {
    setSelectedUsers([])
  }

  const handleSend = async () => {
    if (!title.trim() || !message.trim()) {
      toast.error('Title and message are required')
      return
    }

    if (mode === 'individual' && selectedUsers.length === 0) {
      toast.error('Select at least one recipient')
      return
    }

    setSending(true)
    try {
      if (mode === 'individual') {
        const res = await api.post('/api/admin/notifications/send', {
          user_ids: selectedUsers.map(u => u.id),
          title: title.trim(),
          message: message.trim(),
        })
        toast.success(res.data.message)
        setSentHistory(prev => [{
          title: title.trim(),
          count: res.data.sent_count,
          time: new Date().toLocaleTimeString(),
        }, ...prev.slice(0, 4)])
      } else {
        const params: Record<string, string> = {}
        if (broadcastRole) params.role = broadcastRole
        if (broadcastStation) params.station_id = broadcastStation
        const res = await api.post('/api/admin/notifications/broadcast', {
          title: title.trim(),
          message: message.trim(),
        }, { params })
        toast.success(res.data.message)
        setSentHistory(prev => [{
          title: title.trim(),
          count: res.data.sent_count,
          time: new Date().toLocaleTimeString(),
        }, ...prev.slice(0, 4)])
      }
      setTitle('')
      setMessage('')
      setSelectedUsers([])
    } catch {
      toast.error('Failed to send notification')
    } finally {
      setSending(false)
    }
  }

  const roleColors: Record<string, string> = {
    constable: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    head_constable: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
    sub_inspector: 'bg-green-500/10 text-green-400 border-green-500/20',
    inspector: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    dsp: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
    sho: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    commissioner: 'bg-red-500/10 text-red-400 border-red-500/20',
    super_admin: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-600/20 rounded-xl flex items-center justify-center">
            <Bell className="w-5 h-5 text-primary-400" />
          </div>
          Send Notifications
        </h1>
        <p className="text-dark-400 text-sm mt-1">Send notifications to officers and staff</p>
      </motion.div>

      {/* Mode Toggle */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex gap-2">
        <button
          onClick={() => setMode('individual')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all border ${
            mode === 'individual'
              ? 'bg-primary-600/10 text-primary-400 border-primary-500/30'
              : 'bg-dark-900/60 text-dark-300 border-dark-700 hover:border-dark-600'
          }`}
        >
          <User className="w-4 h-4" />
          Individual
        </button>
        <button
          onClick={() => setMode('broadcast')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all border ${
            mode === 'broadcast'
              ? 'bg-primary-600/10 text-primary-400 border-primary-500/30'
              : 'bg-dark-900/60 text-dark-300 border-dark-700 hover:border-dark-600'
          }`}
        >
          <Megaphone className="w-4 h-4" />
          Broadcast
        </button>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Recipient Selection */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-1 rounded-2xl bg-dark-900/80 border border-dark-700 overflow-hidden"
        >
          <div className="px-5 py-4 border-b border-dark-700/50">
            <h2 className="text-white font-semibold text-sm flex items-center gap-2">
              <Users className="w-4 h-4 text-primary-400" />
              {mode === 'individual' ? 'Select Recipients' : 'Broadcast Filters'}
            </h2>
          </div>

          {mode === 'individual' ? (
            <div className="p-4 space-y-3">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
                <input
                  type="text"
                  className="w-full bg-dark-800/60 border border-dark-700 rounded-xl pl-9 pr-3 py-2 text-sm text-white placeholder:text-dark-500 focus:outline-none focus:border-primary-500/50"
                  placeholder="Search officers..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                />
              </div>

              {/* Select all / Clear */}
              <div className="flex items-center justify-between">
                <span className="text-dark-400 text-xs">{selectedUsers.length} selected</span>
                <div className="flex gap-2">
                  <button onClick={selectAll} className="text-xs text-primary-400 hover:text-primary-300">Select all</button>
                  <button onClick={clearSelection} className="text-xs text-dark-400 hover:text-white">Clear</button>
                </div>
              </div>

              {/* User List */}
              <div className="space-y-1.5 max-h-[400px] overflow-y-auto">
                {loadingUsers ? (
                  <div className="text-center py-8">
                    <Loader2 className="w-5 h-5 text-dark-400 animate-spin mx-auto" />
                  </div>
                ) : filteredUsers.length === 0 ? (
                  <p className="text-dark-500 text-xs text-center py-6">No users found</p>
                ) : (
                  filteredUsers.map(user => {
                    const isSelected = selectedUsers.some(u => u.id === user.id)
                    return (
                      <button
                        key={user.id}
                        onClick={() => toggleUser(user)}
                        className={`w-full flex items-center gap-3 p-2.5 rounded-xl text-left transition-all border ${
                          isSelected
                            ? 'bg-primary-500/10 border-primary-500/30'
                            : 'bg-dark-800/40 border-transparent hover:border-dark-600'
                        }`}
                      >
                        <div className={`w-5 h-5 rounded-md border flex items-center justify-center flex-shrink-0 transition-all ${
                          isSelected ? 'bg-primary-500 border-primary-500' : 'border-dark-600'
                        }`}>
                          {isSelected && <CheckCircle className="w-3.5 h-3.5 text-white" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-white text-sm font-medium truncate">{user.full_name}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium border ${roleColors[user.role] || 'bg-dark-700 text-dark-300 border-dark-600'}`}>
                              {user.role.replace('_', ' ')}
                            </span>
                            {user.station_id && (
                              <span className="text-dark-500 text-[10px]">{user.station_id}</span>
                            )}
                          </div>
                        </div>
                      </button>
                    )
                  })
                )}
              </div>
            </div>
          ) : (
            /* Broadcast Filters */
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-dark-400 text-xs font-medium mb-1.5">Filter by Role</label>
                <select
                  className="w-full bg-dark-800/60 border border-dark-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500/50"
                  value={broadcastRole}
                  onChange={e => setBroadcastRole(e.target.value)}
                >
                  <option value="">All Roles</option>
                  <option value="constable">Constable</option>
                  <option value="head_constable">Head Constable</option>
                  <option value="sub_inspector">Sub Inspector</option>
                  <option value="inspector">Inspector</option>
                  <option value="dsp">DSP</option>
                  <option value="sho">SHO</option>
                  <option value="commissioner">Commissioner</option>
                </select>
              </div>
              <div>
                <label className="block text-dark-400 text-xs font-medium mb-1.5">Filter by Station</label>
                <input
                  type="text"
                  className="w-full bg-dark-800/60 border border-dark-700 rounded-xl px-3 py-2 text-sm text-white placeholder:text-dark-500 focus:outline-none focus:border-primary-500/50"
                  placeholder="Station ID (leave empty for all)"
                  value={broadcastStation}
                  onChange={e => setBroadcastStation(e.target.value)}
                />
              </div>
              <div className="p-3 bg-yellow-500/5 border border-yellow-500/20 rounded-xl">
                <p className="text-yellow-400 text-xs font-medium flex items-center gap-1.5">
                  <Megaphone className="w-3.5 h-3.5" />
                  Broadcast Notice
                </p>
                <p className="text-dark-400 text-[11px] mt-1">
                  This will send the notification to all active users matching the selected filters.
                </p>
              </div>
            </div>
          )}
        </motion.div>

        {/* Right: Compose */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-2 space-y-4"
        >
          {/* Compose Card */}
          <div className="rounded-2xl bg-dark-900/80 border border-dark-700 overflow-hidden">
            <div className="px-5 py-4 border-b border-dark-700/50">
              <h2 className="text-white font-semibold text-sm flex items-center gap-2">
                <Send className="w-4 h-4 text-primary-400" />
                Compose Notification
              </h2>
            </div>
            <div className="p-5 space-y-4">
              {/* Selected recipients chips */}
              {mode === 'individual' && selectedUsers.length > 0 && (
                <div>
                  <label className="block text-dark-400 text-xs font-medium mb-2">To:</label>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedUsers.map(user => (
                      <span key={user.id} className="inline-flex items-center gap-1 px-2.5 py-1 bg-primary-500/10 text-primary-400 rounded-lg text-xs border border-primary-500/20">
                        {user.full_name}
                        <button onClick={() => toggleUser(user)} className="hover:text-white transition-colors">
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Title */}
              <div>
                <label className="block text-dark-400 text-xs font-medium mb-1.5">Title *</label>
                <input
                  type="text"
                  className="w-full bg-dark-800/60 border border-dark-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-dark-500 focus:outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/20 transition-all"
                  placeholder="Notification title..."
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  maxLength={200}
                />
              </div>

              {/* Message */}
              <div>
                <label className="block text-dark-400 text-xs font-medium mb-1.5">Message *</label>
                <textarea
                  className="w-full bg-dark-800/60 border border-dark-700 rounded-xl px-4 py-3 text-sm text-white placeholder:text-dark-500 focus:outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/20 transition-all resize-none min-h-[120px]"
                  placeholder="Write your notification message..."
                  value={message}
                  onChange={e => setMessage(e.target.value)}
                  maxLength={2000}
                />
                <p className="text-dark-500 text-[10px] mt-1 text-right">{message.length}/2000</p>
              </div>

              {/* Send Button */}
              <div className="flex items-center justify-between pt-2">
                <p className="text-dark-500 text-xs">
                  {mode === 'individual'
                    ? `Sending to ${selectedUsers.length} recipient(s)`
                    : `Broadcasting to ${broadcastRole || 'all'} ${broadcastStation ? `at ${broadcastStation}` : 'users'}`
                  }
                </p>
                <button
                  onClick={handleSend}
                  disabled={sending || !title.trim() || !message.trim() || (mode === 'individual' && selectedUsers.length === 0)}
                  className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 text-white rounded-xl text-sm font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-primary-500/10"
                >
                  {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  {sending ? 'Sending...' : 'Send Notification'}
                </button>
              </div>
            </div>
          </div>

          {/* Sent History */}
          {sentHistory.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="rounded-2xl bg-dark-900/80 border border-dark-700 overflow-hidden"
            >
              <div className="px-5 py-3.5 border-b border-dark-700/50">
                <h3 className="text-white font-semibold text-sm flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  Recently Sent
                </h3>
              </div>
              <div className="p-4 space-y-2">
                {sentHistory.map((item, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-dark-800/40 rounded-xl">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-green-500/10 flex items-center justify-center">
                        <Bell className="w-4 h-4 text-green-400" />
                      </div>
                      <div>
                        <p className="text-white text-sm font-medium">{item.title}</p>
                        <p className="text-dark-400 text-xs">Sent to {item.count} user(s) at {item.time}</p>
                      </div>
                    </div>
                    <CheckCircle className="w-4 h-4 text-green-400" />
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
