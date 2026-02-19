import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, Search, FileText, X, CheckCircle, AlertCircle, CloudUpload } from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Badge from '@/components/ui/Badge'
import EmptyState from '@/components/ui/EmptyState'
import api from '@/lib/axios'
import toast from 'react-hot-toast'

export default function DocumentsPage() {
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState([])

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
        toast.success(`${file.name} uploaded successfully`)
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
      const { data } = await api.get('/api/v1/documents/search', {
        params: { query: searchQuery },
      })
      setSearchResults(data.results || data || [])
    } catch {
      toast.error('Search failed')
    } finally {
      setSearching(false)
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
          <motion.div
            animate={{ y: dragActive ? -5 : 0 }}
            className="flex flex-col items-center"
          >
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

          {/* Upload progress */}
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
      </GlassCard>

      {/* Search */}
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

        {/* Search Results */}
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
                      {result.score && (
                        <Badge color="cyan" className="mt-2">
                          Relevance: {(result.score * 100).toFixed(0)}%
                        </Badge>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </GlassCard>

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <GlassCard>
          <h3 className="text-sm font-semibold text-white/80 mb-3">Recent Uploads</h3>
          <div className="space-y-2">
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
        </GlassCard>
      )}

      {uploadedFiles.length === 0 && searchResults.length === 0 && (
        <EmptyState
          icon={FileText}
          title="No documents yet"
          description="Upload medical PDFs to search through your health records with AI"
        />
      )}
    </div>
  )
}
