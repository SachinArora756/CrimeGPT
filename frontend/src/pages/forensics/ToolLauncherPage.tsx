import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Microscope, Image, Film, FileText, Headphones, Fingerprint,
  Dna, ScanLine, Car, Shield, Crosshair, Hash, Search, Brain,
  Camera, Eye, Zap, ArrowRight, Layers
} from 'lucide-react'
import api from '../../api/client'

interface ToolDefinition {
  tool_key: string
  display_name: string
  category: string
  description: string | null
  icon: string | null
  accepted_file_types: string[] | string | null
  is_active: boolean
  max_file_size_mb: number
}

interface ToolCategory {
  category: string
  tools: ToolDefinition[]
}

function normalizeFileTypes(value: string[] | string | null | undefined): string[] {
  if (!value) return []
  if (Array.isArray(value)) return value
  if (typeof value === 'string') return value.split(',').map(s => s.trim()).filter(Boolean)
  return []
}

function formatFileTypes(value: string[] | string | null | undefined): string {
  const types = normalizeFileTypes(value)
  if (types.length === 0) return 'Any'
  if (types.includes('*/*')) return 'Any file'
  const short = types.slice(0, 3).map(t => {
    const ext = t.split('/').pop() || t
    return ext === '*' ? 'Any' : ext
  })
  return short.join(', ') + (types.length > 3 ? ` +${types.length - 3}` : '')
}

const categoryMeta: Record<string, { label: string; icon: typeof Microscope; color: string; bgColor: string; borderColor: string; gradient: string }> = {
  'Image Analysis': { label: 'Image & Video Analysis', icon: Image, color: 'text-blue-400', bgColor: 'bg-blue-500/10', borderColor: 'border-blue-500/20', gradient: 'from-blue-500/10 to-blue-500/5' },
  'Audio/Video': { label: 'Audio & Video', icon: Headphones, color: 'text-green-400', bgColor: 'bg-green-500/10', borderColor: 'border-green-500/20', gradient: 'from-green-500/10 to-green-500/5' },
  'Document Analysis': { label: 'Document Analysis', icon: FileText, color: 'text-amber-400', bgColor: 'bg-amber-500/10', borderColor: 'border-amber-500/20', gradient: 'from-amber-500/10 to-amber-500/5' },
  'Digital Forensics': { label: 'Digital Forensics', icon: Hash, color: 'text-cyan-400', bgColor: 'bg-cyan-500/10', borderColor: 'border-cyan-500/20', gradient: 'from-cyan-500/10 to-cyan-500/5' },
  'Biometric Analysis': { label: 'Biometric Analysis', icon: Fingerprint, color: 'text-purple-400', bgColor: 'bg-purple-500/10', borderColor: 'border-purple-500/20', gradient: 'from-purple-500/10 to-purple-500/5' },
  'Vehicle Analysis': { label: 'Vehicle Analysis', icon: Car, color: 'text-orange-400', bgColor: 'bg-orange-500/10', borderColor: 'border-orange-500/20', gradient: 'from-orange-500/10 to-orange-500/5' },
  'Threat Analysis': { label: 'Threat Analysis', icon: Shield, color: 'text-red-400', bgColor: 'bg-red-500/10', borderColor: 'border-red-500/20', gradient: 'from-red-500/10 to-red-500/5' },
}

const toolIcons: Record<string, typeof Microscope> = {
  image_ocr: ScanLine,
  image_object_detect: Eye,
  image_exif: Image,
  audio_transcribe: Headphones,
  document_ocr: ScanLine,
  document_pdf_parse: FileText,
  document_summarize: Brain,
  digital_hash: Hash,
  digital_verify_hash: Hash,
  digital_metadata: FileText,
  digital_file_identify: Search,
  face_detect: Camera,
  face_recognize: Fingerprint,
  fingerprint_match: Fingerprint,
  dna_search: Dna,
  vehicle_detect: Car,
  license_plate_ocr: Car,
  weapon_detect: Crosshair,
  image_similarity: Search,
  crime_scene_analysis: Microscope,
  video_extract_frames: Film,
}

export default function ToolLauncherPage() {
  const navigate = useNavigate()
  const [categories, setCategories] = useState<ToolCategory[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [activeCategory, setActiveCategory] = useState<string | null>(null)

  useEffect(() => {
    api.get('/api/forensic-toolkit/tools')
      .then(res => setCategories(res.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const filteredCategories = categories.map(cat => ({
    ...cat,
    tools: cat.tools.filter(t =>
      t.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.tool_key.toLowerCase().includes(searchTerm.toLowerCase())
    ),
  })).filter(cat => cat.tools.length > 0)

  const totalTools = categories.reduce((sum, c) => sum + c.tools.length, 0)
  const activeTools = categories.reduce((sum, c) => sum + c.tools.filter(t => t.is_active).length, 0)

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="h-20 rounded-2xl bg-dark-800/50 animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="h-28 rounded-xl bg-dark-800/50 animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 blur-lg" />
            <div className="relative w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center shadow-xl shadow-purple-500/20">
              <Microscope className="w-7 h-7 text-white" />
            </div>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Forensic Tool Launcher</h1>
            <p className="text-dark-400 text-sm">Select a forensic analysis tool to execute</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-dark-800 border border-dark-700/50">
            <Zap className="w-3.5 h-3.5 text-green-400" />
            <span className="text-xs text-dark-300">{activeTools}/{totalTools} active</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-dark-800 border border-dark-700/50">
            <Layers className="w-3.5 h-3.5 text-purple-400" />
            <span className="text-xs text-dark-300">{categories.length} categories</span>
          </div>
        </div>
      </div>

      {/* Search + Category Filter */}
      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search forensic tools..."
            className="w-full bg-dark-800/80 border border-dark-700/50 rounded-xl pl-11 pr-4 py-3 text-sm text-white placeholder-dark-500 outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/20 transition-all"
          />
        </div>
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
          <button
            onClick={() => setActiveCategory(null)}
            className={`px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
              !activeCategory ? 'bg-primary-500/10 text-primary-400 border border-primary-500/20' : 'text-dark-400 hover:text-white hover:bg-dark-800'
            }`}
          >
            All
          </button>
          {categories.map(cat => {
            const meta = categoryMeta[cat.category]
            return (
              <button
                key={cat.category}
                onClick={() => setActiveCategory(activeCategory === cat.category ? null : cat.category)}
                className={`px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                  activeCategory === cat.category
                    ? `${meta?.bgColor || 'bg-dark-700'} ${meta?.color || 'text-white'} border ${meta?.borderColor || 'border-dark-600'}`
                    : 'text-dark-400 hover:text-white hover:bg-dark-800'
                }`}
              >
                {meta?.label || cat.category}
              </button>
            )
          })}
        </div>
      </div>

      {/* Tool Categories */}
      <AnimatePresence mode="wait">
        <div className="space-y-8">
          {filteredCategories
            .filter(cat => !activeCategory || cat.category === activeCategory)
            .map((category, catIdx) => {
              const meta = categoryMeta[category.category] || {
                label: category.category, icon: Microscope, color: 'text-white',
                bgColor: 'bg-dark-700', borderColor: 'border-dark-600', gradient: 'from-dark-800 to-dark-900'
              }
              const CategoryIcon = meta.icon
              return (
                <motion.div
                  key={category.category}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: catIdx * 0.08 }}
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-8 h-8 rounded-lg ${meta.bgColor} flex items-center justify-center`}>
                      <CategoryIcon className={`w-4 h-4 ${meta.color}`} />
                    </div>
                    <h2 className={`text-sm font-bold ${meta.color}`}>{meta.label}</h2>
                    <div className="flex-1 h-px bg-dark-700/50" />
                    <span className="text-[10px] text-dark-500">{category.tools.length} tools</span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {category.tools.map((tool, toolIdx) => {
                      const ToolIcon = toolIcons[tool.tool_key] || Microscope
                      return (
                        <motion.button
                          key={tool.tool_key}
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: catIdx * 0.08 + toolIdx * 0.03 }}
                          onClick={() => navigate(`/forensics/execute/${tool.tool_key}`)}
                          disabled={!tool.is_active}
                          className={`group relative text-left p-4 rounded-xl border transition-all duration-200 overflow-hidden disabled:opacity-30 disabled:cursor-not-allowed ${
                            tool.is_active
                              ? `bg-gradient-to-br ${meta.gradient} border-dark-700/50 hover:border-${meta.color.replace('text-', '')}/30 hover:shadow-lg hover:shadow-${meta.color.replace('text-', '')}/5 hover:-translate-y-0.5`
                              : 'bg-dark-900/50 border-dark-700/30'
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            <div className={`w-10 h-10 rounded-xl ${meta.bgColor} border ${meta.borderColor} flex items-center justify-center group-hover:scale-110 transition-transform duration-200`}>
                              <ToolIcon className={`w-5 h-5 ${meta.color}`} />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <p className="text-sm font-semibold text-white group-hover:text-primary-300 transition-colors truncate">
                                  {tool.display_name}
                                </p>
                                <ArrowRight className="w-3.5 h-3.5 text-dark-600 group-hover:text-primary-400 opacity-0 group-hover:opacity-100 transition-all -translate-x-1 group-hover:translate-x-0" />
                              </div>
                              <p className="text-[11px] text-dark-400 mt-1 line-clamp-2 leading-relaxed">
                                {tool.description || 'Execute forensic analysis'}
                              </p>
                              {tool.accepted_file_types && normalizeFileTypes(tool.accepted_file_types).length > 0 && (
                                <div className="flex items-center gap-1 mt-2">
                                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-dark-800 text-dark-500 border border-dark-700/50">
                                    {formatFileTypes(tool.accepted_file_types)}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                          {!tool.is_active && (
                            <div className="absolute top-2 right-2">
                              <span className="text-[9px] px-1.5 py-0.5 rounded bg-dark-700 text-dark-500">Offline</span>
                            </div>
                          )}
                        </motion.button>
                      )
                    })}
                  </div>
                </motion.div>
              )
            })}
        </div>
      </AnimatePresence>

      {filteredCategories.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16">
          <div className="w-16 h-16 rounded-2xl bg-dark-800 flex items-center justify-center mb-4">
            <Search className="w-7 h-7 text-dark-500" />
          </div>
          <p className="text-dark-400 text-sm">No tools match your search</p>
          <button
            onClick={() => { setSearchTerm(''); setActiveCategory(null) }}
            className="mt-3 text-xs text-primary-400 hover:text-primary-300"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  )
}
