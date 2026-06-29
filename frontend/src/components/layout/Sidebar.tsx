import { NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  FolderOpen,
  PlusCircle,
  Shield,
  Brain,
  LogOut,
} from 'lucide-react'
import { useAuthStore } from '../../store/authStore'

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/cases', icon: FolderOpen, label: 'Cases' },
  { path: '/cases/new', icon: PlusCircle, label: 'New Case' },
]

export default function Sidebar() {
  const { user, logout } = useAuthStore()

  return (
    <motion.aside
      initial={{ x: -280 }}
      animate={{ x: 0 }}
      className="w-64 bg-dark-900 border-r border-dark-700 flex flex-col"
    >
      <div className="p-6 border-b border-dark-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">CrimeGPT</h1>
            <p className="text-xs text-dark-400">Investigation OS</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors duration-200 ${
                isActive
                  ? 'bg-primary-600/20 text-primary-400 border border-primary-600/30'
                  : 'text-dark-300 hover:bg-dark-800 hover:text-white'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-dark-700">
        <div className="flex items-center gap-3 px-4 py-3">
          <div className="w-8 h-8 bg-dark-600 rounded-full flex items-center justify-center">
            <Brain className="w-4 h-4 text-primary-400" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{user?.full_name}</p>
            <p className="text-xs text-dark-400 capitalize">{user?.role?.replace('_', ' ')}</p>
          </div>
          <button onClick={logout} className="text-dark-400 hover:text-red-400 transition-colors">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </motion.aside>
  )
}
