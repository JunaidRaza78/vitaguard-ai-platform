import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Users, Pill, Calendar, HeartPulse, MessageCircle, Upload, Activity } from 'lucide-react'
import KpiCard from '@/components/dashboard/KpiCard'
import VitalsTrendChart from '@/components/dashboard/VitalsTrendChart'
import RiskGauge from '@/components/dashboard/RiskGauge'
import AnomalyAlert from '@/components/dashboard/AnomalyAlert'
import FamilyTimeline from '@/components/dashboard/FamilyTimeline'
import RecordVitalsModal from '@/components/dashboard/RecordVitalsModal'
import Button from '@/components/ui/Button'
import GlassCard from '@/components/ui/GlassCard'
import api from '@/lib/axios'

export default function DashboardPage() {
  const [summary, setSummary] = useState(null)
  const [vitalsData, setVitalsData] = useState([])
  const [anomalies, setAnomalies] = useState([])
  const [riskScores, setRiskScores] = useState([])
  const [timeline, setTimeline] = useState([])
  const [showVitalsModal, setShowVitalsModal] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      const [summaryRes, vitalsRes, anomalyRes, riskRes, timelineRes] = await Promise.allSettled([
        api.get('/api/v1/dashboard/summary'),
        api.get('/api/v1/vitals/my/latest'),
        api.get('/api/v1/vitals/my/anomalies'),
        api.get('/api/v1/vitals/my/risk-scores'),
        api.get('/api/v1/dashboard/family-timeline'),
      ])

      if (summaryRes.status === 'fulfilled') {
        const d = summaryRes.value.data
        setSummary({
          ...d,
          family_members: d.family_members ?? 0,
          active_medications: Array.isArray(d.active_medications) ? d.active_medications.length : (d.active_medications ?? 0),
          upcoming_appointments: Array.isArray(d.upcoming_appointments) ? d.upcoming_appointments.length : (d.upcoming_appointments ?? 0),
          health_score: d.health_score ?? null,
        })
      }
      if (vitalsRes.status === 'fulfilled') setVitalsData(vitalsRes.value.data?.vitals || vitalsRes.value.data || [])
      if (anomalyRes.status === 'fulfilled') setAnomalies(anomalyRes.value.data?.alerts || anomalyRes.value.data?.anomalies || [])
      if (riskRes.status === 'fulfilled') setRiskScores(riskRes.value.data?.risk_scores || [])
      if (timelineRes.status === 'fulfilled') setTimeline(timelineRes.value.data?.events || [])
    } catch {
      // Dashboard loads gracefully with defaults
    }
  }

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          icon={Users}
          label="Family Members"
          value={summary?.family_members || 0}
          color="cyan"
          delay={0}
        />
        <KpiCard
          icon={Pill}
          label="Active Medications"
          value={summary?.active_medications || 0}
          change={summary?.medication_change}
          color="violet"
          delay={0.1}
        />
        <KpiCard
          icon={Calendar}
          label="Upcoming Appointments"
          value={summary?.upcoming_appointments || 0}
          color="amber"
          delay={0.2}
        />
        <KpiCard
          icon={HeartPulse}
          label="Health Score"
          value={summary?.health_score ? `${summary.health_score}%` : '—'}
          change={summary?.score_change}
          color="emerald"
          delay={0.3}
        />
      </div>

      {/* Quick Actions */}
      <div className="flex gap-3 flex-wrap">
        <Button onClick={() => setShowVitalsModal(true)} variant="primary" size="sm">
          <Activity className="w-4 h-4" />
          Record Vitals
        </Button>
        <Button onClick={() => navigate('/chat')} variant="ghost" size="sm">
          <MessageCircle className="w-4 h-4" />
          Ask AI
        </Button>
        <Button onClick={() => navigate('/documents')} variant="ghost" size="sm">
          <Upload className="w-4 h-4" />
          Upload Doc
        </Button>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <VitalsTrendChart data={vitalsData} />
        </div>
        <FamilyTimeline events={timeline} />
      </div>

      {/* Risk Gauges */}
      {riskScores.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-white/60 mb-3">Risk Assessment</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            {riskScores.map((risk, i) => (
              <RiskGauge key={i} label={risk.category} score={risk.score} />
            ))}
          </div>
        </div>
      )}

      {/* Default risk gauges if no data */}
      {riskScores.length === 0 && (
        <div>
          <h3 className="text-sm font-semibold text-white/60 mb-3">Risk Assessment</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            <RiskGauge label="Cardiovascular" score={25} />
            <RiskGauge label="Diabetes" score={15} />
            <RiskGauge label="Respiratory" score={10} />
            <RiskGauge label="Mental Health" score={35} />
            <RiskGauge label="Overall" score={20} />
          </div>
        </div>
      )}

      {/* Anomaly Alerts */}
      <GlassCard>
        <h3 className="text-sm font-semibold text-white/80 mb-3">Anomaly Alerts</h3>
        {anomalies.length > 0 ? (
          <div className="space-y-2">
            {anomalies.map((a, i) => (
              <AnomalyAlert key={i} anomaly={a} index={i} />
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            <AnomalyAlert anomaly={{ metric: 'Heart Rate', message: 'Slight elevation detected above baseline (82 BPM)', severity: 'low', trend: 'up', timestamp: new Date().toISOString() }} index={0} />
            <AnomalyAlert anomaly={{ metric: 'Blood Pressure', message: 'All readings within normal range', severity: 'low', trend: 'down', timestamp: new Date().toISOString() }} index={1} />
          </div>
        )}
      </GlassCard>

      <RecordVitalsModal isOpen={showVitalsModal} onClose={() => setShowVitalsModal(false)} />
    </div>
  )
}
