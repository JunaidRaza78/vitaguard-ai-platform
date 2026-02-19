import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

const glows = {
  cyan: 'from-cyan-500/20 to-cyan-600/5 border-cyan-500/20',
  emerald: 'from-emerald-500/20 to-emerald-600/5 border-emerald-500/20',
  violet: 'from-violet-500/20 to-violet-600/5 border-violet-500/20',
  rose: 'from-rose-500/20 to-rose-600/5 border-rose-500/20',
  amber: 'from-amber-500/20 to-amber-600/5 border-amber-500/20',
}

const iconBgs = {
  cyan: 'bg-cyan-500/15 text-cyan-400',
  emerald: 'bg-emerald-500/15 text-emerald-400',
  violet: 'bg-violet-500/15 text-violet-400',
  rose: 'bg-rose-500/15 text-rose-400',
  amber: 'bg-amber-500/15 text-amber-400',
}

export default function KpiCard({ icon: Icon, label, value, change, color = 'cyan', delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className={cn(
        'glass rounded-2xl p-5 border bg-gradient-to-br',
        glows[color]
      )}
    >
      <div className="flex items-start justify-between">
        <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center', iconBgs[color])}>
          <Icon className="w-5 h-5" />
        </div>
        {change && (
          <span className={cn(
            'text-xs font-medium px-2 py-0.5 rounded-full',
            change > 0 ? 'bg-emerald-500/15 text-emerald-400' : 'bg-rose-500/15 text-rose-400'
          )}>
            {change > 0 ? '+' : ''}{change}%
          </span>
        )}
      </div>
      <div className="mt-4">
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: delay + 0.2 }}
          className="text-2xl font-bold text-white"
        >
          {value}
        </motion.p>
        <p className="text-xs text-white/40 mt-1">{label}</p>
      </div>
    </motion.div>
  )
}
