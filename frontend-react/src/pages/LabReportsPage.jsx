import { useState, useMemo, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FlaskConical, Plus, AlertTriangle, FileText, Activity, Clipboard, History, TrendingUp, Calendar } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import GlassCard from '@/components/ui/GlassCard'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Textarea from '@/components/ui/Textarea'
import Badge from '@/components/ui/Badge'
import api from '@/lib/axios'
import toast from 'react-hot-toast'
import { formatDate } from '@/lib/utils'

function renderMarkdown(text) {
  if (!text) return ''
  return text
    // Bold: **text**
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
    // Italic: *text*
    .replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>')
    // Headers: lines starting with ##
    .replace(/^### (.+)$/gm, '<h4 class="text-base font-semibold text-white mt-4 mb-1">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 class="text-lg font-semibold text-white mt-4 mb-2">$1</h3>')
    // Bullet points: lines starting with • or - or *
    .replace(/^[•\-\*] (.+)$/gm, '<li class="ml-4 pl-1">$1</li>')
    // Wrap consecutive <li> in <ul>
    .replace(/((?:<li[^>]*>.*<\/li>\n?)+)/g, '<ul class="list-disc space-y-1 my-2">$1</ul>')
    // Arrow → styling
    .replace(/→/g, '<span class="text-cyan-400">→</span>')
    // Line breaks
    .replace(/\n/g, '<br />')
    // Clean up double <br /> inside lists
    .replace(/<\/li><br \/>/g, '</li>')
    .replace(/<\/ul><br \/>/g, '</ul>')
    .replace(/<br \/><ul/g, '<ul')
}

const commonTests = [
  { name: 'Hemoglobin', unit: 'g/dL', min: 12.0, max: 17.5 },
  { name: 'White Blood Cells', unit: 'K/uL', min: 4.5, max: 11.0 },
  { name: 'Platelets', unit: 'K/uL', min: 150, max: 400 },
  { name: 'Blood Glucose (Fasting)', unit: 'mg/dL', min: 70, max: 100 },
  { name: 'Creatinine', unit: 'mg/dL', min: 0.6, max: 1.2 },
  { name: 'Cholesterol (Total)', unit: 'mg/dL', min: 0, max: 200 },
  { name: 'HDL Cholesterol', unit: 'mg/dL', min: 40, max: 60 },
  { name: 'LDL Cholesterol', unit: 'mg/dL', min: 0, max: 100 },
  { name: 'Triglycerides', unit: 'mg/dL', min: 0, max: 150 },
  { name: 'TSH', unit: 'mIU/L', min: 0.4, max: 4.0 },
]

function ReferenceBar({ value, min, max, unit }) {
  const numVal = parseFloat(value)
  if (isNaN(numVal)) return null

  const range = max - min
  const extendedMin = min - range * 0.3
  const extendedMax = max + range * 0.3
  const totalRange = extendedMax - extendedMin
  const pos = Math.max(0, Math.min(100, ((numVal - extendedMin) / totalRange) * 100))
  const normalStart = ((min - extendedMin) / totalRange) * 100
  const normalEnd = ((max - extendedMin) / totalRange) * 100

  const isLow = numVal < min
  const isHigh = numVal > max
  const isNormal = !isLow && !isHigh

  return (
    <div className="mt-2">
      <div className="relative h-3 rounded-full bg-white/5 overflow-hidden">
        {/* Normal range */}
        <div
          className="absolute top-0 h-full bg-emerald-500/20 rounded-full"
          style={{ left: `${normalStart}%`, width: `${normalEnd - normalStart}%` }}
        />
        {/* Marker */}
        <motion.div
          initial={{ left: '50%' }}
          animate={{ left: `${pos}%` }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className={`absolute top-0 w-3 h-3 rounded-full -translate-x-1/2 ${
            isNormal ? 'bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]' :
            isHigh ? 'bg-rose-400 shadow-[0_0_8px_rgba(244,63,94,0.5)]' :
            'bg-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.5)]'
          }`}
        />
      </div>
      <div className="flex justify-between mt-1">
        <span className="text-[10px] text-white/30">{min} {unit}</span>
        <span className={`text-[10px] font-medium ${
          isNormal ? 'text-emerald-400' : isHigh ? 'text-rose-400' : 'text-amber-400'
        }`}>
          {numVal} {unit} ({isNormal ? 'Normal' : isHigh ? 'High' : 'Low'})
        </span>
        <span className="text-[10px] text-white/30">{max} {unit}</span>
      </div>
    </div>
  )
}

export default function LabReportsPage() {
  const [tab, setTab] = useState('analyze') // analyze | history
  const [mode, setMode] = useState('manual') // manual | parse
  const [results, setResults] = useState([])
  const [parseText, setParseText] = useState('')
  const [manualEntries, setManualEntries] = useState([{ test: '', value: '' }])
  const [interpreting, setInterpreting] = useState(false)
  const [interpretation, setInterpretation] = useState(null)
  const [history, setHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [trendTest, setTrendTest] = useState(null)
  const [trendData, setTrendData] = useState(null)

  const addEntry = () => {
    setManualEntries(prev => [...prev, { test: '', value: '' }])
  }

  const updateEntry = (index, field, value) => {
    setManualEntries(prev => prev.map((e, i) => i === index ? { ...e, [field]: value } : e))
  }

  const removeEntry = (index) => {
    setManualEntries(prev => prev.filter((_, i) => i !== index))
  }

  const processManual = () => {
    const processed = manualEntries
      .filter(e => e.test && e.value)
      .map(entry => {
        const ref = commonTests.find(t => t.name.toLowerCase() === entry.test.toLowerCase())
        const numVal = parseFloat(entry.value)
        let status = 'normal'
        if (ref && !isNaN(numVal)) {
          if (numVal < ref.min) status = 'low'
          else if (numVal > ref.max) status = 'high'
        }
        return { ...entry, ref, status, numVal }
      })
    setResults(processed)
    checkEmergency(processed)
  }

  const parseLab = async () => {
    if (!parseText.trim()) return
    setInterpreting(true)
    try {
      const { data } = await api.post('/api/v1/labs/parse-text', { text: parseText })

      // Backend returns parsed_results as { test_key: value } dict
      const parsedResults = data.parsed_results || {}
      if (Object.keys(parsedResults).length > 0) {
        const processed = Object.entries(parsedResults).map(([key, val]) => {
          const ref = commonTests.find(t =>
            t.name.toLowerCase().includes(key.toLowerCase()) ||
            key.toLowerCase().includes(t.name.toLowerCase().split(' ')[0])
          )
          const numVal = parseFloat(val)
          let status = 'normal'
          if (ref && !isNaN(numVal)) {
            if (numVal < ref.min) status = 'low'
            else if (numVal > ref.max) status = 'high'
          }
          return { test: key, value: val, numVal, ref, status }
        })
        setResults(processed)
        checkEmergency(processed)
      } else if (data.message) {
        toast(data.message, { icon: 'ℹ️' })
      }

      // Backend returns interpretation object with classified results + AI summary
      if (data.interpretation) {
        const interp = data.interpretation
        const summary = interp.ai_summary || interp.summary || (typeof interp === 'string' ? interp : JSON.stringify(interp, null, 2))
        setInterpretation(summary)
      }
    } catch {
      toast.error('Failed to parse lab text')
    } finally {
      setInterpreting(false)
    }
  }

  const checkEmergency = (processed) => {
    const emergencies = processed.filter(r => {
      if (!r.ref || isNaN(r.numVal)) return false
      const range = r.ref.max - r.ref.min
      return r.numVal < r.ref.min - range * 0.5 || r.numVal > r.ref.max + range * 0.5
    })
    if (emergencies.length > 0) {
      toast.error(`Critical values detected for: ${emergencies.map(e => e.test).join(', ')}`, { duration: 5000 })
    }
  }

  const saveResults = async () => {
    if (results.length === 0) return
    try {
      const payload = {
        results: results.reduce((acc, r) => ({ ...acc, [r.test]: r.numVal }), {}),
        report_date: new Date().toISOString().split('T')[0],
        ai_summary: interpretation || undefined,
      }
      await api.post('/api/v1/labs/save-results', payload)
      toast.success('Lab results saved to history')
      loadHistory() // Refresh history
    } catch {
      toast.error('Failed to save results')
    }
  }

  const loadHistory = async () => {
    setLoadingHistory(true)
    try {
      const { data } = await api.get('/api/v1/labs/history')
      setHistory(data.history || [])
    } catch {
      toast.error('Failed to load lab history')
    } finally {
      setLoadingHistory(false)
    }
  }

  const loadTrend = async (testName) => {
    try {
      const testKey = testName.toLowerCase().replace(/[^a-z0-9]/g, '_')
      const { data } = await api.get(`/api/v1/labs/trend/${testKey}`)
      setTrendData(data)
      setTrendTest(testName)
    } catch {
      toast.error('Failed to load trend data')
    }
  }

  useEffect(() => {
    if (tab === 'history') {
      loadHistory()
    }
  }, [tab])

  return (
    <div className="space-y-6">
      {/* Main Tabs */}
      <div className="flex gap-3">
        <button
          onClick={() => setTab('analyze')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm transition-all ${
            tab === 'analyze' ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30' : 'glass text-white/50'
          }`}
        >
          <Activity className="w-4 h-4" /> Analyze
        </button>
        <button
          onClick={() => setTab('history')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm transition-all ${
            tab === 'history' ? 'bg-violet-500/15 text-violet-400 border border-violet-500/30' : 'glass text-white/50'
          }`}
        >
          <History className="w-4 h-4" /> History
        </button>
      </div>

      {/* Analyze Tab */}
      {tab === 'analyze' && (
        <>
          {/* Mode Tabs */}
          <div className="flex gap-3">
            <button
              onClick={() => setMode('manual')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm transition-all ${
                mode === 'manual' ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'glass text-white/50'
              }`}
            >
              <Plus className="w-4 h-4" /> Manual Entry
            </button>
            <button
              onClick={() => setMode('parse')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm transition-all ${
                mode === 'parse' ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30' : 'glass text-white/50'
              }`}
            >
              <Clipboard className="w-4 h-4" /> Paste Lab Text
            </button>
          </div>
        </>
      )}

      {/* Manual Entry */}
      {tab === 'analyze' && mode === 'manual' && (
        <GlassCard>
          <h3 className="text-sm font-semibold text-white/80 mb-4">Enter Lab Results</h3>
          <div className="space-y-3">
            {manualEntries.map((entry, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex gap-3 items-end"
              >
                <div className="flex-1">
                  <label className="text-xs text-white/50 mb-1 block">Test Name</label>
                  <select
                    value={entry.test}
                    onChange={(e) => updateEntry(i, 'test', e.target.value)}
                    className="glass-input w-full px-3 py-2.5 text-sm"
                  >
                    <option value="" className="bg-[#12121a]">Select test...</option>
                    {commonTests.map(t => (
                      <option key={t.name} value={t.name} className="bg-[#12121a]">{t.name}</option>
                    ))}
                  </select>
                </div>
                <div className="w-32">
                  <label className="text-xs text-white/50 mb-1 block">Value</label>
                  <input
                    type="number"
                    step="0.01"
                    value={entry.value}
                    onChange={(e) => updateEntry(i, 'value', e.target.value)}
                    placeholder="0.0"
                    className="glass-input w-full px-3 py-2.5 text-sm"
                  />
                </div>
                {manualEntries.length > 1 && (
                  <button
                    onClick={() => removeEntry(i)}
                    className="p-2 text-white/30 hover:text-rose-400 transition-colors"
                  >
                    &times;
                  </button>
                )}
              </motion.div>
            ))}
          </div>
          <div className="flex gap-3 mt-4">
            <Button variant="ghost" size="sm" onClick={addEntry}>
              <Plus className="w-4 h-4" /> Add Test
            </Button>
            <Button size="sm" onClick={processManual}>
              <Activity className="w-4 h-4" /> Analyze
            </Button>
          </div>
        </GlassCard>
      )}

      {/* Parse Text */}
      {tab === 'analyze' && mode === 'parse' && (
        <GlassCard>
          <h3 className="text-sm font-semibold text-white/80 mb-4">Paste Lab Report Text</h3>
          <Textarea
            placeholder="Paste your lab report text here..."
            value={parseText}
            onChange={(e) => setParseText(e.target.value)}
            className="min-h-[150px]"
          />
          <Button className="mt-3" onClick={parseLab} loading={interpreting}>
            <FlaskConical className="w-4 h-4" /> Interpret Results
          </Button>
        </GlassCard>
      )}

      {/* Results */}
      <AnimatePresence>
        {tab === 'analyze' && results.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <GlassCard>
              <h3 className="text-sm font-semibold text-white/80 mb-4">Lab Results</h3>
              <div className="space-y-4">
                {results.map((r, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="glass rounded-xl p-4"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <FlaskConical className="w-4 h-4 text-cyan-400" />
                        <span className="text-sm font-medium text-white">{r.test}</span>
                      </div>
                      <Badge color={
                        r.status === 'normal' ? 'emerald' :
                        r.status === 'high' ? 'rose' : 'amber'
                      }>
                        {r.status === 'normal' ? 'Normal' : r.status === 'high' ? 'High' : 'Low'}
                      </Badge>
                    </div>
                    {r.ref && (
                      <ReferenceBar
                        value={r.value}
                        min={r.ref.min}
                        max={r.ref.max}
                        unit={r.ref.unit}
                      />
                    )}
                  </motion.div>
                ))}
              </div>
              {results.length > 0 && (
                <div className="mt-4 pt-4 border-t border-white/5">
                  <Button onClick={saveResults} size="sm">
                    Save to History
                  </Button>
                </div>
              )}
            </GlassCard>
          </motion.div>
        )}
      </AnimatePresence>

      {/* AI Interpretation */}
      {tab === 'analyze' && interpretation && (
        <GlassCard glow="violet">
          <div className="flex items-center gap-2 mb-3">
            <FileText className="w-4 h-4 text-violet-400" />
            <h3 className="text-sm font-semibold text-white/80">AI Interpretation</h3>
          </div>
          <div
            className="text-sm text-white/70 leading-relaxed [&_ul]:list-disc [&_ul]:ml-4 [&_li]:mb-1 [&_h3]:text-lg [&_h4]:text-base"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(interpretation) }}
          />
          <p className="text-[10px] text-white/30 mt-3">
            This is AI-generated analysis for informational purposes only. Consult your doctor.
          </p>
        </GlassCard>
      )}

      {/* History Tab */}
      {tab === 'history' && (
        <div className="space-y-4">
          {loadingHistory ? (
            <GlassCard>
              <div className="text-center py-8 text-white/50">Loading history...</div>
            </GlassCard>
          ) : history.length === 0 ? (
            <GlassCard>
              <div className="text-center py-8 text-white/50">No lab history found</div>
            </GlassCard>
          ) : (
            history.map((report, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
              >
                <GlassCard>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-cyan-400" />
                      <span className="text-sm font-medium text-white">{formatDate(report.date)}</span>
                      <Badge color="violet">{report.results.length} tests</Badge>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {report.results.map((r, i) => (
                      <div
                        key={i}
                        className="glass rounded-lg p-3 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors"
                        onClick={() => loadTrend(r.test_name)}
                      >
                        <div className="flex items-center gap-2">
                          <FlaskConical className="w-3 h-3 text-cyan-400" />
                          <span className="text-xs font-medium text-white">{r.test_name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-white/70">{r.value} {r.unit}</span>
                          <Badge color={r.status === 'normal' ? 'emerald' : r.status === 'high' ? 'rose' : 'amber'} size="sm">
                            {r.status}
                          </Badge>
                          <TrendingUp className="w-3 h-3 text-white/30" />
                        </div>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              </motion.div>
            ))
          )}
        </div>
      )}

      {/* Trend Chart Modal */}
      <AnimatePresence>
        {trendData && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setTrendData(null)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="glass-strong rounded-2xl p-6 w-full max-w-3xl"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-cyan-400" />
                  <h3 className="text-lg font-semibold text-white">{trendTest} Trend</h3>
                  <Badge color="violet">{trendData.total_points} data points</Badge>
                </div>
                <button
                  onClick={() => setTrendData(null)}
                  className="text-white/50 hover:text-white transition-colors"
                >
                  ✕
                </button>
              </div>
              {trendData.trend_data.length > 0 ? (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trendData.trend_data}>
                      <XAxis
                        dataKey="date"
                        stroke="rgba(255,255,255,0.2)"
                        style={{ fontSize: '11px' }}
                      />
                      <YAxis
                        stroke="rgba(255,255,255,0.2)"
                        style={{ fontSize: '11px' }}
                        domain={['auto', 'auto']}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'rgba(30, 30, 40, 0.95)',
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: '8px',
                          color: 'white',
                        }}
                      />
                      {trendData.reference_low && (
                        <ReferenceLine
                          y={trendData.reference_low}
                          stroke="#10b981"
                          strokeDasharray="3 3"
                          label={{ value: 'Low', fill: '#10b981', fontSize: 10 }}
                        />
                      )}
                      {trendData.reference_high && (
                        <ReferenceLine
                          y={trendData.reference_high}
                          stroke="#10b981"
                          strokeDasharray="3 3"
                          label={{ value: 'High', fill: '#10b981', fontSize: 10 }}
                        />
                      )}
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#06b6d4"
                        strokeWidth={2}
                        dot={{ fill: '#06b6d4', r: 4 }}
                        activeDot={{ r: 6 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="text-center py-12 text-white/50">No trend data available</div>
              )}
              <div className="mt-4 text-xs text-white/50 text-center">
                Reference range: {trendData.reference_low} - {trendData.reference_high} {trendData.unit}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
