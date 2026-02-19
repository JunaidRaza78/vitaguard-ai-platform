import { Sun, Moon } from 'lucide-react'
import { motion } from 'framer-motion'
import useThemeStore from '@/stores/themeStore'

export default function ThemeToggle() {
  const { isDark, toggle } = useThemeStore()

  return (
    <motion.button
      whileTap={{ scale: 0.9 }}
      onClick={toggle}
      className="p-2 rounded-xl glass glass-hover transition-all"
    >
      {isDark ? (
        <Sun className="w-5 h-5 text-amber-400" />
      ) : (
        <Moon className="w-5 h-5 text-violet-400" />
      )}
    </motion.button>
  )
}
