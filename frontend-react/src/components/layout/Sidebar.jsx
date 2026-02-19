import { NavLink, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  MessageCircle,
  FileText,
  User,
  Users,
  Bell,
  FlaskConical,
  LogOut,
  Heart,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { useState } from 'react'
import useAuthStore from '@/stores/authStore'
import { getInitials } from '@/lib/utils'

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/chat', icon: MessageCircle, label: 'Medical Chat' },
  { path: '/documents', icon: FileText, label: 'Documents' },
  { path: '/family', icon: Users, label: 'Family' },
  { path: '/notifications', icon: Bell, label: 'Notifications' },
  { path: '/lab-reports', icon: FlaskConical, label: 'Lab Reports' },
  { path: '/profile', icon: User, label: 'Profile' },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 260 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className="fixed left-0 top-0 h-screen z-40 flex flex-col glass-strong border-r border-white/10"
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-white/10">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center flex-shrink-0">
          <Heart className="w-5 h-5 text-white" />
        </div>
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <h1 className="text-sm font-bold text-white whitespace-nowrap">Family Health</h1>
            <p className="text-[10px] text-white/40">AI Manager</p>
          </motion.div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative ${
                isActive
                  ? 'bg-cyan-500/15 text-cyan-400'
                  : 'text-white/60 hover:text-white hover:bg-white/5'
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <motion.div
                    layoutId="activeNav"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full bg-cyan-400"
                    style={{ boxShadow: '0 0 10px rgba(6, 182, 212, 0.6)' }}
                  />
                )}
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {!collapsed && (
                  <span className="text-sm font-medium whitespace-nowrap">{item.label}</span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User section */}
      <div className="border-t border-white/10 p-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center flex-shrink-0 text-xs font-bold text-white">
            {getInitials(user?.first_name, user?.last_name)}
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user?.first_name} {user?.last_name}
              </p>
              <p className="text-[10px] text-white/40 truncate">{user?.email}</p>
            </div>
          )}
          {!collapsed && (
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-lg hover:bg-white/10 transition-colors text-white/40 hover:text-rose-400"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-20 w-6 h-6 rounded-full glass flex items-center justify-center hover:bg-white/20 transition-colors"
      >
        {collapsed ? (
          <ChevronRight className="w-3 h-3 text-white/60" />
        ) : (
          <ChevronLeft className="w-3 h-3 text-white/60" />
        )}
      </button>
    </motion.aside>
  )
}
