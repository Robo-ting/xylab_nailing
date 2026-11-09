import { useEffect, useRef, useState, useCallback } from 'react'
import type { Point, Roi } from '../lib/types'
import { drawScene, fitTransform, toMm, toPx, drawPolygon, type Scene, type ViewTransform } from '../lib/render'
import { rectPolygon, circlePolygon, distance } from '../lib/geometry'

export type InteractionMode = 'none' | 'roi-rect' | 'roi-circle' | 'roi-poly' | 'add-nail'

interface BoardCanvasProps {
  scene: Scene
  width?: number
  height?: number
  mode?: InteractionMode
  onRoiCreate?: (roi: Roi) => void
  onNailAdd?: (pt: Point) => void
  onNailClick?: (id: string) => void
}

/** 交互式板面画布：渲染场景 + 支持 ROI 框选 / 添加钉位 */
export function BoardCanvas({
  scene,
  width = 720,
  height = 480,
  mode = 'none',
  onRoiCreate,
  onNailAdd,
  onNailClick,
}: BoardCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const overlayRef = useRef<HTMLCanvasElement>(null)
  const [drag, setDrag] = useState<{ start: Point; cur: Point } | null>(null)
  const [polyPts, setPolyPts] = useState<Point[]>([])
  const [hoverMm, setHoverMm] = useState<Point | null>(null)
  const [boardImage, setBoardImage] = useState<HTMLImageElement | null>(null)

  const transform = useRef<ViewTransform>({ scale: 1, offsetX: 0, offsetY: 0 })

  useEffect(() => {
    const url = scene.boardImageUrl
    if (!url) {
      setBoardImage(null)
      return
    }
    const img = new Image()
    img.onload = () => setBoardImage(img)
    img.onerror = () => setBoardImage(null)
    img.src = url
    return () => {
      img.onload = null
      img.onerror = null
    }
  }, [scene.boardImageUrl])

  // 主场景绘制
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const t = fitTransform(scene.boardWidth, scene.boardHeight, width, height)
    transform.current = t
    drawScene(ctx, { ...scene, boardImage }, t)
  }, [scene, width, height, boardImage])

  // 交互 overlay 绘制（拖拽预览 / 多边形预览）
  useEffect(() => {
    const overlay = overlayRef.current
    if (!overlay) return
    const ctx = overlay.getContext('2d')
    if (!ctx) return
    ctx.clearRect(0, 0, width, height)
    const t = transform.current

    if (drag && (mode === 'roi-rect' || mode === 'roi-circle')) {
      const poly =
        mode === 'roi-rect'
          ? rectFromDrag(drag.start, drag.cur)
          : circlePolygon(drag.start, distance(drag.start, drag.cur), 40)
      drawPolygon(ctx, t, poly, {
        fill: 'rgba(56,189,248,0.12)',
        stroke: '#38bdf8',
        lineWidth: 1.5,
        dash: [5, 3],
      })
    }

    if (mode === 'roi-poly' && polyPts.length > 0) {
      ctx.strokeStyle = '#38bdf8'
      ctx.fillStyle = 'rgba(56,189,248,0.12)'
      ctx.lineWidth = 1.5
      ctx.setLineDash([5, 3])
      ctx.beginPath()
      polyPts.forEach((p, i) => {
        const px = toPx(t, p)
        if (i === 0) ctx.moveTo(px.x, px.y)
        else ctx.lineTo(px.x, px.y)
      })
      if (hoverMm) {
        const h = toPx(t, hoverMm)
        ctx.lineTo(h.x, h.y)
      }
      ctx.stroke()
      ctx.setLineDash([])
      polyPts.forEach((p) => {
        const px = toPx(t, p)
        ctx.fillStyle = '#38bdf8'
        ctx.beginPath()
        ctx.arc(px.x, px.y, 3, 0, Math.PI * 2)
        ctx.fill()
      })
    }
  }, [drag, polyPts, hoverMm, mode, width, height])

  const getMm = useCallback((e: React.MouseEvent): Point => {
    const rect = overlayRef.current!.getBoundingClientRect()
    const sx = width / rect.width
    const sy = height / rect.height
    const px = (e.clientX - rect.left) * sx
    const py = (e.clientY - rect.top) * sy
    return toMm(transform.current, px, py)
  }, [width, height])

  const handleDown = (e: React.MouseEvent) => {
    const mm = getMm(e)
    if (mode === 'roi-rect' || mode === 'roi-circle') {
      setDrag({ start: mm, cur: mm })
    } else if (mode === 'roi-poly') {
      setPolyPts((prev) => [...prev, mm])
    } else if (mode === 'add-nail') {
      onNailAdd?.(mm)
    } else if (mode === 'none') {
      // 点击最近钉位
      if (onNailClick) {
        let best: string | null = null
        let bestD = Infinity
        for (const n of scene.designNails) {
          const target = n.final ?? n.design
          const d = distance(target, mm)
          if (d < bestD) {
            bestD = d
            best = n.id
          }
        }
        if (best && bestD < 15) onNailClick(best)
      }
    }
  }

  const handleMove = (e: React.MouseEvent) => {
    const mm = getMm(e)
    setHoverMm(mm)
    if (drag) setDrag({ ...drag, cur: mm })
  }

  const handleUp = () => {
    if (drag && (mode === 'roi-rect' || mode === 'roi-circle')) {
      const poly =
        mode === 'roi-rect'
          ? rectFromDrag(drag.start, drag.cur)
          : circlePolygon(drag.start, distance(drag.start, drag.cur), 40)
      if (polyBigEnough(poly)) {
        onRoiCreate?.({
          id: 'R' + Date.now(),
          shape: mode === 'roi-rect' ? 'rect' : 'circle',
          polygon: poly,
          enabled: true,
          label: mode === 'roi-rect' ? '矩形ROI' : '圆形ROI',
        })
      }
      setDrag(null)
    }
  }

  const finishPoly = () => {
    if (polyPts.length >= 3) {
      onRoiCreate?.({
        id: 'R' + Date.now(),
        shape: 'polygon',
        polygon: polyPts,
        enabled: true,
        label: '多边形ROI',
      })
    }
    setPolyPts([])
  }

  return (
    <div className="canvas-wrap" style={{ width: '100%' }}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{ position: 'absolute', inset: 0 }}
      />
      <canvas
        ref={overlayRef}
        width={width}
        height={height}
        style={{
          position: 'relative',
          cursor: mode === 'none' ? 'default' : 'crosshair',
          width: '100%',
        }}
        onMouseDown={handleDown}
        onMouseMove={handleMove}
        onMouseUp={handleUp}
        onDoubleClick={mode === 'roi-poly' ? finishPoly : undefined}
      />
      {mode === 'roi-poly' && polyPts.length >= 3 && (
        <button
          className="btn btn-primary btn-sm"
          style={{ position: 'absolute', right: 10, top: 10 }}
          onClick={finishPoly}
        >
          完成多边形 ({polyPts.length}点)
        </button>
      )}
      {hoverMm && (mode !== 'none' || scene.coordUnit === 'px') && (
        <div
          style={{
            position: 'absolute',
            left: 10,
            bottom: 10,
            fontSize: 11,
            fontFamily: 'var(--mono)',
            color: 'var(--text-dim)',
            background: 'rgba(0,0,0,0.5)',
            padding: '2px 8px',
            borderRadius: 6,
          }}
        >
          {hoverMm.x.toFixed(0)}, {hoverMm.y.toFixed(0)} {scene.coordUnit === 'px' ? 'px' : 'mm'}
        </div>
      )}
    </div>
  )
}

function rectFromDrag(a: Point, b: Point): Point[] {
  const x = Math.min(a.x, b.x)
  const y = Math.min(a.y, b.y)
  const w = Math.abs(a.x - b.x)
  const h = Math.abs(a.y - b.y)
  return rectPolygon(x, y, w, h)
}

function polyBigEnough(poly: Point[]): boolean {
  const xs = poly.map((p) => p.x)
  const ys = poly.map((p) => p.y)
  return Math.max(...xs) - Math.min(...xs) > 3 && Math.max(...ys) - Math.min(...ys) > 3
}
