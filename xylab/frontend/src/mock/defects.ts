// ==========================================================================
// 模拟缺陷数据（代替真实 YOLOv8-seg 输出）
// 接入后端后由 /api/detect 返回同结构数据
// ==========================================================================
import type { Defect, DefectType, Point } from '../lib/types'
import { polygonArea } from '../lib/geometry'

export const DEFECT_META: Record<
  DefectType,
  { label: string; color: string; en: string }
> = {
  knot_live: { label: '活节', en: 'Live knot', color: '#3b82f6' },
  knot_dead: { label: '死节', en: 'Dead knot', color: '#f59e0b' },
  crack: { label: '裂缝', en: 'Crack', color: '#ef4444' },
  decay: { label: '腐朽', en: 'Decay', color: '#8b5cf6' },
  wormhole: { label: '虫洞', en: 'Wormhole', color: '#ec4899' },
  nail_exposed: { label: '外露钉帽', en: 'Exposed nail', color: '#14b8a6' },
  nail_rusted: { label: '锈蚀钉帽', en: 'Rusted nail', color: '#a16207' },
}

function makePolygon(cx: number, cy: number, rx: number, ry: number, jitter = 0.25, n = 12): Point[] {
  const pts: Point[] = []
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2
    const r = 1 + (Math.sin(i * 2.3) * jitter)
    pts.push({ x: cx + rx * r * Math.cos(a), y: cy + ry * r * Math.sin(a) })
  }
  return pts
}

function makeDefect(
  id: string,
  type: DefectType,
  cx: number,
  cy: number,
  rx: number,
  ry: number,
  confidence: number,
  severity: Defect['severity'],
): Defect {
  const polygon = makePolygon(cx, cy, rx, ry)
  const xs = polygon.map((p) => p.x)
  const ys = polygon.map((p) => p.y)
  const minX = Math.min(...xs)
  const minY = Math.min(...ys)
  const maxX = Math.max(...xs)
  const maxY = Math.max(...ys)
  return {
    id,
    type,
    confidence,
    polygon,
    bbox: [minX, minY, maxX - minX, maxY - minY],
    area: Math.round(polygonArea(polygon)),
    severity,
  }
}

/** 板面尺寸（mm） */
export const SAMPLE_BOARD = { width: 600, height: 400 }

/** 内置样例缺陷集（600x400 板面） */
export const SAMPLE_DEFECTS: Defect[] = [
  makeDefect('D1', 'knot_live', 150, 120, 22, 20, 0.94, 'moderate'),
  makeDefect('D2', 'knot_dead', 380, 90, 18, 16, 0.88, 'severe'),
  makeDefect('D3', 'crack', 300, 250, 60, 8, 0.76, 'moderate'),
  makeDefect('D4', 'decay', 480, 300, 35, 30, 0.81, 'severe'),
  makeDefect('D5', 'wormhole', 220, 320, 10, 10, 0.65, 'minor'),
  makeDefect('D6', 'nail_exposed', 120, 300, 8, 8, 0.97, 'minor'),
  makeDefect('D7', 'knot_live', 500, 150, 16, 15, 0.9, 'minor'),
  makeDefect('D8', 'nail_rusted', 420, 200, 9, 9, 0.72, 'moderate'),
]

/** 第二块板（多板叠合演示） */
export const SAMPLE_DEFECTS_BOARD2: Defect[] = [
  makeDefect('E1', 'knot_dead', 200, 180, 20, 18, 0.85, 'moderate'),
  makeDefect('E2', 'crack', 350, 300, 50, 7, 0.7, 'moderate'),
  makeDefect('E3', 'knot_live', 450, 120, 18, 17, 0.92, 'minor'),
]
