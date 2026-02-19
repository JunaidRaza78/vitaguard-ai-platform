import { motion } from 'framer-motion'
import { Activity, Pill, Calendar, Stethoscope } from 'lucide-react'
import { formatRelativeTime } from '@/lib/utils'
import GlassCard from '@/components/ui/GlassCard'

const eventIcons = {
  vital: Activity,
  medication: Pill,
  appointment: Calendar,
  checkup: Stethoscope,
}

const eventColors = {
  vital: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
  medication: 'bg-violet-500/15 text-violet-400 border-violet-500/30',
  appointment: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  checkup: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
}

export default function FamilyTimeline({ events = [] }) {
  const sampleEvents = events.length > 0 ? events : [
    { id: 1, type: 'vital', member: 'You', description: 'Blood pressure recorded: 120/80', timestamp: new Date(Date.now() - 3600000).toISOString() },
    { id: 2, type: 'medication', member: 'Sarah', description: 'Took morning medication', timestamp: new Date(Date.now() - 7200000).toISOString() },
    { id: 3, type: 'appointment', member: 'You', description: 'Upcoming: Dr. Smith at 3 PM', timestamp: new Date(Date.now() - 14400000).toISOString() },
    { id: 4, type: 'checkup', member: 'Mom', description: 'Annual checkup completed', timestamp: new Date(Date.now() - 86400000).toISOString() },
  ]

  return (
    <GlassCard className="p-5">
      <h3 className="text-sm font-semibold text-white/80 mb-4">Family Timeline</h3>
      <div className="space-y-1">
        {sampleEvents.map((event, i) => {
          const Icon = eventIcons[event.type] || Activity
          return (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className="flex gap-3 relative"
            >
              {/* Timeline line */}
              {i < sampleEvents.length - 1 && (
                <div className="absolute left-[18px] top-10 w-px h-[calc(100%-16px)] bg-white/10" />
              )}
              {/* Icon */}
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 border ${eventColors[event.type]}`}>
                <Icon className="w-4 h-4" />
              </div>
              {/* Content */}
              <div className="flex-1 pb-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-white/60">{event.member}</span>
                  <span className="text-[10px] text-white/30">{formatRelativeTime(event.timestamp)}</span>
                </div>
                <p className="text-sm text-white/80 mt-0.5">{event.description}</p>
              </div>
            </motion.div>
          )
        })}
      </div>
    </GlassCard>
  )
}
