import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import { motion } from 'framer-motion'
import GlassCard from '@/components/ui/GlassCard'

export default function RiskGauge({ label, score = 0, maxScore = 100 }) {
  const percentage = Math.round((score / maxScore) * 100)
  const color = percentage < 30 ? '#10b981' : percentage < 60 ? '#f59e0b' : '#f43f5e'
  const riskLevel = percentage < 30 ? 'Low' : percentage < 60 ? 'Moderate' : 'High'

  const data = [
    { value: percentage },
    { value: 100 - percentage },
  ]

  return (
    <GlassCard className="p-4 text-center">
      <div className="h-32 relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="85%"
              startAngle={180}
              endAngle={0}
              innerRadius={50}
              outerRadius={65}
              dataKey="value"
              stroke="none"
            >
              <Cell fill={color} />
              <Cell fill="rgba(255,255,255,0.05)" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-2">
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-2xl font-bold"
            style={{ color }}
          >
            {percentage}%
          </motion.span>
        </div>
      </div>
      <p className="text-sm font-medium text-white/80 mt-1">{label}</p>
      <p className="text-xs mt-0.5" style={{ color }}>{riskLevel} Risk</p>
    </GlassCard>
  )
}
