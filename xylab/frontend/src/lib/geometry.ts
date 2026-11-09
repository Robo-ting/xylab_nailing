// ==========================================================================
// 几何算法：射线法点在多边形内判定、多边形面积、求交、腐蚀、包围盒
// 用于 ROI 过滤、装配重合区计算、缺陷掩码处理
// ==========================================================================
import type { Point } from './types'

/** 射线法（Ray Casting）判断点是否在多边形内部：奇数次穿越=内部 */
export function pointInPolygon(pt: Point, polygon: Point[]): boolean {
  let inside = false
  const n = polygon.length
  for (let i = 0, j = n - 1; i < n; j = i++) {
    const xi = polygon[i].x
    const yi = polygon[i].y
    const xj = polygon[j].x
    const yj = polygon[j].y
    const intersect =
      yi > pt.y !== yj > pt.y &&
      pt.x < ((xj - xi) * (pt.y - yi)) / (yj - yi) + xi
    if (intersect) inside = !inside
  }
  return inside
}

/** 多边形有向面积（Shoelace），正值表示逆时针 */
export function signedArea(polygon: Point[]): number {
  let area = 0
  const n = polygon.length
  for (let i = 0; i < n; i++) {
    const a = polygon[i]
    const b = polygon[(i + 1) % n]
    area += a.x * b.y - b.x * a.y
  }
  return area / 2
}

/** 多边形绝对面积 */
export function polygonArea(polygon: Point[]): number {
  return Math.abs(signedArea(polygon))
}

/** 多边形质心 */
export function centroid(polygon: Point[]): Point {
  let cx = 0
  let cy = 0
  let a = 0
  const n = polygon.length
  for (let i = 0; i < n; i++) {
    const p0 = polygon[i]
    const p1 = polygon[(i + 1) % n]
    const cross = p0.x * p1.y - p1.x * p0.y
    a += cross
    cx += (p0.x + p1.x) * cross
    cy += (p0.y + p1.y) * cross
  }
  a *= 0.5
  if (Math.abs(a) < 1e-9) {
    // 退化多边形取顶点平均
    const s = polygon.reduce((acc, p) => ({ x: acc.x + p.x, y: acc.y + p.y }), { x: 0, y: 0 })
    return { x: s.x / n, y: s.y / n }
  }
  return { x: cx / (6 * a), y: cy / (6 * a) }
}

/** 轴对齐包围盒 */
export function boundingBox(polygon: Point[]): { min: Point; max: Point } {
  const min = { x: Infinity, y: Infinity }
  const max = { x: -Infinity, y: -Infinity }
  for (const p of polygon) {
    min.x = Math.min(min.x, p.x)
    min.y = Math.min(min.y, p.y)
    max.x = Math.max(max.x, p.x)
    max.y = Math.max(max.y, p.y)
  }
  return { min, max }
}

/** 两点欧氏距离 */
export function distance(a: Point, b: Point): number {
  return Math.hypot(a.x - b.x, a.y - b.y)
}

// ------------------------------------------------------------------
// Sutherland–Hodgman 凸多边形裁剪：计算凸重合区（装配 T 型节点）
// 要求裁剪窗口 clip 为凸多边形；subject 会被 clip 依次裁剪
// ------------------------------------------------------------------
function inside(p: Point, a: Point, b: Point): boolean {
  // 点 p 是否在有向边 a->b 左侧（配合逆时针裁剪窗口）
  return (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x) >= 0
}

function segIntersect(p1: Point, p2: Point, a: Point, b: Point): Point {
  const A1 = p2.y - p1.y
  const B1 = p1.x - p2.x
  const C1 = A1 * p1.x + B1 * p1.y
  const A2 = b.y - a.y
  const B2 = a.x - b.x
  const C2 = A2 * a.x + B2 * a.y
  const det = A1 * B2 - A2 * B1
  if (Math.abs(det) < 1e-9) return p2
  return {
    x: (B2 * C1 - B1 * C2) / det,
    y: (A1 * C2 - A2 * C1) / det,
  }
}

/** 保证多边形为逆时针方向 */
export function ensureCCW(polygon: Point[]): Point[] {
  return signedArea(polygon) < 0 ? [...polygon].reverse() : polygon
}

/** 凸多边形裁剪求交（返回交集多边形，可能为空） */
export function polygonIntersection(subject: Point[], clip: Point[]): Point[] {
  let output = ensureCCW(subject)
  const clipCCW = ensureCCW(clip)
  const n = clipCCW.length
  for (let i = 0; i < n; i++) {
    const a = clipCCW[i]
    const b = clipCCW[(i + 1) % n]
    const input = output
    output = []
    if (input.length === 0) break
    for (let j = 0; j < input.length; j++) {
      const cur = input[j]
      const prev = input[(j + input.length - 1) % input.length]
      const curIn = inside(cur, a, b)
      const prevIn = inside(prev, a, b)
      if (curIn) {
        if (!prevIn) output.push(segIntersect(prev, cur, a, b))
        output.push(cur)
      } else if (prevIn) {
        output.push(segIntersect(prev, cur, a, b))
      }
    }
  }
  return output
}

/**
 * 多边形向内腐蚀（近似）：把每个顶点沿其两邻边内法线方向缩进 margin。
 * 用于装配重合区留出最小搭接边距。适用于近凸的矩形类节点。
 */
export function erodePolygon(polygon: Point[], margin: number): Point[] {
  if (margin <= 0) return polygon
  const c = centroid(polygon)
  return polygon.map((p) => {
    const dx = p.x - c.x
    const dy = p.y - c.y
    const d = Math.hypot(dx, dy) || 1
    const shrink = Math.max(0, d - margin) / d
    return { x: c.x + dx * shrink, y: c.y + dy * shrink }
  })
}

/** 多边形最大内接尺寸的粗略估计（用于校验搭接是否足够） */
export function maxInscribedDimension(polygon: Point[]): number {
  const { min, max } = boundingBox(polygon)
  return Math.min(max.x - min.x, max.y - min.y)
}

/** 生成矩形多边形（左上角 + 宽高） */
export function rectPolygon(x: number, y: number, w: number, h: number): Point[] {
  return [
    { x, y },
    { x: x + w, y },
    { x: x + w, y: y + h },
    { x, y: y + h },
  ]
}

/** 生成圆近似多边形 */
export function circlePolygon(center: Point, radius: number, segments = 32): Point[] {
  const pts: Point[] = []
  for (let i = 0; i < segments; i++) {
    const a = (i / segments) * Math.PI * 2
    pts.push({ x: center.x + radius * Math.cos(a), y: center.y + radius * Math.sin(a) })
  }
  return pts
}
