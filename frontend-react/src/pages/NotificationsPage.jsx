import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bell, Pill, Calendar, AlertTriangle, Filter, Plus, Mail, Clock } from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Modal from '@/components/ui/Modal'
import Badge from '@/components/ui/Badge'
import EmptyState from '@/components/ui/EmptyState'
import { formatRelativeTime } from '@/lib/utils'
import api from '@/lib/axios'
import toast from 'react-hot-toast'

const filterTabs = [
  { key: 'all', label: 'All', icon: Bell },
  { key: 'medication', label: 'Medication', icon: Pill },
  { key: 'appointment', label: 'Appointment', icon: Calendar },
  { key: 'alert', label: 'Alerts', icon: AlertTriangle },
]

const typeColors = {
  medication: 'violet',
  appointment: 'amber',
  alert: 'rose',
  reminder: 'cyan',
  info: 'emerald',
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([])
  const [upcomingNotifications, setUpcomingNotifications] = useState([])
  const [reminders, setReminders] = useState([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [showAddMedModal, setShowAddMedModal] = useState(false)
  const [medForm, setMedForm] = useState({ name: '', dosage: '', time: '08:00', frequency: 'daily' })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [notifRes, upcomingRes, remRes] = await Promise.allSettled([
        api.get('/api/v1/notifications/me'),
        api.get('/api/v1/notifications/me/upcoming'),
        api.get('/api/v1/notifications/me/medications'),
      ])
      if (notifRes.status === 'fulfilled') setNotifications(notifRes.value.data.notifications || notifRes.value.data || [])
      if (upcomingRes.status === 'fulfilled') setUpcomingNotifications(upcomingRes.value.data.notifications || upcomingRes.value.data || [])
      if (remRes.status === 'fulfilled') setReminders(remRes.value.data.reminders || remRes.value.data || [])
    } catch {} finally {
      setLoading(false)
    }
  }

  const filteredNotifications = filter === 'all'
    ? notifications
    : notifications.filter(n => n.type === filter)

  const addMedication = async () => {
    if (!medForm.name || !medForm.dosage) {
      toast.error('Please fill in medication name and dosage')
      return
    }
    try {
      await api.post('/api/v1/notifications/add-medication', {
        medication_name: medForm.name,
        dosage: medForm.dosage,
        frequency: medForm.frequency,
        reminder_times: [medForm.time],
      })
      toast.success('Medication reminder added')
      setShowAddMedModal(false)
      setMedForm({ name: '', dosage: '', time: '08:00', frequency: 'daily' })
      loadData()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add reminder')
    }
  }

  const formatScheduledTime = (scheduledAt) => {
    const date = new Date(scheduledAt)
    const now = new Date()
    const diff = date - now
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))

    if (diff < 0) return 'Past due'
    if (hours < 1) return `in ${minutes}m`
    if (hours < 24) return `in ${hours}h ${minutes}m`
    const days = Math.floor(hours / 24)
    return `in ${days}d`
  }

  const sendTestEmail = async () => {
    try {
      await api.post('/api/v1/notifications/test-email')
      toast.success('Test email sent')
    } catch {
      toast.error('Failed to send test email')
    }
  }

  return (
    <div className="space-y-6">
      {/* Filter Tabs */}
      <div className="flex items-center gap-2 flex-wrap">
        {filterTabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm transition-all ${
              filter === tab.key
                ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30'
                : 'glass text-white/50 hover:text-white/80'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
        <div className="ml-auto flex gap-2">
          <Button onClick={sendTestEmail} variant="ghost" size="sm">
            <Mail className="w-4 h-4" /> Test Email
          </Button>
        </div>
      </div>

      {/* Upcoming Notifications */}
      {upcomingNotifications.length > 0 && (
        <GlassCard glow="cyan">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-white/80">Upcoming Reminders</h3>
            <Badge color="cyan">{upcomingNotifications.length}</Badge>
          </div>
          <div className="space-y-2">
            {upcomingNotifications.slice(0, 5).map((notif, i) => (
              <motion.div
                key={notif.notification_id || i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="glass rounded-lg p-3 flex items-center justify-between"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    notif.type?.includes('medication') ? 'bg-violet-500/15 text-violet-400' :
                    notif.type?.includes('appointment') ? 'bg-amber-500/15 text-amber-400' :
                    'bg-cyan-500/15 text-cyan-400'
                  }`}>
                    {notif.type?.includes('medication') ? <Pill className="w-4 h-4" /> :
                     notif.type?.includes('appointment') ? <Calendar className="w-4 h-4" /> :
                     <Bell className="w-4 h-4" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{notif.title}</p>
                    <p className="text-xs text-white/50 truncate">{notif.message}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <Badge color="cyan" size="sm">
                    {formatScheduledTime(notif.scheduled_at)}
                  </Badge>
                  <div className="text-xs text-white/50">
                    {new Date(notif.scheduled_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </GlassCard>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Notifications Feed */}
        <div className="lg:col-span-2 space-y-3">
          <h3 className="text-sm font-semibold text-white/60">Notifications</h3>
          <AnimatePresence>
            {filteredNotifications.length > 0 ? (
              filteredNotifications.map((notif, i) => (
                <motion.div
                  key={notif.id || i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <GlassCard className="p-4" animate={false}>
                    <div className="flex items-start gap-3">
                      <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
                        notif.type === 'medication' ? 'bg-violet-500/15 text-violet-400' :
                        notif.type === 'appointment' ? 'bg-amber-500/15 text-amber-400' :
                        notif.type === 'alert' ? 'bg-rose-500/15 text-rose-400' :
                        'bg-cyan-500/15 text-cyan-400'
                      }`}>
                        {notif.type === 'medication' ? <Pill className="w-4 h-4" /> :
                         notif.type === 'appointment' ? <Calendar className="w-4 h-4" /> :
                         notif.type === 'alert' ? <AlertTriangle className="w-4 h-4" /> :
                         <Bell className="w-4 h-4" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-white">{notif.title}</p>
                          <Badge color={typeColors[notif.type] || 'gray'}>{notif.type}</Badge>
                        </div>
                        <p className="text-xs text-white/50 mt-1">{notif.message || notif.body}</p>
                        <p className="text-[10px] text-white/30 mt-1">
                          {notif.created_at ? formatRelativeTime(notif.created_at) : ''}
                        </p>
                      </div>
                      {!notif.read && (
                        <span className="w-2 h-2 rounded-full bg-cyan-400 flex-shrink-0 mt-2" />
                      )}
                    </div>
                  </GlassCard>
                </motion.div>
              ))
            ) : !loading ? (
              <EmptyState
                icon={Bell}
                title="No notifications"
                description="You're all caught up! Notifications will appear here."
              />
            ) : null}
          </AnimatePresence>
        </div>

        {/* Medication Reminders */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white/60">Medication Reminders</h3>
            <Button onClick={() => setShowAddMedModal(true)} variant="ghost" size="sm">
              <Plus className="w-4 h-4" />
            </Button>
          </div>

          {reminders.length > 0 ? (
            reminders.map((rem, i) => (
              <GlassCard key={i} className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-violet-500/15 flex items-center justify-center">
                    <Pill className="w-5 h-5 text-violet-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-white">{rem.name}</p>
                    <p className="text-xs text-white/40">{rem.dosage}</p>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-1 text-xs text-white/50">
                      <Clock className="w-3 h-3" />
                      {rem.time}
                    </div>
                    <p className="text-[10px] text-white/30">{rem.frequency}</p>
                  </div>
                </div>
              </GlassCard>
            ))
          ) : (
            <GlassCard className="p-4 text-center">
              <Pill className="w-6 h-6 text-white/20 mx-auto mb-2" />
              <p className="text-xs text-white/40">No medication reminders</p>
            </GlassCard>
          )}
        </div>
      </div>

      {/* Add Medication Modal */}
      <Modal isOpen={showAddMedModal} onClose={() => setShowAddMedModal(false)} title="Add Medication Reminder">
        <div className="space-y-4">
          <Input
            label="Medication Name"
            placeholder="e.g., Aspirin"
            value={medForm.name}
            onChange={(e) => setMedForm(p => ({ ...p, name: e.target.value }))}
          />
          <Input
            label="Dosage"
            placeholder="e.g., 100mg"
            value={medForm.dosage}
            onChange={(e) => setMedForm(p => ({ ...p, dosage: e.target.value }))}
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Time"
              type="time"
              value={medForm.time}
              onChange={(e) => setMedForm(p => ({ ...p, time: e.target.value }))}
            />
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-white/70">Frequency</label>
              <select
                value={medForm.frequency}
                onChange={(e) => setMedForm(p => ({ ...p, frequency: e.target.value }))}
                className="glass-input w-full px-4 py-3 text-sm"
              >
                <option value="daily" className="bg-[#12121a]">Daily</option>
                <option value="twice_daily" className="bg-[#12121a]">Twice Daily</option>
                <option value="weekly" className="bg-[#12121a]">Weekly</option>
                <option value="as_needed" className="bg-[#12121a]">As Needed</option>
              </select>
            </div>
          </div>
          <div className="flex gap-3">
            <Button variant="ghost" onClick={() => setShowAddMedModal(false)} className="flex-1">Cancel</Button>
            <Button onClick={addMedication} className="flex-1">Add Reminder</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
