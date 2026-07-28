import { motion } from 'framer-motion'
import { X, Check, Camera, AlertTriangle, Zap } from 'lucide-react'

interface AutoEnhanceResultProps {
  originalUrl: string
  enhancedUrl: string
  issues: Array<{ type: string; severity: string; score?: number; brightness?: number }>
  enhancementsApplied?: string[]
  onAcceptEnhanced: () => void
  onKeepOriginal: () => void
  onRetake: () => void
  onClose: () => void
}

const issueLabels: Record<string, string> = {
  blur: 'Blurry Image',
  underexposure: 'Too Dark',
  overexposure: 'Too Bright',
  low_contrast: 'Low Contrast',
}

const enhancementLabels: Record<string, string> = {
  deblur: 'Deblur',
  sharpness: 'Sharpen',
  low_light: 'Low-Light Fix',
  auto_levels: 'Auto Levels',
  contrast: 'Contrast Boost',
}

export default function AutoEnhanceResult({
  originalUrl,
  enhancedUrl,
  issues,
  enhancementsApplied,
  onAcceptEnhanced,
  onKeepOriginal,
  onRetake,
  onClose,
}: AutoEnhanceResultProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-dark-900 border border-dark-700 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-dark-700/50">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-amber-500/10">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Quality Issues Detected</h3>
              <p className="text-xs text-dark-400">Auto-enhanced version created for comparison</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-xl hover:bg-dark-700/50 transition-colors">
            <X className="w-5 h-5 text-dark-400" />
          </button>
        </div>

        {/* Comparison */}
        <div className="p-5">
          <div className="grid grid-cols-2 gap-4 mb-5">
            <div>
              <p className="text-xs text-dark-400 mb-2 text-center font-medium">Original</p>
              <div className="rounded-xl overflow-hidden border border-red-500/30 bg-dark-800">
                <img src={originalUrl} alt="Original" className="w-full h-64 object-contain" />
              </div>
            </div>
            <div>
              <p className="text-xs text-dark-400 mb-2 text-center font-medium">Enhanced</p>
              <div className="rounded-xl overflow-hidden border border-green-500/30 bg-dark-800">
                <img src={enhancedUrl} alt="Enhanced" className="w-full h-64 object-contain" />
              </div>
            </div>
          </div>

          {/* Issues & Enhancements */}
          <div className="grid grid-cols-2 gap-4 mb-5">
            <div className="p-4 rounded-xl bg-red-500/5 border border-red-500/20">
              <p className="text-[10px] text-red-400 uppercase tracking-wider mb-2 font-semibold">Issues Found</p>
              <ul className="space-y-1.5">
                {issues.map((issue, i) => (
                  <li key={i} className="flex items-center gap-2 text-xs text-dark-300">
                    <AlertTriangle className="w-3 h-3 text-red-400 flex-shrink-0" />
                    <span>{issueLabels[issue.type] || issue.type}</span>
                    <span className={`ml-auto text-[10px] px-1.5 py-0.5 rounded ${
                      issue.severity === 'high' ? 'bg-red-500/20 text-red-300' : 'bg-amber-500/20 text-amber-300'
                    }`}>
                      {issue.severity}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="p-4 rounded-xl bg-green-500/5 border border-green-500/20">
              <p className="text-[10px] text-green-400 uppercase tracking-wider mb-2 font-semibold">Enhancements Applied</p>
              <ul className="space-y-1.5">
                {(enhancementsApplied || []).map((enh, i) => (
                  <li key={i} className="flex items-center gap-2 text-xs text-dark-300">
                    <Zap className="w-3 h-3 text-green-400 flex-shrink-0" />
                    <span>{enhancementLabels[enh] || enh}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3 justify-end">
            <button
              onClick={onRetake}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-dark-700/50 border border-dark-600 text-dark-300 text-sm font-medium hover:bg-dark-700 transition-colors"
            >
              <Camera className="w-4 h-4" /> Retake Photo
            </button>
            <button
              onClick={onKeepOriginal}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-dark-700/50 border border-dark-600 text-dark-300 text-sm font-medium hover:bg-dark-700 transition-colors"
            >
              Keep Original
            </button>
            <button
              onClick={onAcceptEnhanced}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-green-600 to-emerald-600 text-white text-sm font-medium hover:from-green-500 hover:to-emerald-500 transition-all"
            >
              <Check className="w-4 h-4" /> Use Enhanced
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}
