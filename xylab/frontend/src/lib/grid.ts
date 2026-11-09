// ==========================================================================
// 栅格化：把缺陷掩码多边形写入布尔禁区栅格（射线法内外判定）
// 支持 ROI 过滤：仅落在启用 ROI 内的缺陷参与禁区构建
// ==========================================================================
import type { Defect, Grid, Point, Roi } from './types'
import { pointInPolygon, boundingBox } from './geometry'

export interface GridSpec {
  /** 板面宽度 mm */
  width: number
  /** 板面高度 mm */
  height: number
  /** 栅格单元 mm（默认 1mm） */
  cellSize: number
  origin?: Point
}

/** 创建空栅格 */
export function createGrid(spec: GridSpec): Grid {
  const cellSize = spec.cellSize
  const cols = Math.ceil(spec.width / cellSize)
  const rows = Math.ceil(spec.height / cellSize)
  return {
    cols,
    rows,
    cellSize,
    origin: spec.origin ?? { x: 0, y: 0 },
    forbidden: new Uint8Array(cols * rows),
    cost: new Float32Array(cols * rows),
  }
}

/** 栅格索引 -> 物理坐标（单元中心） */
export function cellToPoint(grid: Grid, col: number, row: number): Point {
  return {
    x: grid.origin.x + (col + 0.5) * grid.cellSize,
    y: grid.origin.y + (row + 0.5) * grid.cellSize,
  }
}

/** 物理坐标 -> 栅格索引 */
export function pointToCell(grid: Grid, pt: Point): { col: number; row: number } {
  return {
    col: Math.floor((pt.x - grid.origin.x) / grid.cellSize),
    row: Math.floor((pt.y - grid.origin.y) / grid.cellSize),
  }
}

export function idx(grid: Grid, col: number, row: number): number {
  return row * grid.cols + col
}

export function inBounds(grid: Grid, col: number, row: number): boolean {
  return col >= 0 && col < grid.cols && row >= 0 && row < grid.rows
}

/**
 * 判断缺陷是否被 ROI 采纳：
 * - 无启用 ROI 时全部采纳；
 * - 有启用 ROI 时，缺陷质心落在任一启用 ROI 内即采纳。
 */
export function defectInRois(defect: Defect, rois: Roi[]): boolean {
  const active = rois.filter((r) => r.enabled)
  if (active.length === 0) return true
  const bb = boundingBox(defect.polygon)
  const c = { x: (bb.min.x + bb.max.x) / 2, y: (bb.min.y + bb.max.y) / 2 }
  return active.some((r) => pointInPolygon(c, r.polygon))
}

/**
 * 把缺陷多边形栅格化写入禁区（射线法）。返回被采纳的缺陷数量。
 * 只在缺陷包围盒范围内遍历，提升性能。
 */
export function rasterizeDefects(grid: Grid, defects: Defect[], rois: Roi[]): number {
  let accepted = 0
  for (const d of defects) {
    if (!defectInRois(d, rois)) continue
    accepted++
    const bb = boundingBox(d.polygon)
    const c0 = pointToCell(grid, bb.min)
    const c1 = pointToCell(grid, bb.max)
    for (let row = Math.max(0, c0.row); row <= Math.min(grid.rows - 1, c1.row); row++) {
      for (let col = Math.max(0, c0.col); col <= Math.min(grid.cols - 1, c1.col); col++) {
        const p = cellToPoint(grid, col, row)
        if (pointInPolygon(p, d.polygon)) {
          grid.forbidden[idx(grid, col, row)] = 1
        }
      }
    }
  }
  return accepted
}

/** 把规范边距区（板面边缘 margin）标为禁区 */
export function markEdgeMargin(grid: Grid, marginMm: number): void {
  const m = Math.round(marginMm / grid.cellSize)
  for (let row = 0; row < grid.rows; row++) {
    for (let col = 0; col < grid.cols; col++) {
      if (col < m || row < m || col >= grid.cols - m || row >= grid.rows - m) {
        grid.forbidden[idx(grid, col, row)] = 1
      }
    }
  }
}

/**
 * 装配约束：把落在给定重合区多边形之外的所有单元标为禁区。
 * 用于「两块板层叠、仅重合区可钉合」场景（T 型节点 Layer-0 约束）。
 */
export function markOutsidePolygon(grid: Grid, polygon: Point[]): void {
  if (polygon.length < 3) return
  for (let row = 0; row < grid.rows; row++) {
    for (let col = 0; col < grid.cols; col++) {
      const p = cellToPoint(grid, col, row)
      if (!pointInPolygon(p, polygon)) {
        grid.forbidden[idx(grid, col, row)] = 1
      }
    }
  }
}

/** 统计禁区单元数 */
export function countForbidden(grid: Grid): number {
  let n = 0
  for (let i = 0; i < grid.forbidden.length; i++) if (grid.forbidden[i]) n++
  return n
}
