import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ChevronLeft, Save, Undo2, Download,
  MousePointer, Circle, Square, Type, ArrowRight, Minus,
  Hash, PenTool, Eye, Zap, Loader2
} from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../../api/client'

type AnnotationTool = 'select' | 'arrow' | 'circle' | 'rectangle' | 'text' | 'measurement' | 'marker' | 'freehand'

interface Annotation {
  id?: number
  annotation_type: string
  canvas_data: any
  label?: string
  evidence_number?: number
}

export default function PhotoAnnotationPage() {
  const { photoId } = useParams()
  const navigate = useNavigate()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const imageRef = useRef<HTMLImageElement | null>(null)

  const [photo, setPhoto] = useState<any>(null)
  const [annotations, setAnnotations] = useState<Annotation[]>([])
  const [currentTool, setCurrentTool] = useState<AnnotationTool>('select')
  const [color, setColor] = useState('#FF0000')
  const [strokeWidth, setStrokeWidth] = useState(2)
  const [isDrawing, setIsDrawing] = useState(false)
  const [drawStart, setDrawStart] = useState<{ x: number; y: number } | null>(null)
  const [currentPoints, setCurrentPoints] = useState<{ x: number; y: number }[]>([])
  const [evidenceCounter, setEvidenceCounter] = useState(1)
  const [undoStack, setUndoStack] = useState<Annotation[][]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [qualityResult, setQualityResult] = useState<any>(null)
  const [assessing, setAssessing] = useState(false)

  useEffect(() => {
    if (!photoId) return
    Promise.all([
      api.get(`/api/forensic-photography/photos/${photoId}`),
      api.get(`/api/forensic-photography/annotations/${photoId}`),
    ]).then(([photoRes, annRes]) => {
      setPhoto(photoRes.data)
      setAnnotations(annRes.data)
    }).catch(() => toast.error('Failed to load photo'))
      .finally(() => setLoading(false))
  }, [photoId])

  useEffect(() => {
    if (!photo) return
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
      imageRef.current = img
      redrawCanvas()
    }
    img.src = `/api/forensic-photography/photos/${photoId}/file`
  }, [photo])

  useEffect(() => {
    redrawCanvas()
  }, [annotations])

  const redrawCanvas = useCallback(() => {
    const canvas = canvasRef.current
    const img = imageRef.current
    if (!canvas || !img) return

    canvas.width = img.naturalWidth
    canvas.height = img.naturalHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.drawImage(img, 0, 0)

    annotations.forEach(ann => {
      const d = ann.canvas_data
      ctx.strokeStyle = d.color || '#FF0000'
      ctx.lineWidth = d.strokeWidth || 2
      ctx.fillStyle = d.color || '#FF0000'

      if (ann.annotation_type === 'arrow') {
        ctx.beginPath()
        ctx.moveTo(d.startX, d.startY)
        ctx.lineTo(d.endX, d.endY)
        ctx.stroke()
        drawArrowhead(ctx, d.startX, d.startY, d.endX, d.endY)
      } else if (ann.annotation_type === 'circle') {
        ctx.beginPath()
        ctx.arc(d.centerX, d.centerY, d.radius, 0, Math.PI * 2)
        ctx.stroke()
      } else if (ann.annotation_type === 'rectangle') {
        ctx.strokeRect(d.x, d.y, d.width, d.height)
      } else if (ann.annotation_type === 'text') {
        ctx.font = `${d.fontSize || 24}px sans-serif`
        ctx.fillText(d.text || '', d.x, d.y)
      } else if (ann.annotation_type === 'measurement') {
        ctx.beginPath()
        ctx.moveTo(d.startX, d.startY)
        ctx.lineTo(d.endX, d.endY)
        ctx.stroke()
        ctx.beginPath()
        ctx.moveTo(d.startX, d.startY - 8)
        ctx.lineTo(d.startX, d.startY + 8)
        ctx.stroke()
        ctx.beginPath()
        ctx.moveTo(d.endX, d.endY - 8)
        ctx.lineTo(d.endX, d.endY + 8)
        ctx.stroke()
        if (d.measurement_text) {
          ctx.font = '16px sans-serif'
          ctx.fillText(d.measurement_text, (d.startX + d.endX) / 2, (d.startY + d.endY) / 2 - 10)
        }
      } else if (ann.annotation_type === 'marker') {
        ctx.beginPath()
        ctx.arc(d.x, d.y, 18, 0, Math.PI * 2)
        ctx.fillStyle = '#FFD700'
        ctx.fill()
        ctx.strokeStyle = '#000'
        ctx.lineWidth = 2
        ctx.stroke()
        ctx.fillStyle = '#000'
        ctx.font = 'bold 14px sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillText(String(ann.evidence_number || 0), d.x, d.y)
        ctx.textAlign = 'start'
        ctx.textBaseline = 'alphabetic'
      } else if (ann.annotation_type === 'freehand') {
        const points = d.points || []
        if (points.length >= 2) {
          ctx.beginPath()
          ctx.moveTo(points[0].x, points[0].y)
          points.slice(1).forEach((p: any) => ctx.lineTo(p.x, p.y))
          ctx.stroke()
        }
      }
    })
  }, [annotations])

  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return { x: 0, y: 0 }
    const rect = canvas.getBoundingClientRect()
    const scaleX = canvas.width / rect.width
    const scaleY = canvas.height / rect.height
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    }
  }

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (currentTool === 'select') return
    const coords = getCanvasCoords(e)
    setIsDrawing(true)
    setDrawStart(coords)

    if (currentTool === 'marker') {
      const newAnn: Annotation = {
        annotation_type: 'marker',
        canvas_data: { x: coords.x, y: coords.y, color },
        evidence_number: evidenceCounter,
      }
      setUndoStack(prev => [...prev, annotations])
      setAnnotations(prev => [...prev, newAnn])
      setEvidenceCounter(prev => prev + 1)
      setIsDrawing(false)
    } else if (currentTool === 'text') {
      const text = prompt('Enter text:')
      if (text) {
        const newAnn: Annotation = {
          annotation_type: 'text',
          canvas_data: { x: coords.x, y: coords.y, text, color, fontSize: 24 },
          label: text,
        }
        setUndoStack(prev => [...prev, annotations])
        setAnnotations(prev => [...prev, newAnn])
      }
      setIsDrawing(false)
    } else if (currentTool === 'freehand') {
      setCurrentPoints([coords])
    }
  }

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !drawStart) return
    if (currentTool === 'freehand') {
      const coords = getCanvasCoords(e)
      setCurrentPoints(prev => [...prev, coords])
    }
  }

  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !drawStart) return
    setIsDrawing(false)
    const end = getCanvasCoords(e)
    let newAnn: Annotation | null = null

    if (currentTool === 'arrow') {
      newAnn = {
        annotation_type: 'arrow',
        canvas_data: { startX: drawStart.x, startY: drawStart.y, endX: end.x, endY: end.y, color, strokeWidth },
      }
    } else if (currentTool === 'circle') {
      const radius = Math.sqrt(Math.pow(end.x - drawStart.x, 2) + Math.pow(end.y - drawStart.y, 2))
      newAnn = {
        annotation_type: 'circle',
        canvas_data: { centerX: drawStart.x, centerY: drawStart.y, radius, color, strokeWidth },
      }
    } else if (currentTool === 'rectangle') {
      newAnn = {
        annotation_type: 'rectangle',
        canvas_data: { x: drawStart.x, y: drawStart.y, width: end.x - drawStart.x, height: end.y - drawStart.y, color, strokeWidth },
      }
    } else if (currentTool === 'measurement') {
      const px = Math.sqrt(Math.pow(end.x - drawStart.x, 2) + Math.pow(end.y - drawStart.y, 2))
      const text = prompt('Enter measurement (e.g., "15 cm"):') || `${Math.round(px)}px`
      newAnn = {
        annotation_type: 'measurement',
        canvas_data: { startX: drawStart.x, startY: drawStart.y, endX: end.x, endY: end.y, measurement_text: text, color, strokeWidth },
      }
    } else if (currentTool === 'freehand' && currentPoints.length >= 2) {
      newAnn = {
        annotation_type: 'freehand',
        canvas_data: { points: currentPoints, color, strokeWidth },
      }
      setCurrentPoints([])
    }

    if (newAnn) {
      setUndoStack(prev => [...prev, annotations])
      setAnnotations(prev => [...prev, newAnn!])
    }
    setDrawStart(null)
  }

  const handleUndo = () => {
    if (undoStack.length === 0) return
    const prev = undoStack[undoStack.length - 1]
    setAnnotations(prev)
    setUndoStack(stack => stack.slice(0, -1))
  }

  const handleSaveAll = async () => {
    if (!photoId) return
    setSaving(true)
    try {
      for (const ann of annotations) {
        if (!ann.id) {
          await api.post(`/api/forensic-photography/annotations/${photoId}`, {
            annotation_type: ann.annotation_type,
            canvas_data: ann.canvas_data,
            label: ann.label,
            evidence_number: ann.evidence_number,
          })
        }
      }
      toast.success('Annotations saved')
    } catch {
      toast.error('Save failed')
    }
    setSaving(false)
  }

  const handleExport = async () => {
    if (!photoId) return
    try {
      await handleSaveAll()
      const res = await api.post(`/api/forensic-photography/annotations/${photoId}/export`)
      toast.success(`Exported as annotated image: ${res.data.photo_id}`)
    } catch {
      toast.error('Export failed')
    }
  }

  const handleAssess = async () => {
    if (!photoId) return
    setAssessing(true)
    try {
      const res = await api.post(`/api/forensic-photography/quality/assess/${photoId}`)
      setQualityResult(res.data)
      toast.success(`Quality: ${Math.round(res.data.quality_score)}%`)
    } catch {
      toast.error('Assessment failed')
    }
    setAssessing(false)
  }

  const tools: { key: AnnotationTool; icon: any; label: string }[] = [
    { key: 'select', icon: MousePointer, label: 'Select' },
    { key: 'arrow', icon: ArrowRight, label: 'Arrow' },
    { key: 'circle', icon: Circle, label: 'Circle' },
    { key: 'rectangle', icon: Square, label: 'Rectangle' },
    { key: 'text', icon: Type, label: 'Text' },
    { key: 'measurement', icon: Minus, label: 'Measure' },
    { key: 'marker', icon: Hash, label: 'Marker' },
    { key: 'freehand', icon: PenTool, label: 'Freehand' },
  ]

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-96">
        <div className="w-8 h-8 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)] lg:h-[calc(100vh-4rem)]">
      {/* Top Bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-dark-700/50 bg-dark-800/50 flex-shrink-0">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="p-1.5 rounded-lg hover:bg-dark-700/50">
            <ChevronLeft className="w-5 h-5 text-dark-400" />
          </button>
          <span className="text-sm text-white font-medium truncate max-w-[200px]">
            {photo?.original_filename}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleAssess} disabled={assessing} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-xs text-purple-300 hover:bg-purple-500/20">
            {assessing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Eye className="w-3 h-3" />} Assess
          </button>
          <button onClick={handleUndo} disabled={undoStack.length === 0} className="p-1.5 rounded-lg hover:bg-dark-700/50 disabled:opacity-30">
            <Undo2 className="w-4 h-4 text-dark-400" />
          </button>
          <button onClick={handleSaveAll} disabled={saving} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-500/10 border border-green-500/20 text-xs text-green-300 hover:bg-green-500/20">
            {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />} Save
          </button>
          <button onClick={handleExport} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300 hover:bg-blue-500/20">
            <Download className="w-3 h-3" /> Export
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Toolbar */}
        <div className="w-14 bg-dark-800/80 border-r border-dark-700/50 flex flex-col items-center py-3 gap-1 flex-shrink-0">
          {tools.map(t => (
            <button
              key={t.key}
              onClick={() => setCurrentTool(t.key)}
              title={t.label}
              className={`p-2 rounded-lg transition-colors ${
                currentTool === t.key ? 'bg-purple-600 text-white' : 'text-dark-400 hover:bg-dark-700/50 hover:text-white'
              }`}
            >
              <t.icon className="w-4 h-4" />
            </button>
          ))}
          <div className="border-t border-dark-700/50 w-8 my-2" />
          <input
            type="color"
            value={color}
            onChange={e => setColor(e.target.value)}
            className="w-7 h-7 rounded cursor-pointer border-none bg-transparent"
            title="Color"
          />
          <select
            value={strokeWidth}
            onChange={e => setStrokeWidth(Number(e.target.value))}
            className="w-10 text-[10px] bg-dark-700 text-white rounded px-1 py-0.5 mt-1"
          >
            <option value={1}>1px</option>
            <option value={2}>2px</option>
            <option value={3}>3px</option>
            <option value={5}>5px</option>
          </select>
        </div>

        {/* Canvas Area */}
        <div className="flex-1 overflow-auto bg-dark-900/50 p-4 flex items-center justify-center">
          <canvas
            ref={canvasRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            className="max-w-full max-h-full object-contain rounded-lg shadow-2xl cursor-crosshair"
            style={{ imageRendering: 'auto' }}
          />
        </div>

        {/* Quality Panel */}
        {qualityResult && (
          <div className="w-64 bg-dark-800/80 border-l border-dark-700/50 p-4 overflow-y-auto flex-shrink-0">
            <h4 className="text-xs font-bold text-white mb-3">Quality Assessment</h4>
            <div className="space-y-3">
              <div className="p-3 rounded-xl bg-dark-700/50">
                <p className="text-[10px] text-dark-400">Quality Score</p>
                <p className={`text-lg font-bold ${qualityResult.quality_score >= 70 ? 'text-green-400' : qualityResult.quality_score >= 40 ? 'text-amber-400' : 'text-red-400'}`}>
                  {Math.round(qualityResult.quality_score)}%
                </p>
              </div>
              <div className="p-3 rounded-xl bg-dark-700/50">
                <p className="text-[10px] text-dark-400">Court Readiness</p>
                <p className={`text-lg font-bold ${qualityResult.courtroom_readiness >= 70 ? 'text-green-400' : 'text-amber-400'}`}>
                  {Math.round(qualityResult.courtroom_readiness)}%
                </p>
              </div>
              {qualityResult.suggestions?.length > 0 && (
                <div>
                  <p className="text-[10px] text-dark-400 mb-1.5">Suggestions</p>
                  <ul className="space-y-1.5">
                    {qualityResult.suggestions.map((s: string, i: number) => (
                      <li key={i} className="text-[10px] text-dark-300 flex items-start gap-1.5">
                        <Zap className="w-2.5 h-2.5 text-amber-400 mt-0.5 flex-shrink-0" />
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function drawArrowhead(ctx: CanvasRenderingContext2D, x1: number, y1: number, x2: number, y2: number) {
  const angle = Math.atan2(y2 - y1, x2 - x1)
  const len = 15
  const a = Math.PI / 6
  ctx.beginPath()
  ctx.moveTo(x2, y2)
  ctx.lineTo(x2 - len * Math.cos(angle - a), y2 - len * Math.sin(angle - a))
  ctx.lineTo(x2 - len * Math.cos(angle + a), y2 - len * Math.sin(angle + a))
  ctx.closePath()
  ctx.fill()
}
