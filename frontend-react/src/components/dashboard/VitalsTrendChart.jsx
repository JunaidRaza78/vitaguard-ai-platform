import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import GlassCard from '@/components/ui/GlassCard'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-strong p-3 rounded-xl text-sm">
      <p className="text-white/60 mb-1">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} style={{ color: entry.color }} className="font-medium">
          {entry.name}: {entry.value}
        </p>
      ))}
    </div>
  )
}

export default function VitalsTrendChart({ data = [], title = 'Vitals Trend' }) {
  const sampleData = data.length > 0 ? data : [
    { date: 'Mon', heartRate: 72, bp_systolic: 120, bp_diastolic: 80 },
    { date: 'Tue', heartRate: 75, bp_systolic: 118, bp_diastolic: 78 },
    { date: 'Wed', heartRate: 68, bp_systolic: 122, bp_diastolic: 82 },
    { date: 'Thu', heartRate: 71, bp_systolic: 119, bp_diastolic: 79 },
    { date: 'Fri', heartRate: 74, bp_systolic: 121, bp_diastolic: 81 },
    { date: 'Sat', heartRate: 69, bp_systolic: 117, bp_diastolic: 77 },
    { date: 'Sun', heartRate: 73, bp_systolic: 120, bp_diastolic: 80 },
  ]

  return (
    <GlassCard className="p-5">
      <h3 className="text-sm font-semibold text-white/80 mb-4">{title}</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={sampleData}>
            <defs>
              <linearGradient id="gradCyan" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradViolet" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradEmerald" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="date" stroke="rgba(255,255,255,0.3)" fontSize={12} />
            <YAxis stroke="rgba(255,255,255,0.3)" fontSize={12} />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="heartRate"
              name="Heart Rate"
              stroke="#06b6d4"
              fill="url(#gradCyan)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="bp_systolic"
              name="Systolic BP"
              stroke="#8b5cf6"
              fill="url(#gradViolet)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="bp_diastolic"
              name="Diastolic BP"
              stroke="#10b981"
              fill="url(#gradEmerald)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </GlassCard>
  )
}
