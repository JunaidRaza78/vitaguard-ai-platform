import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, AlertTriangle, ChevronDown, ExternalLink, Sparkles } from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import api from '@/lib/axios'

const specialties = [
  { value: '', label: 'General Medical' },
  { value: 'cardiology', label: 'Cardiology' },
  { value: 'dermatology', label: 'Dermatology' },
  { value: 'neurology', label: 'Neurology' },
  { value: 'pediatrics', label: 'Pediatrics' },
  { value: 'orthopedics', label: 'Orthopedics' },
  { value: 'nutrition', label: 'Nutrition' },
  { value: 'mental_health', label: 'Mental Health' },
]

const emergencyKeywords = ['chest pain', 'difficulty breathing', 'stroke', 'seizure', 'unconscious', 'severe bleeding', 'heart attack']

export default function ChatPage() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I\'m your AI health assistant. How can I help you today? Remember, I provide information only - always consult a healthcare professional for medical advice.' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [specialty, setSpecialty] = useState('')
  const [showEmergency, setShowEmergency] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const checkEmergency = (text) => {
    const lower = text.toLowerCase()
    return emergencyKeywords.some(kw => lower.includes(kw))
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')

    if (checkEmergency(userMessage)) {
      setShowEmergency(true)
    }

    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const { data } = await api.post('/api/v1/chat', {
        message: userMessage,
        specialty: specialty || undefined,
      })

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response || data.message || 'I apologize, I could not process your request.',
        sources: data.sources || [],
      }])
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)]">
      {/* Emergency Banner */}
      <AnimatePresence>
        {showEmergency && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-4"
          >
            <div className="glass rounded-xl p-4 border border-rose-500/30 bg-rose-500/5">
              <div className="flex items-center gap-3">
                <div className="pulse-neon">
                  <AlertTriangle className="w-6 h-6 text-rose-400" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-rose-400">Emergency Detected</p>
                  <p className="text-xs text-white/50">If this is a medical emergency, call 911 immediately.</p>
                </div>
                <button onClick={() => setShowEmergency(false)} className="text-white/40 hover:text-white text-sm">
                  Dismiss
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Specialty Filter */}
      <div className="flex items-center gap-3 mb-4">
        <Sparkles className="w-4 h-4 text-cyan-400" />
        <div className="flex gap-2 flex-wrap">
          {specialties.map(s => (
            <button
              key={s.value}
              onClick={() => setSpecialty(s.value)}
              className={`px-3 py-1 text-xs rounded-full transition-all ${
                specialty === s.value
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                  : 'glass text-white/50 hover:text-white/80'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <GlassCard className="flex-1 overflow-y-auto p-4 space-y-4 mb-4" animate={false}>
        {messages.map((msg, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
              msg.role === 'user'
                ? 'bg-gradient-to-br from-violet-500 to-fuchsia-500'
                : 'bg-gradient-to-br from-cyan-500 to-emerald-500'
            }`}>
              {msg.role === 'user' ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-white" />}
            </div>
            <div className={`max-w-[75%] ${msg.role === 'user' ? 'text-right' : ''}`}>
              <div className={`rounded-2xl p-4 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 border border-violet-500/20 text-white'
                  : 'glass text-white/90'
              }`}>
                <p className="whitespace-pre-wrap">{msg.content}</p>
              </div>
              {/* Sources */}
              {msg.sources?.length > 0 && (
                <div className="mt-2 space-y-1">
                  <p className="text-[10px] text-white/30 uppercase tracking-wider">Sources</p>
                  {msg.sources.map((src, j) => (
                    <div key={j} className="flex items-center gap-1 text-xs text-cyan-400/70">
                      <ExternalLink className="w-3 h-3" />
                      <span className="truncate">{src.title || src}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="glass rounded-2xl px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </GlassCard>

      {/* Input */}
      <div className="glass-strong rounded-2xl p-3 flex items-end gap-3">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask me about your health..."
          rows={1}
          className="flex-1 bg-transparent border-none outline-none text-sm text-white resize-none placeholder:text-white/30 max-h-32"
          style={{ minHeight: '24px' }}
        />
        <Button
          onClick={handleSend}
          disabled={!input.trim() || loading}
          size="sm"
          className="flex-shrink-0"
        >
          <Send className="w-4 h-4" />
        </Button>
      </div>

      {/* Disclaimer */}
      <p className="text-[10px] text-white/20 text-center mt-2">
        AI responses are for informational purposes only. Always consult a healthcare professional.
      </p>
    </div>
  )
}
