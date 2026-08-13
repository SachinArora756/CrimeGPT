import { motion } from 'framer-motion'

interface CrimeGPTLogoProps {
  size?: 'sm' | 'md' | 'lg'
  animate?: boolean
  showText?: boolean
  subtitle?: string
}

export default function CrimeGPTLogo({ size = 'lg', animate = true, showText = true, subtitle }: CrimeGPTLogoProps) {
  const dimensions = { sm: 40, md: 56, lg: 80 }[size]
  const textSize = { sm: 'text-base', md: 'text-xl', lg: 'text-[28px]' }[size]
  const subSize = { sm: 'text-[9px]', md: 'text-xs', lg: 'text-sm' }[size]

  return (
    <div className="flex flex-col items-center">
      <motion.div
        initial={animate ? { scale: 0, rotate: -180 } : false}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ duration: 0.7, delay: 0.1, type: 'spring', stiffness: 120 }}
        className="relative inline-flex"
      >
        {/* Outer rotating ring */}
        <motion.div
          animate={animate ? { rotate: 360 } : undefined}
          transition={{ duration: 25, repeat: Infinity, ease: 'linear' }}
          className="absolute -inset-2"
        >
          <svg viewBox="0 0 100 100" className="w-full h-full" fill="none">
            <circle cx="50" cy="50" r="46" stroke="url(#ringGrad)" strokeWidth="0.8" strokeDasharray="4 6" opacity="0.5" />
          </svg>
        </motion.div>

        {/* Inner counter-rotating ring */}
        <motion.div
          animate={animate ? { rotate: -360 } : undefined}
          transition={{ duration: 18, repeat: Infinity, ease: 'linear' }}
          className="absolute -inset-3"
        >
          <svg viewBox="0 0 100 100" className="w-full h-full" fill="none">
            <circle cx="50" cy="50" r="48" stroke="url(#ringGrad2)" strokeWidth="0.5" strokeDasharray="2 8" opacity="0.3" />
          </svg>
        </motion.div>

        {/* Main logo container */}
        <div
          className="relative rounded-2xl flex items-center justify-center overflow-hidden"
          style={{ width: dimensions, height: dimensions }}
        >
          {/* Background gradient */}
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-600 via-blue-700 to-cyan-800 rounded-2xl" />

          {/* Animated mesh overlay */}
          <div className="absolute inset-0 opacity-20">
            <svg viewBox="0 0 80 80" className="w-full h-full">
              <defs>
                <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#818cf8" />
                  <stop offset="100%" stopColor="#06b6d4" />
                </linearGradient>
                <linearGradient id="ringGrad2" x1="100%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#c084fc" />
                  <stop offset="100%" stopColor="#22d3ee" />
                </linearGradient>
              </defs>
              {/* Circuit board pattern */}
              <path d="M10 40 H25 L30 35 H50 L55 40 H70" stroke="#fff" strokeWidth="0.8" fill="none" />
              <path d="M40 10 V25 L35 30 V50 L40 55 V70" stroke="#fff" strokeWidth="0.8" fill="none" />
              <path d="M15 20 H30 L35 25" stroke="#fff" strokeWidth="0.5" fill="none" />
              <path d="M50 60 H65 L70 55" stroke="#fff" strokeWidth="0.5" fill="none" />
              <circle cx="25" cy="40" r="1.5" fill="#fff" />
              <circle cx="55" cy="40" r="1.5" fill="#fff" />
              <circle cx="40" cy="25" r="1.5" fill="#fff" />
              <circle cx="40" cy="55" r="1.5" fill="#fff" />
              <circle cx="30" cy="35" r="1" fill="#fff" />
              <circle cx="50" cy="45" r="1" fill="#fff" />
            </svg>
          </div>

          {/* Main icon: Shield with AI brain */}
          <svg
            viewBox="0 0 48 48"
            className="relative z-10"
            style={{ width: dimensions * 0.6, height: dimensions * 0.6 }}
            fill="none"
          >
            {/* Shield outline */}
            <path
              d="M24 4 L40 10 V22 C40 33 33 40 24 44 C15 40 8 33 8 22 V10 L24 4Z"
              stroke="white"
              strokeWidth="1.5"
              fill="none"
              opacity="0.9"
            />
            {/* Inner shield fill */}
            <path
              d="M24 7 L37 12 V22 C37 31 31 37 24 41 C17 37 11 31 11 22 V12 L24 7Z"
              fill="white"
              opacity="0.1"
            />
            {/* AI Brain / Neural network inside shield */}
            <circle cx="24" cy="20" r="2" fill="white" opacity="0.9" />
            <circle cx="18" cy="24" r="1.5" fill="white" opacity="0.7" />
            <circle cx="30" cy="24" r="1.5" fill="white" opacity="0.7" />
            <circle cx="20" cy="30" r="1.5" fill="white" opacity="0.7" />
            <circle cx="28" cy="30" r="1.5" fill="white" opacity="0.7" />
            <circle cx="24" cy="35" r="1.2" fill="white" opacity="0.6" />
            {/* Neural connections */}
            <line x1="24" y1="20" x2="18" y2="24" stroke="white" strokeWidth="0.8" opacity="0.6" />
            <line x1="24" y1="20" x2="30" y2="24" stroke="white" strokeWidth="0.8" opacity="0.6" />
            <line x1="18" y1="24" x2="20" y2="30" stroke="white" strokeWidth="0.8" opacity="0.6" />
            <line x1="30" y1="24" x2="28" y2="30" stroke="white" strokeWidth="0.8" opacity="0.6" />
            <line x1="20" y1="30" x2="24" y2="35" stroke="white" strokeWidth="0.8" opacity="0.5" />
            <line x1="28" y1="30" x2="24" y2="35" stroke="white" strokeWidth="0.8" opacity="0.5" />
            {/* Crossfire scan line */}
            <path d="M14 18 L34 18" stroke="cyan" strokeWidth="0.5" opacity="0.4" strokeDasharray="2 2" />
            <path d="M16 33 L32 33" stroke="cyan" strokeWidth="0.5" opacity="0.3" strokeDasharray="2 2" />
          </svg>

          {/* Corner accents */}
          <div className="absolute top-1 left-1 w-3 h-3 border-t border-l border-cyan-400/40 rounded-tl-lg" />
          <div className="absolute top-1 right-1 w-3 h-3 border-t border-r border-cyan-400/40 rounded-tr-lg" />
          <div className="absolute bottom-1 left-1 w-3 h-3 border-b border-l border-cyan-400/40 rounded-bl-lg" />
          <div className="absolute bottom-1 right-1 w-3 h-3 border-b border-r border-cyan-400/40 rounded-br-lg" />

          {/* Pulse glow */}
          <motion.div
            animate={animate ? { opacity: [0.3, 0.6, 0.3] } : undefined}
            transition={{ duration: 3, repeat: Infinity }}
            className="absolute inset-0 rounded-2xl bg-gradient-to-t from-cyan-500/20 to-transparent"
          />
        </div>

        {/* Outer glow pulse */}
        <motion.div
          animate={animate ? { scale: [1, 1.15, 1], opacity: [0.4, 0, 0.4] } : undefined}
          transition={{ duration: 3, repeat: Infinity }}
          className="absolute inset-0 rounded-2xl border border-indigo-400/30"
        />
      </motion.div>

      {showText && (
        <>
          <motion.h1
            initial={animate ? { opacity: 0, y: 10 } : false}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className={`${textSize} font-bold text-white mt-5 tracking-tight`}
          >
            <span className="bg-gradient-to-r from-white via-blue-100 to-cyan-200 bg-clip-text text-transparent">
              Crime
            </span>
            <span className="bg-gradient-to-r from-cyan-300 to-indigo-300 bg-clip-text text-transparent">
              GPT
            </span>
          </motion.h1>
          {subtitle && (
            <motion.p
              initial={animate ? { opacity: 0 } : false}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className={`${subSize} text-blue-300/60 mt-1.5 font-medium`}
            >
              {subtitle}
            </motion.p>
          )}
        </>
      )}
    </div>
  )
}
