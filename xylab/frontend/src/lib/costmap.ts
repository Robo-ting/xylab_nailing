// ==========================================================================
// 软代价图：以缺陷置信度为权重的高斯衰减代价场
//   C_k(p) = conf_k * exp(-d^2 / (2 sigma^2))，多缺陷叠加后截断到 [0,1]
// 目标函数：p* = argmin [ alpha * d(p, p0) + beta * C(p) ]，p ∈ 可行域
// ==========================================================================
import type { Defect, Grid, Point, Roi } from './types'
import { cellToPoint, idx, defectInRois } from './grid'
import { centroid } from './geometry'

/** 计算软代价场（写入 grid.cost） */
export function buildSoftCost(grid: Grid, defects: Defect[], rois: Roi[], sigmaMm: number): void {
  const sigma = Math.max(1, sigmaMm)
  const twoSigma2 = 2 * sigma * sigma
  // 缺陷中心（质心）与置信度
  const centers = defects
    .filter((d) => defectInRois(d, rois))
    .map((d) => ({ c: centroid(d.polygon), conf: d.confidence }))

  for (let row = 0; row < grid.rows; row++) {
    for (let col = 0; col < grid.cols; col++) {
      const p = cellToPoint(grid, col, row)
      let c = 0
      for (const { c: center, conf } of centers) {
        const dx = p.x - center.x
        const dy = p.y - center.y
        const d2 = dx * dx + dy * dy
        c += conf * Math.exp(-d2 / twoSigma2)
      }
      grid.cost[idx(grid, col, row)] = Math.min(1, c)
    }
  }
}

/**
 * 在可行域内寻找综合目标最优点（结合偏移距离与软代价）。
 * 返回最优物理坐标与其偏移量；若无可行点返回 null。
 */
export function findOptimalPoint(
  grid: Grid,
  design: Point,
  alpha: number,
  beta: number,
  useSoftCost: boolean,
): { point: Point; offset: number; cost: number } | null {
  let best: Point | null = null
  let bestScore = Infinity
  let bestOffset = 0
  let bestCost = 0

  for (let row = 0; row < grid.rows; row++) {
    for (let col = 0; col < grid.cols; col++) {
      const i = idx(grid, col, row)
      if (grid.forbidden[i]) continue
      const p = cellToPoint(grid, col, row)
      const dx = p.x - design.x
      const dy = p.y - design.y
      const dist = Math.hypot(dx, dy)
      const cost = useSoftCost ? grid.cost[i] : 0
      const score = alpha * dist + beta * cost
      if (score < bestScore) {
        bestScore = score
        best = p
        bestOffset = dist
        bestCost = cost
      }
    }
  }

  if (!best) return null
  return { point: best, offset: bestOffset, cost: bestCost }
}

/** 收集所有可行单元中心（供 KD-tree 构建） */
export function collectFeasiblePoints(grid: Grid): Point[] {
  const pts: Point[] = []
  for (let row = 0; row < grid.rows; row++) {
    for (let col = 0; col < grid.cols; col++) {
      if (!grid.forbidden[idx(grid, col, row)]) {
        pts.push(cellToPoint(grid, col, row))
      }
    }
  }
  return pts
}
