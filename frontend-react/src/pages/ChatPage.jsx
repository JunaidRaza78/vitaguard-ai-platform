import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, AlertTriangle, ExternalLink, Sparkles, Plus, MessageSquare, Trash2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import GlassCard from '@/components/ui/GlassCard'
import Button from '@/components/ui/Button'
import useAuthStore from '@/stores/authStore'
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

const WELCOME_MSG = { role: 'assistant', content: "Hello! I'm your AI health assistant. How can I help you today? Remember, I provide information only - always consult a healthcare professional for medical advice." }

// Per-user storage keys
function storageKey(userId) { return `health_chat_sessions_${userId}` }
function activeKey(userId) { return `health_chat_active_${userId}` }

function loadSessions(userId) {
  try { return JSON.parse(localStorage.getItem(storageKey(userId)) || '[]') } catch { return [] }
}

function saveSessions(userId, sessions) {
  try { localStorage.setItem(storageKey(userId), JSON.stringify(sessions)) } catch {}
}

function newSession() {
  return { id: Date.now().toString(), title: 'New Chat', messages: [WELCOME_MSG], createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() }
}

// Direct localStorage save (works even if component unmounted)
function persistMessage(userId, sessionId, newMessages) {
  const all = loadSessions(userId)
  const userMsgs = newMessages.filter(m => m.role === 'user')
  const title = userMsgs.length > 0
    ? userMsgs[0].content.slice(0, 40) + (userMsgs[0].content.length > 40 ? '…' : '')
    : 'New Chat'
  const updated = all.map(s =>
    s.id === sessionId
      ? { ...s, messages: newMessages, title, updatedAt: new Date().toISOString() }
      : s
  )
  saveSessions(userId, updated)
  return updated
}

export default function ChatPage() {
  const user = useAuthStore((s) => s.user)
  const userId = user?.user_id || user?.id || 'guest'

  const [sessions, setSessions] = useState(() => {
    const saved = loadSessions(userId)
    if (saved.length === 0) {
      const s = newSession()
      saveSessions(userId, [s])
      return [s]
    }
    return saved
  })

  const [activeId, setActiveId] = useState(() => {
    const saved = loadSessions(userId)
    const storedActive = localStorage.getItem(activeKey(userId))
    if (storedActive && saved.find(s => s.id === storedActive)) return storedActive
    return saved[0]?.id || null
  })

  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [specialty, setSpecialty] = useState('')
  const [showEmergency, setShowEmergency] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Reload sessions from localStorage whenever userId changes (handles user switch + mount)
  useEffect(() => {
    const saved = loadSessions(userId)
    if (saved.length > 0) {
      setSessions(saved)
      const storedActive = localStorage.getItem(activeKey(userId))
      setActiveId(storedActive && saved.find(s => s.id === storedActive) ? storedActive : saved[0].id)
    } else {
      // New user with no history — start fresh
      const s = newSession()
      saveSessions(userId, [s])
      setSessions([s])
      setActiveId(s.id)
    }
  }, [userId])

  const activeSession = sessions.find(s => s.id === activeId)
  const messages = activeSession?.messages || [WELCOME_MSG]

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (activeId) localStorage.setItem(activeKey(userId), activeId)
  }, [activeId, userId])

  const syncFromStorage = useCallback(() => {
    const saved = loadSessions(userId)
    setSessions(saved)
  }, [userId])

  const startNewChat = () => {
    const s = newSession()
    const current = loadSessions(userId)
    const updated = [s, ...current]
    saveSessions(userId, updated)
    setSessions(updated)
    setActiveId(s.id)
    setShowEmergency(false)
  }

  const deleteSession = (id, e) => {
    e.stopPropagation()
    const current = loadSessions(userId)
    const updated = current.filter(s => s.id !== id)
    if (updated.length === 0) {
      const fresh = newSession()
      saveSessions(userId, [fresh])
      setSessions([fresh])
      setActiveId(fresh.id)
    } else {
      saveSessions(userId, updated)
      setSessions(updated)
      if (activeId === id) setActiveId(updated[0].id)
    }
  }

  const checkEmergency = (text) => emergencyKeywords.some(kw => text.toLowerCase().includes(kw))

  const handleSend = async () => {
    if (!input.trim() || loading || !activeId) return
    const userMessage = input.trim()
    const currentUserId = userId
    const currentSessionId = activeId
    setInput('')

    if (checkEmergency(userMessage)) setShowEmergency(true)

    // Build messages with user input and save immediately
    const withUser = [...messages, { role: 'user', content: userMessage }]
    const afterUser = persistMessage(currentUserId, currentSessionId, withUser)
    setSessions(afterUser)
    setLoading(true)

    try {
      const { data } = await api.post('/api/v1/chat', {
        message: userMessage,
        specialty: specialty || undefined,
      })

      const reply = {
        role: 'assistant',
        content: data.response || data.message || 'I apologize, I could not process your request.',
        sources: data.sources || [],
      }
      const withReply = [...withUser, reply]

      // Save directly to localStorage — works even if user switched tabs during request
      const afterReply = persistMessage(currentUserId, currentSessionId, withReply)
      setSessions(afterReply)
    } catch {
      const withError = [...withUser, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]
      const afterError = persistMessage(currentUserId, currentSessionId, withError)
      setSessions(afterError)
    } finally {
      setLoading(false)
    }
  }

  // When user returns to this tab, re-sync from localStorage to pick up any completed responses
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) syncFromStorage()
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [syncFromStorage])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const formatTime = (iso) => {
    const d = new Date(iso)
    const now = new Date()
    const diff = now - d
    if (diff < 86400000) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    if (diff < 604800000) return d.toLocaleDateString([], { weekday: 'short' })
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
  }

  return (
    <div className="flex h-[calc(100vh-7rem)] gap-4">
      {/* ── Sidebar: Chat History ── */}
      <div className="w-56 flex-shrink-0 flex flex-col gap-2">
        <Button onClick={startNewChat} size="sm" className="w-full justify-start gap-2">
          <Plus className="w-4 h-4" /> New Chat
        </Button>

        <div className="flex-1 overflow-y-auto space-y-1 pr-0.5">
          {sessions.map(s => (
            <motion.button
              key={s.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              onClick={() => { setActiveId(s.id); setShowEmergency(false) }}
              className={`w-full text-left px-3 py-2.5 rounded-xl text-xs transition-all group flex items-start gap-2 ${
                s.id === activeId
                  ? 'bg-cyan-500/15 border border-cyan-500/25 text-white'
                  : 'glass text-white/50 hover:text-white/80 hover:bg-white/5'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-cyan-400/60" />
              <div className="flex-1 min-w-0">
                <p className="truncate font-medium leading-tight">{s.title}</p>
                <p className="text-[10px] text-white/30 mt-0.5">{formatTime(s.updatedAt)}</p>
              </div>
              <button
                onClick={(e) => deleteSession(s.id, e)}
                className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:text-rose-400 transition-all flex-shrink-0"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </motion.button>
          ))}
        </div>
      </div>

      {/* ── Main Chat Area ── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Emergency Banner */}
        <AnimatePresence>
          {showEmergency && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="mb-3">
              <div className="glass rounded-xl p-3 border border-rose-500/30 bg-rose-500/5">
                <div className="flex items-center gap-3">
                  <div className="pulse-neon"><AlertTriangle className="w-5 h-5 text-rose-400" /></div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-rose-400">Emergency Detected</p>
                    <p className="text-xs text-white/50">If this is a medical emergency, call 911 immediately.</p>
                  </div>
                  <button onClick={() => setShowEmergency(false)} className="text-white/40 hover:text-white text-xs">Dismiss</button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Specialty Filter */}
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <Sparkles className="w-4 h-4 text-cyan-400 flex-shrink-0" />
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

        {/* Messages */}
        <GlassCard className="flex-1 overflow-y-auto p-4 space-y-4 mb-3" animate={false}>
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
                  {msg.role === 'assistant' ? (
                    <ReactMarkdown
                      components={{
                        h1: ({children}) => <h1 style={{color:'white',fontWeight:700,fontSize:'1.1rem',margin:'8px 0 4px'}}>{children}</h1>,
                        h2: ({children}) => <h2 style={{color:'white',fontWeight:600,fontSize:'1rem',margin:'8px 0 4px'}}>{children}</h2>,
                        h3: ({children}) => <h3 style={{color:'rgba(255,255,255,0.9)',fontWeight:600,fontSize:'0.95rem',margin:'6px 0 2px'}}>{children}</h3>,
                        p: ({children}) => <p style={{color:'rgba(255,255,255,0.85)',margin:'4px 0',lineHeight:1.6}}>{children}</p>,
                        strong: ({children}) => <strong style={{color:'white',fontWeight:600}}>{children}</strong>,
                        ul: ({children}) => <ul style={{paddingLeft:'1.2rem',margin:'4px 0'}}>{children}</ul>,
                        ol: ({children}) => <ol style={{paddingLeft:'1.2rem',margin:'4px 0'}}>{children}</ol>,
                        li: ({children}) => <li style={{color:'rgba(255,255,255,0.85)',margin:'2px 0'}}>{children}</li>,
                        code: ({children}) => <code style={{background:'rgba(255,255,255,0.1)',color:'#67e8f9',padding:'1px 5px',borderRadius:4,fontSize:'0.85em'}}>{children}</code>,
                        hr: () => <hr style={{borderColor:'rgba(255,255,255,0.1)',margin:'8px 0'}} />,
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  ) : (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  )}
                </div>
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
          <Button onClick={handleSend} disabled={!input.trim() || loading} size="sm" className="flex-shrink-0">
            <Send className="w-4 h-4" />
          </Button>
        </div>

        <p className="text-[10px] text-white/20 text-center mt-2">
          AI responses are for informational purposes only. Always consult a healthcare professional.
        </p>
      </div>
    </div>
  )
}
