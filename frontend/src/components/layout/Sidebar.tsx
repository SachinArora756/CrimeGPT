import { NavLink, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard,
  FolderOpen,
  PlusCircle,
  Shield,
  LogOut,
  Settings,
  Users,
  KeyRound,
  Activity,
  UserCircle,
  Bell,
  Database,
  FileText,
  HardDrive,
  Microscope,
  Search,
  Bookmark,
  Clock,
  Skull,
  Eye,
  Wrench,
  ChevronsLeft,
  ChevronsRight,
  Brain,
  Lightbulb,
  UserPlus,
} from 'lucide-react'
import { useAuthStore } from '../../store/authStore'

const officerNavItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/cases', icon: FolderOpen, label: 'Cases' },
  { path: '/cases/new', icon: PlusCircle, label: 'New Case' },
  { path: '/my-documents', icon: FileText, label: 'My Documents' },
  { path: '/my-evidence', icon: HardDrive, label: 'My Evidence' },
  { path: '/notifications', icon: Bell, label: 'Notifications' },
  { path: '/profile', icon: UserCircle, label: 'My Profile' },
]

const adminNavItems = [
  { path: '/admin', icon: Settings, label: 'Command Center' },
  { path: '/admin/users', icon: Users, label: 'Users' },
  { path: '/admin/registrations', icon: UserPlus, label: 'Registrations' },
  { path: '/admin/notifications', icon: Bell, label: 'Send Notifications' },
  { path: '/admin/audit', icon: Activity, label: 'Audit Logs' },
  { path: '/admin/knowledge-base', icon: Database, label: 'Knowledge Base' },
]

const criminalIntelItems = [
  { path: '/criminal-intel', icon: Skull, label: 'Intelligence Hub' },
  { path: '/criminal-intel/profiles', icon: Search, label: 'Criminal Profiles' },
  { path: '/criminal-intel/watchlist', icon: Eye, label: 'Watchlist' },
]

const forensicsItems = [
  { path: '/forensics', icon: Microscope, label: 'Forensics Lab' },
  { path: '/forensics/ai-investigate', icon: Brain, label: 'Crime Analyst AI' },
  { path: '/forensics/ieae', icon: Shield, label: 'IEAE Engine' },
  { path: '/forensics/iidse', icon: Lightbulb, label: 'IIDSE Intelligence' },
  { path: '/forensics/tools', icon: Wrench, label: 'Tool Launcher' },
  { path: '/forensics/history', icon: Clock, label: 'Execution History' },
  { path: '/forensics/saved', icon: Bookmark, label: 'Saved Results' },
]

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { user, logout, isAdmin, hasMinRole } = useAuthStore()
  const navigate = useNavigate()
  const isAdminUser = isAdmin()
  const canAccessForensics = hasMinRole('sub_inspector')

  const navItems = isAdminUser ? adminNavItems : officerNavItems

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const roleLabel = user?.role?.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 72 : 256 }}
      transition={{ duration: 0.25, ease: 'easeInOut' }}
      className="h-full bg-dark-900/95 backdrop-blur-md border-r border-dark-700/50 flex flex-col overflow-hidden"
    >
      {/* Brand */}
      <div className="p-4 border-b border-dark-700/50 flex items-center justify-between min-h-[64px]">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center shadow-lg shrink-0 ${
            isAdminUser
              ? 'bg-gradient-to-br from-red-600 to-red-800 shadow-red-500/20'
              : 'bg-gradient-to-br from-primary-600 to-primary-800 shadow-primary-500/20'
          }`}>
            <Shield className="w-5 h-5 text-white" />
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden whitespace-nowrap"
              >
                <h1 className="text-base font-bold text-white tracking-tight">CrimeGPT</h1>
                <p className="text-[10px] text-dark-400 uppercase tracking-wider">
                  {isAdminUser ? 'Admin Console' : 'Investigation OS'}
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Toggle button */}
      <button
        onClick={onToggle}
        className="mx-auto my-2 p-1.5 text-dark-400 hover:text-white hover:bg-dark-800 rounded-lg transition-colors"
        title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? <ChevronsRight className="w-4 h-4" /> : <ChevronsLeft className="w-4 h-4" />}
      </button>

      {/* Navigation */}
      <nav className="flex-1 px-2 space-y-1 overflow-y-auto overflow-x-hidden">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/dashboard' || item.path === '/admin'}
            title={collapsed ? item.label : undefined}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 ${
                isActive
                  ? 'bg-primary-600/10 text-primary-400 border border-primary-600/20 shadow-sm shadow-primary-500/5'
                  : 'text-dark-300 hover:bg-dark-800/80 hover:text-white border border-transparent'
              } ${collapsed ? 'justify-center px-2' : ''}`
            }
          >
            <item.icon className="w-4 h-4 shrink-0" />
            {!collapsed && <span className="text-sm font-medium whitespace-nowrap">{item.label}</span>}
          </NavLink>
        ))}

        {canAccessForensics && (
          <>
            {!collapsed && (
              <div className="pt-4 pb-1 px-3">
                <p className="text-[9px] font-semibold text-emerald-500/80 uppercase tracking-widest">Criminal Intelligence</p>
              </div>
            )}
            {collapsed && <div className="pt-3 border-t border-dark-700/30 mt-3" />}
            {criminalIntelItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/criminal-intel'}
                title={collapsed ? item.label : undefined}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 ${
                    isActive
                      ? 'bg-emerald-600/10 text-emerald-400 border border-emerald-600/20 shadow-sm shadow-emerald-500/5'
                      : 'text-dark-300 hover:bg-dark-800/80 hover:text-white border border-transparent'
                  } ${collapsed ? 'justify-center px-2' : ''}`
                }
              >
                <item.icon className="w-4 h-4 shrink-0" />
                {!collapsed && <span className="text-sm font-medium whitespace-nowrap">{item.label}</span>}
              </NavLink>
            ))}

            {!collapsed && (
              <div className="pt-4 pb-1 px-3">
                <p className="text-[9px] font-semibold text-purple-500/80 uppercase tracking-widest">Digital Forensics</p>
              </div>
            )}
            {collapsed && <div className="pt-3 border-t border-dark-700/30 mt-3" />}
            {forensicsItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/forensics'}
                title={collapsed ? item.label : undefined}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 ${
                    isActive
                      ? 'bg-purple-600/10 text-purple-400 border border-purple-600/20 shadow-sm shadow-purple-500/5'
                      : 'text-dark-300 hover:bg-dark-800/80 hover:text-white border border-transparent'
                  } ${collapsed ? 'justify-center px-2' : ''}`
                }
              >
                <item.icon className="w-4 h-4 shrink-0" />
                {!collapsed && <span className="text-sm font-medium whitespace-nowrap">{item.label}</span>}
              </NavLink>
            ))}
          </>
        )}
      </nav>

      {/* User Section */}
      <div className="p-2 border-t border-dark-700/50">
        {collapsed ? (
          <div className="flex flex-col items-center gap-2 py-2">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-500/20 to-purple-500/20 flex items-center justify-center border border-primary-500/20">
              <span className="text-sm font-bold text-primary-400">
                {user?.full_name?.charAt(0) || '?'}
              </span>
            </div>
            <button
              onClick={handleLogout}
              title="Logout"
              className="p-2 text-dark-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-dark-800/40">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-500/20 to-purple-500/20 flex items-center justify-center border border-primary-500/20 shrink-0">
                <span className="text-sm font-bold text-primary-400">
                  {user?.full_name?.charAt(0) || '?'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{user?.full_name}</p>
                <p className="text-[10px] text-dark-400">{roleLabel}</p>
              </div>
            </div>
            <div className="flex gap-1.5 mt-2 px-1">
              <NavLink
                to={isAdminUser ? '/admin' : '/settings/password'}
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-[11px] text-dark-400 hover:text-white hover:bg-dark-800 rounded-lg transition-colors flex-1"
              >
                <KeyRound className="w-3 h-3" />
                Password
              </NavLink>
              <button
                onClick={handleLogout}
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-[11px] text-dark-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
              >
                <LogOut className="w-3 h-3" />
                Logout
              </button>
            </div>
          </>
        )}
      </div>
    </motion.aside>
  )
}
