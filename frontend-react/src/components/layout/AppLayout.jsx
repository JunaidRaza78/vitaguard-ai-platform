import { Outlet, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import Sidebar from './Sidebar'
import TopBar from './TopBar'

const pageTitles = {
  '/': 'Dashboard',
  '/chat': 'Medical Chat',
  '/documents': 'Documents',
  '/profile': 'Profile',
  '/family': 'Family',
  '/notifications': 'Notifications',
  '/lab-reports': 'Lab Reports',
}

export default function AppLayout() {
  const location = useLocation()
  const title = pageTitles[location.pathname] || 'Family Health Manager'

  return (
    <div className="min-h-screen">
      {/* Animated background */}
      <div className="mesh-gradient" />
      <div className="mesh-blob-3" />

      <Sidebar />

      {/* Main content area - offset for sidebar */}
      <div className="ml-[260px] transition-all duration-300">
        <TopBar title={title} />

        <main className="p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}
