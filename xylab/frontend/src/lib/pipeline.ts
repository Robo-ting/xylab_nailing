// ==========================================================================
// 全流程编排：图像/缺陷 -> ROI 过滤 -> 栅格化禁区 -> 膨胀 -> 软代价图
//   -> 每个设计钉位 KD-tree 最近可行点 -> 分层决策 -> 日志
// ==========================================================================
import type {
  Defect,
  DesignNail,
  LogEntry,
  NailingDecision,
  PlanningParams,
  Point,
  Roi,
} from './types'
import { createGrid, rasterizeDefects, pointToCell, idx, cellToPoint, markOutsidePolygon } from './grid'
import { dilateCircular, classifyDilation } from './morphology'
import { buildSoftCost, collectFeasiblePoints, findOptimalPoint } from './costmap'
import { KDTree } from './kdtree'
import { boundingBox, centroid, distance, pointInPolygon } from './geometry'
import { decideNail, nearestNailDistance, type NailContext } from './decision'

export interface PipelineInput {
  boardWidth: number
  boardHeight: number
  defects: Defect[]
  rois: Roi[]
  designNails: DesignNail[]
  params: PlanningParams
  substrate: string
  grainRelation: '顺纹' | '横纹' | '斜纹'
  /**
   * 装配重合区多边形（两块板层叠时的可钉合区）。
   * 提供后仅重合区内可钉：区外单元视为禁区，区外设计钉位将移入重合区。
   */
  nailableRegion?: Point[]
}

export interface PipelineResult {
  grid: ReturnType<typeof createGrid>
  /** 0=可行 1=缓冲 2=核心 */
  dilationClass: Uint8Array
  originalForbidden: Uint8Array
  acceptedDefects: number
  nails: DesignNail[]
  decisions: NailingDecision[]
  logs: LogEntry[]
  stats: {
    total: number
    direct: number
    relocated: number
    predrill: number
    skipped: number
    forbiddenCells: number
    feasibleCells: number
  }
}

/** 执行完整规划 + 决策流水线 */
export function runPipeline(input: PipelineInput): PipelineResult {
  const { params } = input
  // 1. 建栅格
  const grid = createGrid({
    width: input.boardWidth,
    height: input.boardHeight,
    cellSize: params.cellSize,
  })

  // 2. ROI 过滤 + 栅格化缺陷禁区
  const accepted = rasterizeDefects(grid, input.defects, input.rois)
  const originalForbidden = grid.forbidden.slice()

  // 3. 形态学膨胀（圆形核，半径 = dilationRadius）
  dilateCircular(grid, params.dilationRadius)
  const dilationClass = classifyDilation(originalForbidden, grid.forbidden)

  // 4. 软代价图
  if (params.costMode === 'soft') {
    buildSoftCost(grid, input.defects, input.rois, params.sigma)
  }

  // 4.5 装配约束：两块板层叠时仅重合区可钉，区外单元标为禁区
  const region = input.nailableRegion
  const hasRegion = !!region && region.length >= 3
  if (hasRegion) {
    markOutsidePolygon(grid, region!)
  }

  // 5. 构建可行域 KD-tree
  const feasible = collectFeasiblePoints(grid)
  const kd = new KDTree(feasible)

  // 6. 逐钉决策
  const nails: DesignNail[] = []
  const decisions: NailingDecision[] = []
  const logs: LogEntry[] = []
  const acceptedDefects = input.defects.filter((d) => defectAccepted(d, input.rois))

  const stats = {
    total: input.designNails.length,
    direct: 0,
    relocated: 0,
    predrill: 0,
    skipped: 0,
    forbiddenCells: 0,
    feasibleCells: feasible.length,
  }

  for (const dn of input.designNails) {
    const cell = pointToCell(grid, dn.design)
    const inForbidden =
      cell.col >= 0 &&
      cell.col < grid.cols &&
      cell.row >= 0 &&
      cell.row < grid.rows &&
      grid.forbidden[idx(grid, cell.col, cell.row)] === 1

    // KD-tree 最近可行点（若在禁区或软代价模式下寻优）
    let finalPoint: Point = dn.design
    let offset = 0
    if (inForbidden) {
      if (params.costMode === 'soft') {
        const opt = findOptimalPoint(grid, dn.design, params.alpha, params.beta, true)
        if (opt) {
          finalPoint = opt.point
          offset = opt.offset
        }
      } else {
        const nn = kd.nearest(dn.design)
        if (nn) {
          finalPoint = nn.point
          offset = nn.dist
        }
      }
    }

    // 组装局部上下文
    const nearby = acceptedDefects.filter((d) => {
      const c = centroid(d.polygon)
      return distance(c, dn.design) <= 20 // 20mm 局部上下文半径
    })
    const costValue =
      params.costMode === 'soft' && cellInBounds(grid, cell)
        ? grid.cost[idx(grid, cell.col, cell.row)]
        : 0

    const ctx: NailContext = {
      nailId: dn.id,
      position: dn.design,
      defectsNearby: nearby,
      inForbiddenZone: inForbidden,
      costValue,
      nearestMetalNail: nearestNailDistance(dn.design, acceptedDefects),
      substrate: input.substrate,
      grainRelation: input.grainRelation,
      assemblyOk: true,
    }

    const decision = decideNail(ctx, params, finalPoint)

    // 装配约束标注：设计钉位在两板重合区外的处理
    const assemblyInside = hasRegion ? pointInPolygon(dn.design, region!) : true
    if (!assemblyInside && decision.action !== 'SKIP') {
      if (offset > 0.5) {
        decision.reason = '装配约束：设计钉位在两板重合区外，已移入重合区最近可行点。' + decision.reason
        if (!decision.citedCodes.includes('装配约束 Layer-0')) decision.citedCodes.unshift('装配约束 Layer-0')
        decision.riskFlags.push('重合区外·已移入')
      } else {
        decision.action = 'SKIP'
        decision.reason = '装配约束：设计钉位在重合区外且无可行替代点，跳过。'
        decision.citedCodes = ['装配约束 Layer-0']
        decision.riskFlags.push('重合区外')
      }
    }

    // 依据动作确定状态与最终坐标
    let status: DesignNail['status'] = 'direct'
    if (decision.action === 'SKIP') {
      status = 'rejected'
      stats.skipped++
    } else if (decision.action === 'RELOCATE' || offset > 0.5) {
      status = 'relocated'
      stats.relocated++
    } else {
      status = 'direct'
      stats.direct++
    }
    if (decision.action === 'PREDRILL_THEN_NAIL') stats.predrill++

    const resolvedFinal = decision.action === 'SKIP' ? dn.design : finalPoint
    const resolvedOffset = decision.action === 'SKIP' ? 0 : offset

    nails.push({
      ...dn,
      final: resolvedFinal,
      offset: Number(resolvedOffset.toFixed(2)),
      status,
      action: decision.action,
      reason: decision.reason,
    })
    decisions.push({ ...decision, target: resolvedFinal })

    logs.push({
      timestamp: new Date().toISOString(),
      nailId: dn.id,
      action: decision.action,
      design: dn.design,
      final: resolvedFinal,
      offset: Number(resolvedOffset.toFixed(2)),
      reason: decision.reason,
      citedCodes: decision.citedCodes,
      compliant: decision.action !== 'SKIP',
    })
  }

  // 统计禁区单元
  for (let i = 0; i < grid.forbidden.length; i++) if (grid.forbidden[i]) stats.forbiddenCells++

  return {
    grid,
    dilationClass,
    originalForbidden,
    acceptedDefects: accepted,
    nails,
    decisions,
    logs,
    stats,
  }
}

function defectAccepted(d: Defect, rois: Roi[]): boolean {
  const active = rois.filter((r) => r.enabled)
  if (active.length === 0) return true
  const c = centroid(d.polygon)
  // 简单包含判定（射线法在 grid 中已用；此处复用质心）
  return active.some((r) => pointInPoly(c, r.polygon))
}

function pointInPoly(pt: Point, polygon: Point[]): boolean {
  let inside = false
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i].x
    const yi = polygon[i].y
    const xj = polygon[j].x
    const yj = polygon[j].y
    const intersect = yi > pt.y !== yj > pt.y && pt.x < ((xj - xi) * (pt.y - yi)) / (yj - yi) + xi
    if (intersect) inside = !inside
  }
  return inside
}

function cellInBounds(grid: ReturnType<typeof createGrid>, cell: { col: number; row: number }): boolean {
  return cell.col >= 0 && cell.col < grid.cols && cell.row >= 0 && cell.row < grid.rows
}

// 便捷：包围盒中心（供外部可视化）
export function defectCenter(d: Defect): Point {
  const bb = boundingBox(d.polygon)
  return { x: (bb.min.x + bb.max.x) / 2, y: (bb.min.y + bb.max.y) / 2 }
}
