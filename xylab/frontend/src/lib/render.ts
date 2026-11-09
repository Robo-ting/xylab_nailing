// ==========================================================================
// Canvas 渲染引擎：把板面场景（板件/缺陷/ROI/禁区栅格/钉位）绘制到 2D 画布
// 采用物理坐标(mm) -> 画布像素 的统一映射
// ==========================================================================
import type { Board, Defect, DesignNail, Grid, Point, Roi } from './types'
import { DEFECT_META } from '../mock/defects'

export interface ViewTransform {
  scale: number // display px per logical unit (mm 演示链路，或原图 px)
  offsetX: number
  offsetY: number
}

export interface SceneLayers {
  boardOutline: boolean
  boards: boolean
  defects: boolean
  masks: boolean
  rois: boolean
  forbiddenOriginal: boolean
  forbiddenDilated: boolean
  costMap: boolean
  designNails: boolean
  finalNails: boolean
  grid: boolean
}

export const DEFAULT_LAYERS: SceneLayers = {
  boardOutline: true,
  boards: false,
  defects: true,
  masks: true,
  rois: true,
  forbiddenOriginal: false,
  forbiddenDilated: false,
  costMap: false,
  designNails: true,
  finalNails: false,
  grid: false,
}

export interface Scene {
  boardWidth: number
  boardHeight: number
  defects: Defect[]
  rois: Roi[]
  boards: Board[]
  designNails: DesignNail[]
  grid?: Grid | null
  dilationClass?: Uint8Array | null
  layers: SceneLayers
  enabledTypes?: Set<string>
  confFilter?: number
  /** 高亮的钉位 id */
  highlightNail?: string
  /** 底板照片（原图像素与 boardWidth/Height 一致）。未设置时画程序木纹。 */
  boardImage?: CanvasImageSource | null
  boardImageUrl?: string
  /** 原图像素禁区 [x,y,w,h]，由 API client 转换后传入 */
  mvpForbidden?: { x: number; y: number; w: number; h: number }[]
  /** 逻辑坐标单位：演示链路为 mm，图片 MVP 为原图 px */
  coordUnit?: 'mm' | 'px'
}

/** 计算适配画布的视图变换（留边距）。逻辑单位由调用方决定（mm 或原图 px）。display = offset + logical * scale */
export function fitTransform(
  boardWidth: number,
  boardHeight: number,
  canvasWidth: number,
  canvasHeight: number,
  pad = 30,
): ViewTransform {
  const sx = (canvasWidth - pad * 2) / boardWidth
  const sy = (canvasHeight - pad * 2) / boardHeight
  const scale = Math.min(sx, sy)
  const offsetX = (canvasWidth - boardWidth * scale) / 2
  const offsetY = (canvasHeight - boardHeight * scale) / 2
  return { scale, offsetX, offsetY }
}

export function toPx(t: ViewTransform, p: Point): Point {
  return { x: t.offsetX + p.x * t.scale, y: t.offsetY + p.y * t.scale }
}

export function toMm(t: ViewTransform, px: number, py: number): Point {
  return { x: (px - t.offsetX) / t.scale, y: (py - t.offsetY) / t.scale }
}

/** 主绘制函数 */
export function drawScene(ctx: CanvasRenderingContext2D, scene: Scene, t: ViewTransform): void {
  const { boardWidth, boardHeight, layers } = scene
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height)

  // 背景：照片 contain+居中（同一 fitTransform），或程序木纹
  if (layers.boardOutline) {
    const o = toPx(t, { x: 0, y: 0 })
    const dw = boardWidth * t.scale
    const dh = boardHeight * t.scale
    if (scene.boardImage) {
      ctx.drawImage(scene.boardImage, o.x, o.y, dw, dh)
    } else {
      ctx.fillStyle = '#1a130c'
      ctx.fillRect(o.x, o.y, dw, dh)
      drawWoodGrain(ctx, t, boardWidth, boardHeight)
    }
    ctx.strokeStyle = '#5a4632'
    ctx.lineWidth = 2
    ctx.strokeRect(o.x, o.y, dw, dh)
  }

  // 禁区/代价栅格
  if (scene.grid && (layers.forbiddenDilated || layers.forbiddenOriginal || layers.costMap)) {
    drawGridLayer(ctx, scene, t)
  }

  // 图片 MVP 禁区矩形（原图 px -> display px）
  if (scene.mvpForbidden && scene.mvpForbidden.length > 0) {
    for (const r of scene.mvpForbidden) {
      const p0 = toPx(t, { x: r.x, y: r.y })
      ctx.fillStyle = 'rgba(239,68,68,0.18)'
      ctx.strokeStyle = 'rgba(239,68,68,0.7)'
      ctx.lineWidth = 1
      ctx.setLineDash([])
      ctx.fillRect(p0.x, p0.y, r.w * t.scale, r.h * t.scale)
      ctx.strokeRect(p0.x, p0.y, r.w * t.scale, r.h * t.scale)
    }
  }

  // 装配板件
  if (layers.boards) {
    for (const b of scene.boards) {
      drawPolygon(ctx, t, b.polygon, {
        fill: hexA(b.color ?? '#a97142', b.role === 'base' ? 0.15 : 0.3),
        stroke: b.color ?? '#a97142',
        lineWidth: 1.5,
        dash: b.role === 'vertical' ? [] : [6, 4],
      })
      const c = polyCentroidPx(ctx, t, b.polygon)
      ctx.fillStyle = '#e6edf7'
      ctx.font = '11px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(b.boardId, c.x, c.y)
    }
  }

  // ROI
  if (layers.rois) {
    for (const r of scene.rois) {
      drawPolygon(ctx, t, r.polygon, {
        fill: r.enabled ? 'rgba(56,189,248,0.10)' : 'rgba(107,126,163,0.06)',
        stroke: r.enabled ? '#38bdf8' : '#6b7ea3',
        lineWidth: 1.5,
        dash: [5, 3],
      })
    }
  }

  // 缺陷
  if (layers.defects) {
    for (const d of scene.defects) {
      if (scene.enabledTypes && !scene.enabledTypes.has(d.type)) continue
      if (scene.confFilter !== undefined && d.confidence < scene.confFilter) continue
      const meta = DEFECT_META[d.type]
      if (layers.masks) {
        drawPolygon(ctx, t, d.polygon, {
          fill: hexA(meta.color, 0.28),
          stroke: meta.color,
          lineWidth: 1,
          dash: [4, 2],
        })
      }
      // bbox
      const bb = d.bbox
      const p0 = toPx(t, { x: bb[0], y: bb[1] })
      ctx.strokeStyle = meta.color
      ctx.lineWidth = 1.2
      ctx.setLineDash([])
      ctx.strokeRect(p0.x, p0.y, bb[2] * t.scale, bb[3] * t.scale)
      // 标签
      ctx.fillStyle = meta.color
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText(`${meta.label} ${(d.confidence * 100) | 0}%`, p0.x, p0.y - 3)
    }
  }

  // 设计钉位
  if (layers.designNails) {
    for (const n of scene.designNails) {
      const p = toPx(t, n.design)
      ctx.strokeStyle = '#93c5fd'
      ctx.lineWidth = 1.5
      ctx.setLineDash([])
      drawCross(ctx, p.x, p.y, 5)
    }
  }

  // 最终钉位（决策后）
  if (layers.finalNails) {
    for (const n of scene.designNails) {
      if (!n.final || !n.action) continue
      const pf = toPx(t, n.final)
      const pd = toPx(t, n.design)
      // 偏移连线
      if (n.status === 'relocated') {
        ctx.strokeStyle = 'rgba(245,158,11,0.7)'
        ctx.lineWidth = 1
        ctx.setLineDash([3, 3])
        ctx.beginPath()
        ctx.moveTo(pd.x, pd.y)
        ctx.lineTo(pf.x, pf.y)
        ctx.stroke()
      }
      const color =
        n.action === 'SKIP'
          ? '#ef4444'
          : n.action === 'RELOCATE'
          ? '#f59e0b'
          : n.action === 'PREDRILL_THEN_NAIL'
          ? '#8b5cf6'
          : '#22c55e'
      ctx.setLineDash([])
      if (n.action === 'SKIP') {
        ctx.strokeStyle = color
        ctx.lineWidth = 2
        drawX(ctx, pf.x, pf.y, 5)
      } else {
        ctx.fillStyle = color
        ctx.beginPath()
        ctx.arc(pf.x, pf.y, n.id === scene.highlightNail ? 6 : 4, 0, Math.PI * 2)
        ctx.fill()
        if (n.action === 'PREDRILL_THEN_NAIL') {
          ctx.strokeStyle = '#fff'
          ctx.lineWidth = 1
          ctx.beginPath()
          ctx.arc(pf.x, pf.y, 7, 0, Math.PI * 2)
          ctx.stroke()
        }
      }
      if (n.id === scene.highlightNail) {
        ctx.strokeStyle = '#fff'
        ctx.lineWidth = 1.5
        ctx.beginPath()
        ctx.arc(pf.x, pf.y, 10, 0, Math.PI * 2)
        ctx.stroke()
      }
    }
  }
}

function drawGridLayer(ctx: CanvasRenderingContext2D, scene: Scene, t: ViewTransform): void {
  const grid = scene.grid!
  const cs = grid.cellSize * t.scale
  for (let row = 0; row < grid.rows; row++) {
    for (let col = 0; col < grid.cols; col++) {
      const i = row * grid.cols + col
      const px = t.offsetX + (grid.origin.x + col * grid.cellSize) * t.scale
      const py = t.offsetY + (grid.origin.y + row * grid.cellSize) * t.scale
      // 代价图
      if (scene.layers.costMap && grid.cost[i] > 0.02) {
        const c = grid.cost[i]
        ctx.fillStyle = `rgba(239,68,68,${Math.min(0.6, c * 0.6)})`
        ctx.fillRect(px, py, cs + 0.5, cs + 0.5)
      }
      // 禁区
      const cls = scene.dilationClass ? scene.dilationClass[i] : grid.forbidden[i] ? 2 : 0
      if (cls === 2 && scene.layers.forbiddenOriginal) {
        ctx.fillStyle = 'rgba(239,68,68,0.55)'
        ctx.fillRect(px, py, cs + 0.5, cs + 0.5)
      } else if (cls === 1 && scene.layers.forbiddenDilated) {
        ctx.fillStyle = 'rgba(245,158,11,0.35)'
        ctx.fillRect(px, py, cs + 0.5, cs + 0.5)
      } else if (cls === 2 && scene.layers.forbiddenDilated && !scene.layers.forbiddenOriginal) {
        ctx.fillStyle = 'rgba(239,68,68,0.5)'
        ctx.fillRect(px, py, cs + 0.5, cs + 0.5)
      }
    }
  }
}

function drawWoodGrain(ctx: CanvasRenderingContext2D, t: ViewTransform, w: number, h: number): void {
  ctx.save()
  ctx.globalAlpha = 0.5
  ctx.strokeStyle = '#3a2b1c'
  ctx.lineWidth = 1
  const o = toPx(t, { x: 0, y: 0 })
  for (let y = 15; y < h; y += 22) {
    ctx.beginPath()
    for (let x = 0; x <= w; x += 10) {
      const yy = y + Math.sin((x / w) * Math.PI * 3 + y) * 4
      const p = toPx(t, { x, y: yy })
      if (x === 0) ctx.moveTo(p.x, p.y)
      else ctx.lineTo(p.x, p.y)
    }
    ctx.stroke()
  }
  ctx.restore()
  void o
}

interface PolyStyle {
  fill?: string
  stroke?: string
  lineWidth?: number
  dash?: number[]
}

export function drawPolygon(
  ctx: CanvasRenderingContext2D,
  t: ViewTransform,
  poly: Point[],
  style: PolyStyle,
): void {
  if (poly.length < 2) return
  ctx.beginPath()
  poly.forEach((p, i) => {
    const px = toPx(t, p)
    if (i === 0) ctx.moveTo(px.x, px.y)
    else ctx.lineTo(px.x, px.y)
  })
  ctx.closePath()
  if (style.fill) {
    ctx.fillStyle = style.fill
    ctx.fill()
  }
  if (style.stroke) {
    ctx.strokeStyle = style.stroke
    ctx.lineWidth = style.lineWidth ?? 1
    ctx.setLineDash(style.dash ?? [])
    ctx.stroke()
    ctx.setLineDash([])
  }
}

function drawCross(ctx: CanvasRenderingContext2D, x: number, y: number, r: number): void {
  ctx.beginPath()
  ctx.moveTo(x - r, y)
  ctx.lineTo(x + r, y)
  ctx.moveTo(x, y - r)
  ctx.lineTo(x, y + r)
  ctx.stroke()
}

function drawX(ctx: CanvasRenderingContext2D, x: number, y: number, r: number): void {
  ctx.beginPath()
  ctx.moveTo(x - r, y - r)
  ctx.lineTo(x + r, y + r)
  ctx.moveTo(x + r, y - r)
  ctx.lineTo(x - r, y + r)
  ctx.stroke()
}

function hexA(hex: string, a: number): string {
  const h = hex.replace('#', '')
  const r = parseInt(h.substring(0, 2), 16)
  const g = parseInt(h.substring(2, 4), 16)
  const b = parseInt(h.substring(4, 6), 16)
  return `rgba(${r},${g},${b},${a})`
}

function polyCentroidPx(ctx: CanvasRenderingContext2D, t: ViewTransform, poly: Point[]): Point {
  let x = 0
  let y = 0
  for (const p of poly) {
    x += p.x
    y += p.y
  }
  return toPx(t, { x: x / poly.length, y: y / poly.length })
}
