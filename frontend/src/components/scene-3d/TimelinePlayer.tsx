import { Play, Pause, SkipBack, SkipForward, Clock } from 'lucide-react'

interface TimelineEvent {
  time: string
  description: string
  camera_position: number[]
  camera_target: number[]
  highlight_objects: string[]
  duration: number
}

interface Props {
  events: TimelineEvent[]
  currentIndex: number
  isPlaying: boolean
  onPlay: () => void
  onPause: () => void
  onSeek: (index: number) => void
  onNext: () => void
  onPrev: () => void
}

export default function TimelinePlayer({ events, currentIndex, isPlaying, onPlay, onPause, onSeek, onNext, onPrev }: Props) {
  const currentEvent = events[currentIndex] || null

  return (
    <div className="bg-gray-900 border-t border-gray-700 px-4 py-3">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <button
            onClick={onPrev}
            disabled={currentIndex === 0}
            className="p-1.5 rounded hover:bg-gray-700 disabled:opacity-30 transition-colors"
          >
            <SkipBack size={16} className="text-gray-300" />
          </button>

          <button
            onClick={isPlaying ? onPause : onPlay}
            className="p-2 rounded-full bg-purple-600 hover:bg-purple-500 transition-colors"
          >
            {isPlaying ? <Pause size={18} className="text-white" /> : <Play size={18} className="text-white" />}
          </button>

          <button
            onClick={onNext}
            disabled={currentIndex >= events.length - 1}
            className="p-1.5 rounded hover:bg-gray-700 disabled:opacity-30 transition-colors"
          >
            <SkipForward size={16} className="text-gray-300" />
          </button>
        </div>

        <div className="flex-1 relative">
          <input
            type="range"
            min={0}
            max={Math.max(events.length - 1, 0)}
            value={currentIndex}
            onChange={(e) => onSeek(parseInt(e.target.value))}
            className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
          />
          <div className="flex justify-between mt-1">
            {events.map((evt, i) => (
              <div
                key={i}
                className={`w-2 h-2 rounded-full cursor-pointer ${i === currentIndex ? 'bg-purple-400' : 'bg-gray-600'}`}
                onClick={() => onSeek(i)}
                title={`${evt.time} - ${evt.description}`}
              />
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2 min-w-[250px]">
          <Clock size={14} className="text-gray-400" />
          {currentEvent ? (
            <div className="text-xs">
              <span className="text-purple-400 font-mono">{currentEvent.time}</span>
              <span className="text-gray-400 ml-2 truncate max-w-[180px] inline-block">
                {currentEvent.description}
              </span>
            </div>
          ) : (
            <span className="text-xs text-gray-500">No events</span>
          )}
        </div>
      </div>
    </div>
  )
}
