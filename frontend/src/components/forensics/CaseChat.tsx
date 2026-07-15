import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MessageSquare, Send, Mic, MicOff, Loader2, User, Bot,
  ChevronDown, ChevronUp, AlertCircle,
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
}

interface CaseChatProps {
  sessionId: string | null
  disabled?: boolean
  accentColor?: 'emerald' | 'purple'
}

export default function CaseChat({ sessionId, disabled = false, accentColor = 'emerald' }: CaseChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputText, setInputText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isExpanded, setIsExpanded] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

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
    }
  }, [sessionId])

  const sendMessage = async () => {
    if (!inputText.trim() || !sessionId || isLoading || disabled) return

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: inputText.trim(),
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    setInputText('')
    setIsLoading(true)

    try {
      const res = await api.post(`/api/ai-investigation/sessions/${sessionId}/message`, {
        message: userMsg.content,
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

  const accent = accentColor === 'purple'
    ? { border: 'border-purple-500/30', bg: 'bg-purple-500/10', text: 'text-purple-400', btn: 'from-purple-600 to-purple-500' }
    : { border: 'border-emerald-500/30', bg: 'bg-emerald-500/10', text: 'text-emerald-400', btn: 'from-emerald-600 to-emerald-500' }

  const chatDisabled = !sessionId || disabled

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-2xl border ${sessionId ? accent.border : 'border-dark-700/50'} bg-dark-900/80 overflow-hidden`}
    >
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-dark-800/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <MessageSquare className={`w-4 h-4 ${sessionId ? accent.text : 'text-dark-500'}`} />
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
              <div className="h-64 overflow-y-auto px-4 py-3 space-y-3">
                {!sessionId && (
                  <div className="h-full flex items-center justify-center">
                    <p className="text-dark-500 text-sm text-center">Upload evidence to start the investigation chat</p>
                  </div>
                )}
                {sessionId && messages.length === 0 && !isLoading && (
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center">
                      <MessageSquare className="w-8 h-8 text-dark-600 mx-auto mb-2" />
                      <p className="text-dark-500 text-sm">Describe your case or ask questions about the analysis</p>
                      <p className="text-dark-600 text-xs mt-1">Use the mic button to dictate with voice</p>
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
                      <Loader2 className="w-4 h-4 text-dark-400 animate-spin" />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

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
                    disabled={chatDisabled || isTranscribing}
                    className={`shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all ${
                      isRecording
                        ? 'bg-red-500/20 border border-red-500/50 animate-pulse'
                        : isTranscribing
                          ? 'bg-dark-800 border border-dark-700'
                          : chatDisabled
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
                      <Mic className={`w-4 h-4 ${chatDisabled ? 'text-dark-600' : 'text-dark-300'}`} />
                    )}
                  </button>

                  {/* Textarea */}
                  <textarea
                    ref={inputRef}
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={chatDisabled}
                    placeholder={
                      isRecording ? 'Recording... click mic to stop'
                        : isTranscribing ? 'Transcribing your voice...'
                        : chatDisabled ? 'Upload evidence first...'
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
                    disabled={chatDisabled || !inputText.trim() || isLoading}
                    className={`shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all ${
                      !chatDisabled && inputText.trim() && !isLoading
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
