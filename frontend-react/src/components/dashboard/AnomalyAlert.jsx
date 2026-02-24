import { motion } from 'framer-motion'
import { AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react'
import { cn } from '@/lib/utils'

const severityColors = {
  high: 'border-rose-500/30 bg-rose-500/5',
  medium: 'border-amber-500/30 bg-amber-500/5',
  low: 'border-emerald-500/30 bg-emerald-500/5',
}

const severityIcons = {
  high: 'text-rose-400',
  medium: 'text-amber-400',
  low: 'text-emerald-400',
}

// Map backend level field to frontend severity
const levelToSeverity = { critical: 'high', warning: 'medium', normal: 'low' }

// Format vital_type snake_case to Title Case
function formatVitalType(vitalType) {
  if (!vitalType) return 'Unknown metric'
  return vitalType.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export default function AnomalyAlert({ anomaly, index = 0 }) {
  // Support both legacy fields (metric/severity/timestamp) and backend fields (vital_type/level/date)
  const metric = anomaly?.metric || formatVitalType(anomaly?.vital_type)
  const severity = anomaly?.severity || levelToSeverity[anomaly?.level] || 'medium'
  const trend = anomaly?.trend || (anomaly?.level === 'critical' ? 'up' : 'down')

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className={cn(
        'glass rounded-xl p-4 border-l-4 flex items-start gap-3',
        severityColors[severity]
      )}
    >
      <div className={cn('mt-0.5', severity === 'high' && 'pulse-neon')}>
        <AlertTriangle className={cn('w-5 h-5', severityIcons[severity])} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium text-white">{metric}</p>
          {trend === 'up' ? (
            <TrendingUp className="w-3 h-3 text-rose-400" />
          ) : (
            <TrendingDown className="w-3 h-3 text-emerald-400" />
          )}
        </div>
        <p className="text-xs text-white/50 mt-1">{anomaly?.message || 'Anomaly detected'}</p>
      </div>
      <span className={cn(
        'text-[10px] font-medium px-2 py-0.5 rounded-full uppercase',
        severity === 'high' ? 'bg-rose-500/15 text-rose-400' :
        severity === 'medium' ? 'bg-amber-500/15 text-amber-400' :
        'bg-emerald-500/15 text-emerald-400'
      )}>
        {severity}
      </span>
    </motion.div>
  )
}
