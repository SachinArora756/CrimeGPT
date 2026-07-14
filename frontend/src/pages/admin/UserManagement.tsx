import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  UserPlus, Edit2, Shield, X, Search, Unlock,
  RotateCcw, Activity, Clock, Badge, Trash2,
} from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../../api/client'
import { UserRole } from '../../store/authStore'

interface AdminUser {
  id: number
  username: string
  email: string
  full_name: string
  role: UserRole
  station_id: string | null
  badge_number: string | null
  department: string | null
  is_active: boolean
  account_locked: boolean
  last_login: string | null
  created_at: string
}

const ROLES: UserRole[] = ['super_admin', 'commissioner', 'acp', 'sho', 'inspector', 'sub_inspector', 'constable']

const ROLE_COLORS: Record<string, string> = {
  super_admin: 'bg-red-500/10 text-red-400 border-red-500/20',
  commissioner: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  acp: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  sho: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  inspector: 'bg-green-500/10 text-green-400 border-green-500/20',
  sub_inspector: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  constable: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
}

const emptyForm = {
  username: '',
  email: '',
  password: '',
  full_name: '',
  role: 'inspector' as UserRole,
  station_id: '',
  badge_number: '',
  department: '',
}

export default function UserManagement() {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [searchQuery, setSearchQuery] = useState('')

  const fetchUsers = async () => {
    try {
      const params: Record<string, string> = {}
      if (searchQuery) params.search = searchQuery
      const res = await api.get('/api/admin/users', { params })
      setUsers(res.data.users || res.data)
    } catch {
      toast.error('Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchUsers() }, [])

  const openCreate = () => {
    setEditingUser(null)
    setForm(emptyForm)
    setShowModal(true)
  }

  const openEdit = (user: AdminUser) => {
    setEditingUser(user)
    setForm({
      username: user.username,
      email: user.email,
      password: '',
      full_name: user.full_name,
      role: user.role,
      station_id: user.station_id || '',
      badge_number: user.badge_number || '',
      department: user.department || '',
    })
    setShowModal(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingUser) {
        const payload: Record<string, unknown> = { ...form }
        delete payload.password
        if (!payload.station_id) delete payload.station_id
        if (!payload.badge_number) delete payload.badge_number
        if (!payload.department) delete payload.department
        await api.put(`/api/admin/users/${editingUser.id}`, payload)
        toast.success('User updated')
      } else {
        const payload: Record<string, unknown> = { ...form }
        if (!payload.station_id) delete payload.station_id
        if (!payload.badge_number) delete payload.badge_number
        if (!payload.department) delete payload.department
        await api.post('/api/admin/users', payload)
        const isAdminRole = form.role === 'super_admin' || form.role === 'commissioner'
        const loginPortal = isAdminRole ? 'Admin Login (/admin/login)' : 'Officer Login (/login)'
        toast.success(`User created! They should login via ${loginPortal}`, { duration: 5000 })
      }
      setShowModal(false)
      fetchUsers()
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      toast.error(error.response?.data?.detail || 'Operation failed')
    }
  }

  const toggleActive = async (user: AdminUser) => {
    try {
      await api.put(`/api/admin/users/${user.id}/toggle-active`)
      toast.success(user.is_active ? 'User deactivated' : 'User activated')
      fetchUsers()
    } catch {
      toast.error('Failed to toggle user status')
    }
  }

  const unlockAccount = async (user: AdminUser) => {
    try {
      await api.put(`/api/admin/users/${user.id}/unlock`)
      toast.success('Account unlocked')
      fetchUsers()
    } catch {
      toast.error('Failed to unlock account')
    }
  }

  const resetPassword = async (user: AdminUser) => {
    const newPw = `Reset@${Date.now().toString().slice(-6)}`
    try {
      await api.post(`/api/admin/users/${user.id}/reset-password`, { new_password: newPw })
      toast.success(`Password reset. Temp: ${newPw}`)
    } catch {
      toast.error('Failed to reset password')
    }
  }

  const deleteUser = async (user: AdminUser) => {
    if (!confirm(`Are you sure you want to delete "${user.full_name}" (@${user.username})? This action cannot be undone.`)) return
    try {
      await api.delete(`/api/admin/users/${user.id}`)
      toast.success(`User "${user.username}" deleted`)
      fetchUsers()
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      toast.error(error.response?.data?.detail || 'Failed to delete user')
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    fetchUsers()
  }

  const filteredUsers = users

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="card animate-pulse h-16 bg-dark-800/50" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1,2,3,4,5,6].map(i => <div key={i} className="card animate-pulse h-48 bg-dark-800/50" />)}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">User Management</h1>
          <p className="text-dark-400 text-sm mt-1">{users.length} registered officers</p>
        </div>
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <UserPlus className="w-4 h-4" /> Create User
        </button>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
        <input
          type="text"
          placeholder="Search by name, username, badge..."
          className="input pl-10"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </form>

      {/* User Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredUsers.map((user, i) => (
          <motion.div
            key={user.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.03 }}
            className="rounded-xl bg-dark-900/80 border border-dark-700 hover:border-dark-600 transition-all overflow-hidden"
          >
            {/* Status bar */}
            <div className={`h-1 w-full ${user.is_active ? 'bg-green-500' : 'bg-red-500'}`} />

            <div className="p-4">
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500/20 to-purple-500/20 flex items-center justify-center border border-primary-500/20">
                    <span className="text-lg font-bold text-primary-400">
                      {user.full_name.charAt(0)}
                    </span>
                  </div>
                  <div>
                    <p className="text-white font-semibold text-sm">{user.full_name}</p>
                    <p className="text-dark-400 text-xs">@{user.username}</p>
                  </div>
                </div>
                <button
                  onClick={() => openEdit(user)}
                  className="p-1.5 text-dark-400 hover:text-white hover:bg-dark-800 rounded-lg transition-colors"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Role Badge */}
              <div className="mb-3">
                <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium border ${ROLE_COLORS[user.role] || ''}`}>
                  <Shield className="w-3 h-3" />
                  {user.role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </span>
              </div>

              {/* Details */}
              <div className="space-y-1.5 text-xs">
                {user.department && (
                  <div className="flex items-center gap-2 text-dark-300">
                    <Activity className="w-3 h-3 text-dark-500" />
                    <span>{user.department}</span>
                  </div>
                )}
                {user.station_id && (
                  <div className="flex items-center gap-2 text-dark-300">
                    <Shield className="w-3 h-3 text-dark-500" />
                    <span>Station: {user.station_id}</span>
                  </div>
                )}
                {user.badge_number && (
                  <div className="flex items-center gap-2 text-dark-300">
                    <Badge className="w-3 h-3 text-dark-500" />
                    <span>Badge: {user.badge_number}</span>
                  </div>
                )}
                <div className="flex items-center gap-2 text-dark-400">
                  <Clock className="w-3 h-3 text-dark-500" />
                  <span>Last login: {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1.5 mt-4 pt-3 border-t border-dark-800">
                <button
                  onClick={() => toggleActive(user)}
                  className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-medium transition-colors ${
                    user.is_active
                      ? 'bg-green-500/10 text-green-400 hover:bg-green-500/20'
                      : 'bg-red-500/10 text-red-400 hover:bg-red-500/20'
                  }`}
                >
                  {user.is_active ? <Activity className="w-3 h-3" /> : <X className="w-3 h-3" />}
                  {user.is_active ? 'Active' : 'Inactive'}
                </button>
                {user.account_locked && (
                  <button
                    onClick={() => unlockAccount(user)}
                    className="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-medium bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20"
                  >
                    <Unlock className="w-3 h-3" /> Unlock
                  </button>
                )}
                <button
                  onClick={() => resetPassword(user)}
                  className="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-medium bg-dark-800 text-dark-300 hover:text-white hover:bg-dark-700 ml-auto"
                >
                  <RotateCcw className="w-3 h-3" /> Reset PW
                </button>
                <button
                  onClick={() => deleteUser(user)}
                  className="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-medium bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
                >
                  <Trash2 className="w-3 h-3" /> Delete
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-dark-900 border border-dark-700 rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
          >
            <div className="flex items-center justify-between p-6 border-b border-dark-700">
              <h2 className="text-lg font-semibold text-white">
                {editingUser ? 'Edit User' : 'Create User'}
              </h2>
              <button onClick={() => setShowModal(false)} className="text-dark-400 hover:text-white p-1 rounded-lg hover:bg-dark-800">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-dark-400 mb-1">Username</label>
                  <input type="text" className="input" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required disabled={!!editingUser} />
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark-400 mb-1">Full Name</label>
                  <input type="text" className="input" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-dark-400 mb-1">Email</label>
                <input type="email" className="input" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
              </div>

              {!editingUser && (
                <div>
                  <label className="block text-xs font-medium text-dark-400 mb-1">Password</label>
                  <input type="password" className="input" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={10} />
                  <p className="text-dark-500 text-[10px] mt-1">Min 10 chars, upper, lower, digit, special char</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-dark-400 mb-1">Role</label>
                  <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as UserRole })}>
                    {ROLES.map((r) => (
                      <option key={r} value={r}>{r.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark-400 mb-1">Department</label>
                  <input type="text" className="input" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-dark-400 mb-1">Station ID</label>
                  <input type="text" className="input" value={form.station_id} onChange={(e) => setForm({ ...form, station_id: e.target.value })} />
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark-400 mb-1">Badge No.</label>
                  <input type="text" className="input" value={form.badge_number} onChange={(e) => setForm({ ...form, badge_number: e.target.value })} />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-dark-700">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-primary">{editingUser ? 'Update' : 'Create'}</button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  )
}
