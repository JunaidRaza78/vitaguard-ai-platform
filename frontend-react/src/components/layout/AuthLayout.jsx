import { Outlet } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Heart } from 'lucide-react'

export default function AuthLayout() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      {/* Animated background */}
      <div className="mesh-gradient" />
      <div className="mesh-blob-3" />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200, delay: 0.2 }}
            className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center mx-auto mb-4 glow-cyan"
          >
            <Heart className="w-8 h-8 text-white" />
          </motion.div>
          <h1 className="text-2xl font-bold text-white text-glow-cyan">Family Health Manager</h1>
          <p className="text-sm text-white/40 mt-1">AI-Powered Healthcare Assistant</p>
        </div>

        {/* Auth form container */}
        <div className="glass-strong p-8 rounded-2xl">
          <Outlet />
        </div>
      </motion.div>
    </div>
  )
}
