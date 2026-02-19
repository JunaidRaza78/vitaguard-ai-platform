import { useState, useCallback, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, Search, FileText, CheckCircle, AlertCircle, CloudUpload, Bot, Send, Sparkles, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import GlassCard from '@/components/ui/GlassCard'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import EmptyState from '@/components/ui/EmptyState'
import api from '@/lib/axios'
import toast from 'react-hot-toast'

const QUICK_PROMPTS = [
  'Summarize the uploaded documents',
  'What are the key findings?',
  'List any abnormal values or concerns',
  'What follow-up actions are recommended?',
]

export default function DocumentsPage() {
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState([])

  // Document Q&A state
  const [qaMessages, setQaMessages] = useState([])
  const [qaInput, setQaInput] = useState('')
  const [qaLoading, setQaLoading] = useState(false)
  const qaEndRef = useRef(null)

  useEffect(() => {
    qaEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [qaMessages])

  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true)
    else if (e.type === 'dragleave') setDragActive(false)
  }, [])

  const handleUpload = async (files) => {
    if (!files?.length) return
    setUploading(true)
    setUploadProgress(0)

    for (const file of files) {
      if (file.type !== 'application/pdf') {
        toast.error(`${file.name}: Only PDF files are supported`)
        continue
      }

      const formData = new FormData()
      formData.append('file', file)

      try {
        await api.post('/api/v1/documents/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (e) => {
            setUploadProgress(Math.round((e.loaded * 100) / e.total))
          },
        })
        setUploadedFiles(prev => [...prev, { name: file.name, status: 'success', date: new Date() }])
        toast.success(`${file.name} uploaded — embeddings processing in background`)
      } catch {
        setUploadedFiles(prev => [...prev, { name: file.name, status: 'error', date: new Date() }])
        toast.error(`Failed to upload ${file.name}`)
      }
    }
    setUploading(false)
    setUploadProgress(0)
  }

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragActive(false)
    handleUpload(e.dataTransfer.files)
  }, [])

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    setSearching(true)
    try {
      const { data } = await api.post('/api/v1/documents/search', {
        query: searchQuery,
        top_k: 5,
      })
      setSearchResults(data.results || data || [])
    } catch {
      toast.error('Search failed')
    } finally {
      setSearching(false)
    }
  }

  const askDocument = async (question) => {
    const q = (question || qaInput).trim()
    if (!q || qaLoading) return
    setQaInput('')

    setQaMessages(prev => [...prev, { role: 'user', content: q }])
    setQaLoading(true)

    try {
      const { data } = await api.post('/api/v1/documents/ask', { question: q })
      const answer = data.answer || 'No answer available.'
      setQaMessages(prev => [...prev, {
        role: 'assistant',
        content: answer,
        sources: data.sources || [],
        contextUsed: data.context_used,
      }])
    } catch {
      setQaMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I could not process your question. Please try again.',
      }])
    } finally {
      setQaLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <GlassCard>
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-10 text-center transition-all duration-300 ${
            dragActive
              ? 'border-cyan-400 bg-cyan-500/5'
              : 'border-white/15 hover:border-white/30'
          }`}
        >
          <motion.div animate={{ y: dragActive ? -5 : 0 }} className="flex flex-col items-center">
            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-4 ${
              dragActive ? 'bg-cyan-500/20' : 'bg-white/5'
            }`}>
              <CloudUpload className={`w-7 h-7 ${dragActive ? 'text-cyan-400' : 'text-white/40'}`} />
            </div>
            <p className="text-sm text-white/70 mb-1">
              {dragActive ? 'Drop files here' : 'Drag & drop medical PDFs here'}
            </p>
            <p className="text-xs text-white/30 mb-4">or click to browse</p>
            <input
              type="file"
              accept=".pdf"
              multiple
              onChange={(e) => handleUpload(e.target.files)}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload">
              <Button as="span" variant="outline" size="sm" className="cursor-pointer">
                <Upload className="w-4 h-4" />
                Browse Files
              </Button>
            </label>
          </motion.div>

          {uploading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-4">
              <div className="w-full h-2 rounded-full bg-white/10 overflow-hidden">
                <motion.div
                  animate={{ width: `${uploadProgress}%` }}
                  className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-500"
                />
              </div>
              <p className="text-xs text-white/40 mt-1">{uploadProgress}%</p>
            </motion.div>
          )}
        </div>

        {uploadedFiles.length > 0 && (
          <div className="mt-4 space-y-2">
            <p className="text-xs text-white/40 uppercase tracking-wider mb-2">Recent Uploads</p>
            {uploadedFiles.map((file, i) => (
              <div key={i} className="flex items-center gap-3 glass rounded-lg p-3">
                <FileText className="w-4 h-4 text-white/40" />
                <span className="text-sm text-white/80 flex-1 truncate">{file.name}</span>
                {file.status === 'success' ? (
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-rose-400" />
                )}
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* Document Q&A */}
      <GlassCard glow="cyan">
        <div className="flex items-center gap-2 mb-4">
          <Bot className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-white/80">Ask AI About Documents</h3>
        </div>

        {/* Quick prompts */}
        <div className="flex flex-wrap gap-2 mb-4">
          {QUICK_PROMPTS.map((p) => (
            <button
              key={p}
              onClick={() => askDocument(p)}
              disabled={qaLoading}
              className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-full glass text-white/60 hover:text-cyan-400 hover:border-cyan-500/30 border border-white/10 transition-all disabled:opacity-40"
            >
              <Sparkles className="w-3 h-3" />
              {p}
            </button>
          ))}
        </div>

        {/* Messages */}
        {qaMessages.length > 0 && (
          <div className="glass rounded-xl p-4 mb-4 max-h-80 overflow-y-auto space-y-4">
            {qaMessages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div className={`w-7 h-7 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-br from-violet-500 to-fuchsia-500'
                    : 'bg-gradient-to-br from-cyan-500 to-emerald-500'
                }`}>
                  {msg.role === 'user'
                    ? <User className="w-3.5 h-3.5 text-white" />
                    : <Bot className="w-3.5 h-3.5 text-white" />}
                </div>
                <div className={`max-w-[80%] rounded-2xl p-3 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 border border-violet-500/20 text-white'
                    : 'glass text-white/90'
                }`}>
                  {msg.role === 'assistant' ? (
                    <ReactMarkdown
                      components={{
                        h1: ({children}) => <h1 style={{color:'white',fontWeight:700,fontSize:'1.05rem',margin:'6px 0 3px'}}>{children}</h1>,
                        h2: ({children}) => <h2 style={{color:'white',fontWeight:600,fontSize:'0.95rem',margin:'6px 0 3px'}}>{children}</h2>,
                        h3: ({children}) => <h3 style={{color:'rgba(255,255,255,0.9)',fontWeight:600,fontSize:'0.9rem',margin:'4px 0 2px'}}>{children}</h3>,
                        p: ({children}) => <p style={{color:'rgba(255,255,255,0.85)',margin:'3px 0',lineHeight:1.6}}>{children}</p>,
                        strong: ({children}) => <strong style={{color:'white',fontWeight:600}}>{children}</strong>,
                        ul: ({children}) => <ul style={{paddingLeft:'1.2rem',margin:'3px 0'}}>{children}</ul>,
                        ol: ({children}) => <ol style={{paddingLeft:'1.2rem',margin:'3px 0'}}>{children}</ol>,
                        li: ({children}) => <li style={{color:'rgba(255,255,255,0.85)',margin:'2px 0'}}>{children}</li>,
                        code: ({children}) => <code style={{background:'rgba(255,255,255,0.1)',color:'#67e8f9',padding:'1px 4px',borderRadius:3,fontSize:'0.85em'}}>{children}</code>,
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  ) : (
                    <p>{msg.content}</p>
                  )}
                  {msg.sources?.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-white/10">
                      <p className="text-[10px] text-white/30 uppercase tracking-wider mb-1">Sources</p>
                      {msg.sources.map((src, j) => (
                        <p key={j} className="text-[11px] text-cyan-400/70 truncate">• {src}</p>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}

            {qaLoading && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
                <div className="w-7 h-7 rounded-xl bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center">
                  <Bot className="w-3.5 h-3.5 text-white" />
                </div>
                <div className="glass rounded-2xl px-4 py-3">
                  <div className="flex gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </motion.div>
            )}
            <div ref={qaEndRef} />
          </div>
        )}

        {/* Input */}
        <div className="flex gap-3">
          <div className="flex-1">
            <Input
              placeholder="Ask anything about your documents..."
              value={qaInput}
              onChange={(e) => setQaInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && askDocument()}
            />
          </div>
          <Button onClick={() => askDocument()} disabled={!qaInput.trim() || qaLoading} loading={qaLoading}>
            <Send className="w-4 h-4" />
          </Button>
        </div>
        <p className="text-[10px] text-white/20 mt-2">
          AI answers based on your uploaded documents and medical knowledge base.
        </p>
      </GlassCard>

      {/* Semantic Search */}
      <GlassCard>
        <h3 className="text-sm font-semibold text-white/80 mb-3">Search Documents</h3>
        <div className="flex gap-3">
          <div className="flex-1">
            <Input
              placeholder="Search your medical records..."
              icon={Search}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>
          <Button onClick={handleSearch} loading={searching}>Search</Button>
        </div>

        <AnimatePresence>
          {searchResults.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mt-4 space-y-2"
            >
              {searchResults.map((result, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="glass rounded-xl p-4"
                >
                  <div className="flex items-start gap-3">
                    <FileText className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {result.metadata?.source || result.title || 'Document'}
                      </p>
                      <p className="text-xs text-white/50 mt-1 line-clamp-3">
                        {result.content || result.text || result.document}
                      </p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </GlassCard>

      {uploadedFiles.length === 0 && searchResults.length === 0 && qaMessages.length === 0 && (
        <EmptyState
          icon={FileText}
          title="No documents yet"
          description="Upload medical PDFs then ask AI to summarize or answer questions from them"
        />
      )}
    </div>
  )
}
