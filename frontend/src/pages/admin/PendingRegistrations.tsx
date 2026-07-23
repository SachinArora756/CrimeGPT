import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { UserPlus, Check, X, Ban, RefreshCw, Search, Loader2, Shield, Mail, Phone, Building, MapPin } from 'lucide-react'
import toast from 'react-hot-toast'
import apiClient from '../../api/client'

interface Registration {
  id: number
  username: string
  email: string
  full_name: string
  role: string
  station_id: string | null
  department: string | null
  badge_number: string | null
  mobile_number: string | null
  status: string
  email_verified: boolean
  admin_approved: boolean
  created_at: string
}

interface Stats {
  pending: number
  active: number
  suspended: number
  rejected: number
  total: number
}

const STATUS_TABS = [
  { key: '', label: 'All' },
  { key: 'pending', label: 'Pending' },
  { key: 'active', label: 'Active' },
  { key: 'suspended', label: 'Suspended' },
  { key: 'rejected', label: 'Rejected' },
]

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  active: 'bg-green-500/10 text-green-400 border-green-500/20',
  suspended: 'bg-red-500/10 text-red-400 border-red-500/20',
  rejected: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
}

const ROLE_LABELS: Record<string, string> = {
  acp: 'ACP',
  sho: 'SHO',
  inspector: 'Inspector',
  sub_inspector: 'Sub Inspector',
  constable: 'Constable',
  super_admin: 'Super Admin',
  commissioner: 'Commissioner',
}

export default function PendingRegistrations() {
  const [registrations, setRegistrations] = useState<Registration[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')
  const [selectedUser, setSelectedUser] = useState<Registration | null>(null)
  const [actionModal, setActionModal] = useState<{ user: Registration; action: string } | null>(null)
  const [reason, setReason] = useState('')
  const [actionLoading, setActionLoading] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const params: Record<string, string> = {}
      if (statusFilter) params.status = statusFilter
      if (search) params.search = search
      const [regRes, statsRes] = await Promise.all([
        apiClient.get('/api/admin/registrations', { params }),
        apiClient.get('/api/admin/registrations/stats'),
      ])
      setRegistrations(regRes.data)
      setStats(statsRes.data)
    } catch {
      toast.error('Failed to load registrations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [statusFilter, search])

  const handleAction = async () => {
    if (!actionModal) return
    setActionLoading(true)
    try {
      await apiClient.post(`/api/admin/registrations/${actionModal.user.id}/action`, {
        action: actionModal.action,
        reason: reason || null,
      })
      toast.success(`User ${actionModal.action}d successfully`)
      setActionModal(null)
      setReason('')
      fetchData()
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      toast.error(error.response?.data?.detail || `Failed to ${actionModal.action}`)
    } finally {
      setActionLoading(false)
    }
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <UserPlus className="w-7 h-7 text-blue-400" />
            Registration Management
          </h1>
          <p className="text-slate-400 mt-1">Review and manage officer registrations</p>
        </div>
        <button
          onClick={fetchData}
          className="p-2 bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 transition-colors"
        >
          <RefreshCw className="w-4 h-4 text-slate-400" />
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            { label: 'Total', value: stats.total, color: 'text-white' },
            { label: 'Pending', value: stats.pending, color: 'text-amber-400' },
            { label: 'Active', value: stats.active, color: 'text-green-400' },
            { label: 'Suspended', value: stats.suspended, color: 'text-red-400' },
            { label: 'Rejected', value: stats.rejected, color: 'text-slate-400' },
          ].map((s) => (
            <div key={s.label} className="bg-dark-900/80 border border-dark-700/50 rounded-xl p-3 text-center">
              <p className={`text-xl font-bold ${s.color}`}>{s.value}</p>
              <p className="text-slate-500 text-xs mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex gap-1 bg-dark-900/80 border border-dark-700/50 rounded-xl p-1 overflow-x-auto">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setStatusFilter(tab.key)}
              className={`px-3 py-1.5 text-sm rounded-lg whitespace-nowrap transition-colors ${
                statusFilter === tab.key
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {tab.label}
              {tab.key === 'pending' && stats?.pending ? ` (${stats.pending})` : ''}
            </button>
          ))}
        </div>
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search by name, email, badge..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-dark-900/80 border border-dark-700/50 rounded-xl text-white text-sm focus:outline-none focus:border-blue-500/50"
          />
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
        </div>
      ) : registrations.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          <UserPlus className="w-10 h-10 mx-auto mb-3 opacity-50" />
          <p>No registrations found</p>
        </div>
      ) : (
        <div className="bg-dark-900/80 border border-dark-700/50 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-dark-700/50">
                  <th className="text-left text-slate-400 font-medium px-4 py-3">Officer</th>
                  <th className="text-left text-slate-400 font-medium px-4 py-3">Badge ID</th>
                  <th className="text-left text-slate-400 font-medium px-4 py-3">Rank</th>
                  <th className="text-left text-slate-400 font-medium px-4 py-3">Station</th>
                  <th className="text-left text-slate-400 font-medium px-4 py-3">Email Verified</th>
                  <th className="text-left text-slate-400 font-medium px-4 py-3">Status</th>
                  <th className="text-left text-slate-400 font-medium px-4 py-3">Date</th>
                  <th className="text-right text-slate-400 font-medium px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {registrations.map((reg) => (
                  <tr key={reg.id} className="border-b border-dark-700/30 hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3">
                      <button onClick={() => setSelectedUser(reg)} className="text-left">
                        <p className="text-white font-medium hover:text-blue-400 transition-colors">{reg.full_name}</p>
                        <p className="text-slate-500 text-xs">{reg.email}</p>
                      </button>
                    </td>
                    <td className="px-4 py-3 text-slate-300 font-mono text-xs">{reg.badge_number || '-'}</td>
                    <td className="px-4 py-3 text-slate-300">{ROLE_LABELS[reg.role] || reg.role}</td>
                    <td className="px-4 py-3 text-slate-300">{reg.station_id || '-'}</td>
                    <td className="px-4 py-3">
                      {reg.email_verified ? (
                        <span className="text-green-400 text-xs flex items-center gap-1"><Check className="w-3 h-3" /> Verified</span>
                      ) : (
                        <span className="text-amber-400 text-xs flex items-center gap-1"><X className="w-3 h-3" /> Pending</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 text-xs rounded-full border ${STATUS_COLORS[reg.status] || STATUS_COLORS.pending}`}>
                        {reg.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs">
                      {new Date(reg.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center gap-1 justify-end">
                        {(reg.status === 'pending') && (
                          <>
                            <button
                              onClick={() => setActionModal({ user: reg, action: 'approve' })}
                              className="p-1.5 bg-green-500/10 hover:bg-green-500/20 text-green-400 rounded-lg transition-colors"
                              title="Approve"
                            >
                              <Check className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => setActionModal({ user: reg, action: 'reject' })}
                              className="p-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors"
                              title="Reject"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          </>
                        )}
                        {reg.status === 'active' && (
                          <button
                            onClick={() => setActionModal({ user: reg, action: 'suspend' })}
                            className="p-1.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 rounded-lg transition-colors"
                            title="Suspend"
                          >
                            <Ban className="w-3.5 h-3.5" />
                          </button>
                        )}
                        {(reg.status === 'suspended' || reg.status === 'rejected') && (
                          <button
                            onClick={() => setActionModal({ user: reg, action: 'reactivate' })}
                            className="p-1.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded-lg transition-colors"
                            title="Reactivate"
                          >
                            <RefreshCw className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      <AnimatePresence>
        {selectedUser && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={() => setSelectedUser(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-dark-900 border border-dark-700/50 rounded-2xl p-6 w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Registration Details</h3>
                <button onClick={() => setSelectedUser(null)} className="text-slate-400 hover:text-white">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="space-y-3">
                <DetailRow icon={<Shield className="w-4 h-4" />} label="Name" value={selectedUser.full_name} />
                <DetailRow icon={<Mail className="w-4 h-4" />} label="Email" value={selectedUser.email} />
                <DetailRow icon={<Shield className="w-4 h-4" />} label="Username" value={selectedUser.username} />
                <DetailRow icon={<Shield className="w-4 h-4" />} label="Badge ID" value={selectedUser.badge_number || '-'} />
                <DetailRow icon={<Shield className="w-4 h-4" />} label="Rank" value={ROLE_LABELS[selectedUser.role] || selectedUser.role} />
                <DetailRow icon={<MapPin className="w-4 h-4" />} label="Station" value={selectedUser.station_id || '-'} />
                <DetailRow icon={<Building className="w-4 h-4" />} label="Department" value={selectedUser.department || '-'} />
                <DetailRow icon={<Phone className="w-4 h-4" />} label="Mobile" value={selectedUser.mobile_number || '-'} />
                <DetailRow icon={<Mail className="w-4 h-4" />} label="Email Verified" value={selectedUser.email_verified ? 'Yes' : 'No'} />
                <DetailRow icon={<Shield className="w-4 h-4" />} label="Status" value={selectedUser.status} />
                <DetailRow icon={<Shield className="w-4 h-4" />} label="Registered" value={new Date(selectedUser.created_at).toLocaleString()} />
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Action Confirmation Modal */}
      <AnimatePresence>
        {actionModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={() => { setActionModal(null); setReason('') }}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-dark-900 border border-dark-700/50 rounded-2xl p-6 w-full max-w-sm"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-white mb-2 capitalize">{actionModal.action} User</h3>
              <p className="text-slate-400 text-sm mb-4">
                Are you sure you want to <span className="font-medium text-white">{actionModal.action}</span>{' '}
                <span className="font-medium text-white">{actionModal.user.full_name}</span>?
              </p>

              {actionModal.action === 'reject' && (
                <div className="mb-4">
                  <label className="block text-sm text-slate-400 mb-1.5">Reason (optional)</label>
                  <textarea
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    className="w-full px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-xl text-white text-sm focus:outline-none focus:border-blue-500/50 resize-none"
                    rows={3}
                    placeholder="Enter rejection reason..."
                  />
                </div>
              )}

              <div className="flex gap-3">
                <button
                  onClick={() => { setActionModal(null); setReason('') }}
                  className="flex-1 py-2.5 bg-white/5 hover:bg-white/10 text-white rounded-xl border border-white/10 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAction}
                  disabled={actionLoading}
                  className={`flex-1 py-2.5 text-white font-medium rounded-xl transition-colors disabled:opacity-50 ${
                    actionModal.action === 'approve'
                      ? 'bg-green-600 hover:bg-green-500'
                      : actionModal.action === 'reject'
                      ? 'bg-red-600 hover:bg-red-500'
                      : actionModal.action === 'suspend'
                      ? 'bg-amber-600 hover:bg-amber-500'
                      : 'bg-blue-600 hover:bg-blue-500'
                  }`}
                >
                  {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : `Confirm ${actionModal.action}`}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function DetailRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-3 py-2 border-b border-dark-700/30 last:border-0">
      <span className="text-slate-500">{icon}</span>
      <span className="text-slate-400 text-sm w-24 flex-shrink-0">{label}</span>
      <span className="text-white text-sm">{value}</span>
    </div>
  )
}
