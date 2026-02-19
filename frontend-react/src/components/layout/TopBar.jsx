import { Bell, Search } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import ThemeToggle from '@/components/ui/ThemeToggle'

export default function TopBar({ title }) {
  const [searchOpen, setSearchOpen] = useState(false)
  const navigate = useNavigate()

  return (
    <header className="h-16 glass-strong border-b border-white/10 flex items-center justify-between px-6 sticky top-0 z-30">
      <h2 className="text-lg font-semibold text-white">{title}</h2>

      <div className="flex items-center gap-3">
        {/* Search */}
        <motion.div
          animate={{ width: searchOpen ? 240 : 40 }}
          className="relative"
        >
          {searchOpen ? (
            <input
              autoFocus
              onBlur={() => setSearchOpen(false)}
              placeholder="Search..."
              className="glass-input w-full pl-10 pr-4 py-2 text-sm"
            />
          ) : null}
          <button
            onClick={() => setSearchOpen(!searchOpen)}
            className={`${searchOpen ? 'absolute left-2 top-1/2 -translate-y-1/2' : ''} p-2 rounded-xl glass glass-hover transition-all`}
          >
            <Search className="w-4 h-4 text-white/60" />
          </button>
        </motion.div>

        {/* Notifications */}
        <button
          onClick={() => navigate('/notifications')}
          className="relative p-2 rounded-xl glass glass-hover transition-all"
        >
          <Bell className="w-4 h-4 text-white/60" />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
        </button>

        {/* Theme toggle */}
        <ThemeToggle />
      </div>
    </header>
  )
}
