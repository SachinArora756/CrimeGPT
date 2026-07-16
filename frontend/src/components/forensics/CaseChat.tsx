import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MessageSquare, Send, Mic, MicOff, Loader2, User, Bot,
  ChevronDown, ChevronUp, AlertCircle, Paperclip, Image, X,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import api from '../../api/client'
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  attachments?: { name: string; url?: string }[]
}

interface CaseChatProps {
  sessionId: string | null
  onSessionCreated?: (sessionId: string) => void
  disabled?: boolean
  accentColor?: 'emerald' | 'purple'
}

export default function CaseChat({ sessionId, onSessionCreated, disabled = false, accentColor = 'emerald' }: CaseChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputText, setInputText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isExpanded, setIsExpanded] = useState(true)
  const [pendingFiles, setPendingFiles] = useState<File[]>([])
  const [pendingPreviews, setPendingPreviews] = useState<(string | null)[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const internalSessionRef = useRef<string | null>(sessionId)

  useEffect(() => {
    internalSessionRef.current = sessionId
  }, [sessionId])

  const onTranscript = useCallback((text: string) => {
    setInputText(prev => prev ? prev + ' ' + text : text)
    inputRef.current?.focus()
  }, [])

  const { isRecording, isTranscribing, startRecording, stopAndTranscribe, cancelRecording, error: voiceError } = useVoiceRecorder(onTranscript)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (!sessionId) {
      setMessages([])
      setInputText('')
      internalSessionRef.current = null
    }
  }, [sessionId])

  const ensureSession = async (): Promise<string> => {
    if (internalSessionRef.current) return internalSessionRef.current
    const res = await api.post('/api/ai-investigation/sessions', { title: 'Chat Session' })
    const newId = res.data.session_id
    internalSessionRef.current = newId
    onSessionCreated?.(newId)
    return newId
  }


  const sendMessage = async () => {
    if ((!inputText.trim() && !pendingFiles.length) || isLoading || disabled) return

    const messageText = inputText.trim()
    const filesToSend = [...pendingFiles]
    const previewsToSend = [...pendingPreviews]

    setInputText('')
    setPendingFiles([])
    setPendingPreviews([])
    setIsLoading(true)

    const userAttachments = filesToSend.map((f, i) => ({
      name: f.name,
      url: previewsToSend[i] || undefined,
    }))

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: messageText || `Attached ${filesToSend.length} file${filesToSend.length > 1 ? 's' : ''}`,
      timestamp: new Date().toISOString(),
      attachments: userAttachments.length ? userAttachments : undefined,
    }
    setMessages(prev => [...prev, userMsg])

    try {
      const sid = await ensureSession()

      if (filesToSend.length) {
        setIsUploading(true)
        for (const file of filesToSend) {
          const formData = new FormData()
          formData.append('file', file)
          await api.post(`/api/ai-investigation/sessions/${sid}/upload`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
          })
        }
        setIsUploading(false)
      }

      const res = await api.post(`/api/ai-investigation/sessions/${sid}/message`, {
        message: messageText || `I've uploaded ${filesToSend.length} evidence file(s). Please analyze them.`,
      })
      setMessages(prev => [...prev, {
        id: res.data.assistant_message.message_id,
        role: 'assistant',
        content: res.data.assistant_message.content,
        timestamp: res.data.assistant_message.created_at,
      }])
    } catch {
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Sorry, I could not process your message. Please try again.',
        timestamp: new Date().toISOString(),
      }])
    } finally {
      setIsLoading(false)
      setIsUploading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleMicClick = () => {
    if (isRecording) {
      stopAndTranscribe()
    } else {
      startRecording()
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = e.target.files
    if (!fileList?.length) return
    const newFiles = Array.from(fileList)
    const newPreviews = newFiles.map(f => f.type.startsWith('image/') ? URL.createObjectURL(f) : null)
    setPendingFiles(prev => [...prev, ...newFiles])
    setPendingPreviews(prev => [...prev, ...newPreviews])
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const removePendingFile = (index: number) => {
    setPendingFiles(prev => prev.filter((_, i) => i !== index))
    setPendingPreviews(prev => prev.filter((_, i) => i !== index))
  }

  const accent = accentColor === 'purple'
    ? { border: 'border-purple-500/30', bg: 'bg-purple-500/10', text: 'text-purple-400', btn: 'from-purple-600 to-purple-500' }
    : { border: 'border-emerald-500/30', bg: 'bg-emerald-500/10', text: 'text-emerald-400', btn: 'from-emerald-600 to-emerald-500' }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-2xl border ${accent.border} bg-dark-900/80 overflow-hidden`}
    >
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*,application/pdf,audio/*,video/*,text/*"
        className="hidden"
        onChange={handleFileSelect}
      />

      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-dark-800/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <MessageSquare className={`w-4 h-4 ${accent.text}`} />
          <span className="text-sm font-medium text-white">Case Discussion</span>
          {messages.length > 0 && (
            <span className="px-1.5 py-0.5 rounded-full text-[9px] bg-dark-700 text-dark-300">{messages.length}</span>
          )}
        </div>
        {isExpanded ? <ChevronUp className="w-4 h-4 text-dark-400" /> : <ChevronDown className="w-4 h-4 text-dark-400" />}
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden">
            <div className="border-t border-dark-700/50">
              {/* Messages area */}
              <div className="h-72 overflow-y-auto px-4 py-3 space-y-3">
                {messages.length === 0 && !isLoading && (
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center">
                      <MessageSquare className="w-8 h-8 text-dark-600 mx-auto mb-2" />
                      <p className="text-dark-500 text-sm">Describe your case or ask questions</p>
                      <p className="text-dark-600 text-xs mt-1">You can attach evidence files anytime using the clip icon</p>
                    </div>
                  </div>
                )}
                {messages.map((msg) => (
                  <div key={msg.id} className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    {msg.role === 'assistant' && (
                      <div className={`w-6 h-6 rounded-full ${accent.bg} flex items-center justify-center shrink-0 mt-1`}>
                        <Bot className={`w-3.5 h-3.5 ${accent.text}`} />
                      </div>
                    )}
                    <div className={`max-w-[80%] rounded-xl px-3 py-2 ${
                      msg.role === 'user'
                        ? 'bg-dark-700 text-dark-100'
                        : 'bg-dark-800/50 border border-dark-700/30 text-dark-200'
                    }`}>
                      {/* Attachments */}
                      {msg.attachments && msg.attachments.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mb-1.5">
                          {msg.attachments.map((att, i) => (
                            <div key={i} className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-dark-600/50 border border-dark-600">
                              <Image className="w-3 h-3 text-dark-400" />
                              <span className="text-[10px] text-dark-300 truncate max-w-[100px]">{att.name}</span>
                            </div>
                          ))}
                        </div>
                      )}
                      {msg.role === 'assistant' ? (
                        <div className="prose prose-invert prose-xs max-w-none text-[13px] leading-relaxed">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                        </div>
                      ) : (
                        <p className="text-[13px] leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                      )}
                    </div>
                    {msg.role === 'user' && (
                      <div className="w-6 h-6 rounded-full bg-dark-700 flex items-center justify-center shrink-0 mt-1">
                        <User className="w-3.5 h-3.5 text-dark-300" />
                      </div>
                    )}
                  </div>
                ))}
                {isLoading && (
                  <div className="flex gap-2 justify-start">
                    <div className={`w-6 h-6 rounded-full ${accent.bg} flex items-center justify-center shrink-0`}>
                      <Bot className={`w-3.5 h-3.5 ${accent.text}`} />
                    </div>
                    <div className="bg-dark-800/50 border border-dark-700/30 rounded-xl px-3 py-2">
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 text-dark-400 animate-spin" />
                        {isUploading && <span className="text-[11px] text-dark-500">Uploading files...</span>}
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Pending files preview */}
              {pendingFiles.length > 0 && (
                <div className="px-4 pb-2">
                  <div className="flex flex-wrap gap-2">
                    {pendingFiles.map((f, idx) => (
                      <div key={idx} className="relative group flex items-center gap-1.5 px-2 py-1 rounded-lg bg-dark-800 border border-dark-700/50">
                        {pendingPreviews[idx] ? (
                          <img src={pendingPreviews[idx]!} alt={f.name} className="w-6 h-6 rounded object-cover" />
                        ) : (
                          <Image className="w-4 h-4 text-dark-400" />
                        )}
                        <span className="text-[11px] text-dark-300 max-w-[80px] truncate">{f.name}</span>
                        <button
                          onClick={() => removePendingFile(idx)}
                          className="w-4 h-4 rounded-full bg-dark-700 hover:bg-red-500/30 flex items-center justify-center transition-colors"
                        >
                          <X className="w-2.5 h-2.5 text-dark-400 hover:text-red-400" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Voice error */}
              {voiceError && (
                <div className="px-4 pb-2">
                  <div className="flex items-center gap-2 text-xs text-red-400 bg-red-500/10 rounded-lg px-3 py-1.5">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    <span>{voiceError}</span>
                  </div>
                </div>
              )}

              {/* Input area */}
              <div className="px-4 pb-4 pt-2 border-t border-dark-800/50">
                <div className="flex items-end gap-2">
                  {/* Mic button */}
                  <button
                    onClick={handleMicClick}
                    disabled={disabled || isTranscribing}
                    className={`shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all ${
                      isRecording
                        ? 'bg-red-500/20 border border-red-500/50 animate-pulse'
                        : isTranscribing
                          ? 'bg-dark-800 border border-dark-700'
                          : disabled
                            ? 'bg-dark-800/50 border border-dark-700/30 cursor-not-allowed'
                            : 'bg-dark-800 border border-dark-700 hover:border-dark-600'
                    }`}
                    title={isRecording ? 'Stop & transcribe' : isTranscribing ? 'Transcribing...' : 'Record voice'}
                  >
                    {isTranscribing ? (
                      <Loader2 className="w-4 h-4 text-dark-400 animate-spin" />
                    ) : isRecording ? (
                      <MicOff className="w-4 h-4 text-red-400" />
                    ) : (
                      <Mic className={`w-4 h-4 ${disabled ? 'text-dark-600' : 'text-dark-300'}`} />
                    )}
                  </button>

                  {/* Attachment button */}
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={disabled || isLoading}
                    className={`shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all ${
                      disabled || isLoading
                        ? 'bg-dark-800/50 border border-dark-700/30 cursor-not-allowed'
                        : 'bg-dark-800 border border-dark-700 hover:border-dark-600'
                    }`}
                    title="Attach evidence files"
                  >
                    <Paperclip className={`w-4 h-4 ${disabled || isLoading ? 'text-dark-600' : 'text-dark-300'}`} />
                  </button>

                  {/* Textarea */}
                  <textarea
                    ref={inputRef}
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={disabled}
                    placeholder={
                      isRecording ? 'Recording... click mic to stop'
                        : isTranscribing ? 'Transcribing your voice...'
                        : disabled ? 'Processing...'
                        : 'Describe the case or ask a question...'
                    }
                    rows={1}
                    className="flex-1 bg-dark-800 border border-dark-700 rounded-xl px-3 py-2 text-sm text-dark-100 placeholder-dark-500 resize-none focus:outline-none focus:border-dark-600 disabled:opacity-50 disabled:cursor-not-allowed min-h-[36px] max-h-[100px]"
                    style={{ height: 'auto', overflow: 'hidden' }}
                    onInput={(e) => {
                      const t = e.target as HTMLTextAreaElement
                      t.style.height = 'auto'
                      t.style.height = Math.min(t.scrollHeight, 100) + 'px'
                    }}
                  />

                  {/* Send button */}
                  <button
                    onClick={sendMessage}
                    disabled={disabled || (!inputText.trim() && !pendingFiles.length) || isLoading}
                    className={`shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all ${
                      !disabled && (inputText.trim() || pendingFiles.length) && !isLoading
                        ? `bg-gradient-to-r ${accent.btn} text-white shadow-lg`
                        : 'bg-dark-800/50 border border-dark-700/30 text-dark-600 cursor-not-allowed'
                    }`}
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>

                {/* Recording indicator */}
                {isRecording && (
                  <div className="flex items-center gap-2 mt-2">
                    <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                    <span className="text-[11px] text-red-400">Recording... click mic to stop and transcribe</span>
                    <button onClick={cancelRecording} className="text-[11px] text-dark-500 hover:text-dark-300 ml-auto">Cancel</button>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
