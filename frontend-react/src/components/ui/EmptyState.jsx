import { motion } from 'framer-motion'

export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-16 text-center"
    >
      {Icon && (
        <div className="w-16 h-16 rounded-2xl glass flex items-center justify-center mb-4">
          <Icon className="w-8 h-8 text-white/40" />
        </div>
      )}
      <h3 className="text-lg font-medium text-white/70 mb-2">{title}</h3>
      {description && <p className="text-sm text-white/40 max-w-sm mb-6">{description}</p>}
      {action}
    </motion.div>
  )
}
