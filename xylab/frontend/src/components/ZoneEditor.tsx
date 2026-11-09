import { useEffect, useRef, useState, type MouseEvent } from 'react'
import { deleteZone, fetchSnapshot, fetchZone, pauseSource, resumeSource, saveZone } from '../api/client'
import { circlePolygon, rectPolygon } from '../lib/geometry'

type Pt = { x: number; y: number }
type Shape = 'rect' | 'circle' | 'polygon'

const SHAPES: { id: Shape; label: string }[] = [
  { id: 'rect', label: '矩形' },
  { id: 'circle', label: '圆形' },
  { id: 'polygon', label: '多边形' },
]

interface ZoneEditorProps {
  sourceId: string
  open: boolean
  onClose: () => void
  onChanged: () => void
}

/** 停在当前帧上画选区。矩形、圆形都会转成多边形再保存。 */
export function ZoneEditor({ sourceId, open, onClose, onChanged }: ZoneEditorProps) {
  const wrapRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const viewRef = useRef({ scale: 1, ox: 0, oy: 0 })
  const [frameUrl, setFrameUrl] = useState<string | null>(null)
  const [frameW, setFrameW] = useState(1)
  const [frameH, setFrameH] = useState(1)
  const [shape, setShape] = useState<Shape>('rect')
  const [points, setPoints] = useState<Pt[]>([])
  const [closed, setClosed] = useState(false)
  const [drag, setDrag] = useState<{ start: Pt; cur: Pt } | null>(null)
  const [hint, setHint] = useState('按住拖出矩形')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!open) return
    let cancelled = false
    let url: string | null = null
    setPoints([])
    setClosed(false)
    setDrag(null)
    setShape('rect')
    setError(null)
    setHint('按住拖出矩形')
    void (async () => {
      try {
        await pauseSource(sourceId)
        const snap = await fetchSnapshot(sourceId)
        url = snap.url
        if (cancelled) {
          URL.revokeObjectURL(snap.url)
          return
        }
        setFrameUrl(snap.url)
        setFrameW(snap.width || 1)
        setFrameH(snap.height || 1)
        const zone = await fetchZone(sourceId)
        if (cancelled || !zone || zone.length < 3) return
        setPoints(zone)
        setClosed(true)
        const loaded = inferShape(zone)
        setShape(loaded)
        setHint(loaded === 'polygon' ? '已载入多边形 · 左键加点，点回起点闭合，右键撤销' : '已载入选区 · 点「多边形」可逐点改')
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err))
      }
    })()
    return () => {
      cancelled = true
      if (url) URL.revokeObjectURL(url)
    }
  }, [open, sourceId])

  const outline = drag ? shapePoints(shape, drag.start, drag.cur) : points

  useEffect(() => {
    if (!open) return
    const wrap = wrapRef.current
    if (!wrap) return
    const draw = () => {
      const canvas = canvasRef.current
      if (!canvas) return
      const wrapW = Math.max(1, wrap.clientWidth)
      const wrapH = Math.max(1, wrap.clientHeight)
      canvas.width = wrapW
      canvas.height = wrapH
      const scale = Math.min(wrapW / frameW, wrapH / frameH)
      const renderW = frameW * scale
      const renderH = frameH * scale
      const ox = (wrapW - renderW) / 2
      const oy = (wrapH - renderH) / 2
      viewRef.current = { scale, ox, oy }
      const img = wrap.querySelector('img')
      if (img) {
        img.style.left = `${ox}px`
        img.style.top = `${oy}px`
        img.style.width = `${renderW}px`
        img.style.height = `${renderH}px`
      }
      const ctx = canvas.getContext('2d')
      if (!ctx || outline.length === 0) return
      const screen = outline.map((p) => ({ x: ox + p.x * scale, y: oy + p.y * scale }))
      const seal = closed || shape !== 'polygon' || outline.length >= 3
      if (outline.length >= 3 && seal) {
        ctx.beginPath()
        ctx.moveTo(screen[0].x, screen[0].y)
        screen.slice(1).forEach((p) => ctx.lineTo(p.x, p.y))
        ctx.closePath()
        ctx.fillStyle = 'rgba(56,139,253,0.18)'
        ctx.fill()
      }
      ctx.beginPath()
      ctx.moveTo(screen[0].x, screen[0].y)
      screen.slice(1).forEach((p) => ctx.lineTo(p.x, p.y))
      if (closed || shape !== 'polygon') ctx.closePath()
      ctx.strokeStyle = '#388bfd'
      ctx.lineWidth = 2
      ctx.setLineDash(closed || shape !== 'polygon' ? [] : [6, 3])
      ctx.stroke()
      ctx.setLineDash([])
      if (shape === 'polygon') {
        screen.forEach((p, i) => {
          ctx.beginPath()
          ctx.arc(p.x, p.y, i === 0 ? 7 : 5, 0, Math.PI * 2)
          ctx.fillStyle = i === 0 ? '#388bfd' : '#e6edf3'
          ctx.strokeStyle = '#388bfd'
          ctx.lineWidth = 2
          ctx.fill()
          ctx.stroke()
        })
      }
    }
    draw()
    const observer = new ResizeObserver(draw)
    observer.observe(wrap)
    return () => observer.disconnect()
  }, [open, frameW, frameH, outline, closed, shape, frameUrl])

  function canvasPoint(event: MouseEvent<HTMLCanvasElement>): Pt | null {
    const canvas = canvasRef.current
    if (!canvas) return null
    const rect = canvas.getBoundingClientRect()
    const x = (event.clientX - rect.left) * (canvas.width / rect.width)
    const y = (event.clientY - rect.top) * (canvas.height / rect.height)
    const { scale, ox, oy } = viewRef.current
    const inside = x >= ox && y >= oy && x <= ox + frameW * scale && y <= oy + frameH * scale
    if (!inside || scale <= 0) return null
    return {
      x: Math.max(0, Math.min(frameW, (x - ox) / scale)),
      y: Math.max(0, Math.min(frameH, (y - oy) / scale)),
    }
  }

  function pickShape(next: Shape) {
    setDrag(null)
    setShape(next)
    if (next === 'polygon') {
      setClosed(points.length >= 3)
      setHint(points.length >= 3 ? '多边形：左键继续加点，点回起点闭合，右键撤销' : '左键加点 · 点回起点闭合 · 右键撤销')
      return
    }
    setHint(next === 'rect' ? '按住拖出矩形，松手后替换当前选区' : '按住从圆心拖出半径，松手后替换当前选区')
  }

  function addPolygonPoint(pt: Pt) {
    if (points.length >= 3) {
      const dx = pt.x - points[0].x
      const dy = pt.y - points[0].y
      const { scale } = viewRef.current
      if (Math.hypot(dx, dy) < 18 / Math.max(scale, 0.0001)) {
        setClosed(true)
        setHint('多边形已闭合 · 保存后后续画面都用这块选区')
        return
      }
    }
    const next = [...points, pt]
    setPoints(next)
    setClosed(false)
    setHint(`${next.length} 个顶点 · 点回起点闭合 · 右键撤销`)
  }

  function onDown(event: MouseEvent<HTMLCanvasElement>) {
    if (event.button !== 0) return
    const pt = canvasPoint(event)
    if (!pt) return
    if (shape === 'polygon') {
      addPolygonPoint(pt)
      return
    }
    setDrag({ start: pt, cur: pt })
  }

  function onMove(event: MouseEvent<HTMLCanvasElement>) {
    if (!drag || shape === 'polygon') return
    const pt = canvasPoint(event)
    if (!pt) return
    setDrag({ start: drag.start, cur: pt })
  }

  function onUp() {
    if (!drag || shape === 'polygon') return
    const next = shapePoints(shape, drag.start, drag.cur)
    setDrag(null)
    if (!bigEnough(next)) {
      setHint(shape === 'rect' ? '矩形太小，重新拖一次' : '圆太小，重新拖一次')
      return
    }
    setPoints(next)
    setClosed(true)
    setHint(shape === 'rect' ? '矩形已就绪 · 保存后后续画面都用这块选区' : '圆形已就绪 · 保存后后续画面都用这块选区')
  }

  function undo() {
    if (shape !== 'polygon') {
      setPoints([])
      setClosed(false)
      setDrag(null)
      return
    }
    setPoints((prev) => prev.slice(0, -1))
    setClosed(false)
  }

  async function finish(kind: 'save' | 'delete') {
    setBusy(true)
    setError(null)
    try {
      if (kind === 'save') {
        if (points.length < 3) {
          setError('先画出选区')
          return
        }
        await saveZone(sourceId, points, frameW, frameH)
      } else {
        await deleteZone(sourceId)
      }
      await resumeSource(sourceId)
      onChanged()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  async function cancel() {
    try {
      await resumeSource(sourceId)
    } catch {
      /* 图片输入没有在播的视频 */
    }
    onClose()
  }

  if (!open) return null

  return (
    <div className="zone-modal">
      <div className="zone-topbar">
        <div className="zone-topbar-title">
          <strong>选区</strong>
          <span className="zone-shapes" role="group" aria-label="选区形状">
            {SHAPES.map((item) => (
              <button
                key={item.id}
                type="button"
                className={'toolbar-btn' + (shape === item.id ? ' active' : '')}
                onClick={() => pickShape(item.id)}
              >
                {item.label}
              </button>
            ))}
          </span>
          <span className="zone-hint">{hint}</span>
        </div>
        <div className="zone-actions">
          <button className="btn btn-sm" onClick={() => { setPoints([]); setClosed(false); setDrag(null) }} type="button">清空</button>
          <button className="btn btn-sm btn-danger" onClick={() => void finish('delete')} disabled={busy} type="button">删除选区</button>
          <button className="btn btn-sm btn-primary" onClick={() => void finish('save')} disabled={busy} type="button">
            {busy ? '保存中…' : '保存选区'}
          </button>
          <button className="btn btn-sm" onClick={() => void cancel()} type="button">取消</button>
        </div>
      </div>
      {error && <div className="badge badge-red zone-error">{error}</div>}
      <div className="zone-canvas-wrap" ref={wrapRef}>
        {frameUrl && <img className="zone-frozen-img" src={frameUrl} alt="停帧" />}
        <canvas
          ref={canvasRef}
          className="zone-canvas"
          onMouseDown={onDown}
          onMouseMove={onMove}
          onMouseUp={onUp}
          onContextMenu={(event) => {
            event.preventDefault()
            undo()
          }}
        />
      </div>
    </div>
  )
}

function inferShape(zone: Pt[]): Shape {
  if (zone.length === 4 && isAxisAlignedRect(zone)) return 'rect'
  if (zone.length >= 24 && isRoughCircle(zone)) return 'circle'
  return 'polygon'
}

function isAxisAlignedRect(zone: Pt[]): boolean {
  const xs = zone.map((p) => p.x)
  const ys = zone.map((p) => p.y)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  return zone.every((p) => Math.min(Math.abs(p.x - minX), Math.abs(p.x - maxX)) < 2 && Math.min(Math.abs(p.y - minY), Math.abs(p.y - maxY)) < 2)
}

function isRoughCircle(zone: Pt[]): boolean {
  const cx = zone.reduce((s, p) => s + p.x, 0) / zone.length
  const cy = zone.reduce((s, p) => s + p.y, 0) / zone.length
  const radii = zone.map((p) => Math.hypot(p.x - cx, p.y - cy))
  const mean = radii.reduce((s, r) => s + r, 0) / radii.length
  if (mean < 8) return false
  const variance = radii.reduce((s, r) => s + (r - mean) ** 2, 0) / radii.length
  return Math.sqrt(variance) / mean < 0.08
}

function shapePoints(shape: Shape, start: Pt, cur: Pt): Pt[] {
  if (shape === 'circle') {
    const radius = Math.hypot(cur.x - start.x, cur.y - start.y)
    if (radius < 1) return []
    return circlePolygon(start, radius, 48)
  }
  const x = Math.min(start.x, cur.x)
  const y = Math.min(start.y, cur.y)
  const w = Math.abs(cur.x - start.x)
  const h = Math.abs(cur.y - start.y)
  if (w < 1 || h < 1) return []
  return rectPolygon(x, y, w, h)
}

function bigEnough(poly: Pt[]): boolean {
  if (poly.length < 3) return false
  const xs = poly.map((p) => p.x)
  const ys = poly.map((p) => p.y)
  return Math.max(...xs) - Math.min(...xs) > 8 && Math.max(...ys) - Math.min(...ys) > 8
}
