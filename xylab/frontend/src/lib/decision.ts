// ==========================================================================
// 决策引擎：分层决策架构
//   第0层 装配重合区约束 -> 第1层 规范硬规则预筛 -> 第2层 缺陷决策矩阵先验
//   -> 第3层 RAG + LLM 融合（前端以规则化模拟，后端可替换为真实 LLM）
// LLM 只输出策略 {action, reason, confidence, params}，坐标由确定性算法计算
// ==========================================================================
import type {
  Defect,
  DefectType,
  NailAction,
  NailingDecision,
  Point,
  PlanningParams,
} from './types'
import { distance } from './geometry'

/** 缺陷决策矩阵：缺陷类型 -> 默认策略与专属安全距（在全局膨胀基础上的修正 mm） */
export interface MatrixRow {
  type: DefectType
  label: string
  defaultAction: NailAction
  extraSafeDist: number
  note: string
}

export const DEFECT_DECISION_MATRIX: MatrixRow[] = [
  { type: 'knot_live', label: '活节', defaultAction: 'PREDRILL_THEN_NAIL', extraSafeDist: 10, note: '硬质活节，靠近时预钻孔避免劈裂' },
  { type: 'knot_dead', label: '死节', defaultAction: 'RELOCATE', extraSafeDist: 15, note: '死节易脱落，优先换位' },
  { type: 'crack', label: '裂缝', defaultAction: 'RELOCATE', extraSafeDist: 10, note: '垂直裂缝方向偏移，避免沿裂缝延长线' },
  { type: 'decay', label: '腐朽', defaultAction: 'SKIP', extraSafeDist: 20, note: '腐朽区强制跳过（硬规则）' },
  { type: 'wormhole', label: '虫洞', defaultAction: 'PREDRILL_THEN_NAIL', extraSafeDist: 8, note: '单孔可预钻，密集区跳过' },
  { type: 'nail_exposed', label: '外露钉帽', defaultAction: 'SKIP', extraSafeDist: 5, note: '正对既有铁钉必须跳过' },
  { type: 'nail_rusted', label: '锈蚀钉帽', defaultAction: 'SKIP', extraSafeDist: 5, note: '锈蚀铁钉跳过并标记人工复核' },
]

export function matrixLookup(type: DefectType): MatrixRow | undefined {
  return DEFECT_DECISION_MATRIX.find((r) => r.type === type)
}

/** 候选钉位局部上下文 */
export interface NailContext {
  nailId: string
  position: Point
  /** 半径内的缺陷 */
  defectsNearby: Defect[]
  /** 是否落在膨胀禁区 */
  inForbiddenZone: boolean
  /** 软代价 0~1 */
  costValue: number
  /** 距最近既有铁钉 mm */
  nearestMetalNail: number
  /** 基材 */
  substrate: string
  /** 纹理关系 */
  grainRelation: '顺纹' | '横纹' | '斜纹'
  /** 装配是否通过 */
  assemblyOk: boolean
}

/** 动作保守度排序：SKIP > RELOCATE > PREDRILL > NAIL */
const CONSERVATISM: Record<NailAction, number> = {
  SKIP: 3,
  RELOCATE: 2,
  PREDRILL_THEN_NAIL: 1,
  NAIL: 0,
}

function moreConservative(a: NailAction, b: NailAction): NailAction {
  return CONSERVATISM[a] >= CONSERVATISM[b] ? a : b
}

/**
 * 综合决策：模拟分层决策链，返回 NailingDecision。
 * 前端确定性实现；接入后端后第3层可替换为真实 LLM 调用。
 */
export function decideNail(ctx: NailContext, params: PlanningParams, target: Point): NailingDecision {
  const citedCodes: string[] = []
  const riskFlags: string[] = []

  // 第0层：装配约束
  if (!ctx.assemblyOk) {
    return {
      nailId: ctx.nailId,
      action: 'SKIP',
      target,
      reason: '候选点不在板件重合区（装配几何约束），跳过并标记人工复核',
      citedCodes: ['装配约束 Layer-0'],
      confidence: 0.95,
      params: {},
      riskFlags: ['装配区外'],
      stage: 'hard_rule',
    }
  }

  // 第1层：硬规则预筛（铁钉安全距）
  if (ctx.nearestMetalNail < params.nailSafeDist) {
    return {
      nailId: ctx.nailId,
      action: 'SKIP',
      target,
      reason: `距最近既有铁钉 ${ctx.nearestMetalNail.toFixed(1)}mm < 安全距 ${params.nailSafeDist}mm，跳过`,
      citedCodes: ['硬规则: SAFE_NAIL_DIST'],
      confidence: 0.98,
      params: {},
      riskFlags: ['邻近铁钉'],
      stage: 'hard_rule',
    }
  }

  // 无邻近缺陷且不在禁区：直接打钉
  if (ctx.defectsNearby.length === 0 && !ctx.inForbiddenZone) {
    return {
      nailId: ctx.nailId,
      action: 'NAIL',
      target,
      reason: '局部无缺陷、不在膨胀禁区，满足 EC5 边距，直接打钉',
      citedCodes: ['EN 1995-1-1 §8.3.1.2'],
      confidence: 0.92,
      params: { insertionAngle: 0, force: 800 },
      riskFlags: [],
      stage: 'hard_rule',
    }
  }

  // 第2层：缺陷决策矩阵先验（取最保守缺陷）
  let action: NailAction = 'NAIL'
  let matrixNote = ''
  let dominant: Defect | null = null
  for (const d of ctx.defectsNearby) {
    const row = matrixLookup(d.type)
    if (!row) continue
    let a = row.defaultAction
    // 严重程度调节
    if (d.severity === 'severe' && a === 'NAIL') a = 'RELOCATE'
    if (d.severity === 'moderate' && a === 'NAIL') a = 'PREDRILL_THEN_NAIL'
    const merged = moreConservative(action, a)
    if (merged !== action || !dominant) {
      dominant = d
      matrixNote = row.note
    }
    action = merged
  }

  // 基材 × 纹理修正：重竹顺纹劈裂风险高 -> 强制预钻
  if (ctx.substrate.includes('竹') && ctx.grainRelation === '顺纹') {
    if (action === 'NAIL') action = 'PREDRILL_THEN_NAIL'
    riskFlags.push('重竹顺纹劈裂风险')
  }

  if (dominant) {
    const row = matrixLookup(dominant.type)
    citedCodes.push(`缺陷矩阵: ${row?.label ?? dominant.type}`)
    if (dominant.confidence < 0.5) {
      riskFlags.push('检测不确定')
    }
  }

  // 第3层：RAG + LLM 融合（模拟），给出理由与置信度
  const stage: NailingDecision['stage'] = 'llm'
  let confidence = 0.78
  if (action === 'PREDRILL_THEN_NAIL') {
    citedCodes.push('EN 1995-1-1 §8.3.1.2 (预钻)')
    confidence = 0.85
  }
  if (action === 'RELOCATE') {
    citedCodes.push('KD-tree 最近可行点')
    confidence = 0.82
  }
  if (action === 'SKIP') {
    confidence = 0.9
  }

  // 置信度门槛：过低强制 SKIP + 人工复核
  if (confidence < params.confThreshold) {
    action = 'SKIP'
    riskFlags.push('置信度低于阈值，人工复核')
  }

  const reason = buildReason(action, dominant, matrixNote, ctx)
  const p: NailingDecision['params'] = {}
  if (action === 'NAIL' || action === 'RELOCATE') {
    p.insertionAngle = 0
    p.force = 800
  }
  if (action === 'PREDRILL_THEN_NAIL') {
    p.insertionAngle = 0
    p.predrillDepth = 4.4 // ≈0.8d, d=5.5
    p.force = 600
  }

  return {
    nailId: ctx.nailId,
    action,
    target,
    reason,
    citedCodes,
    confidence: Number(confidence.toFixed(2)),
    params: p,
    riskFlags,
    stage,
  }
}

function buildReason(
  action: NailAction,
  dominant: Defect | null,
  matrixNote: string,
  ctx: NailContext,
): string {
  const dlabel = dominant ? matrixLookup(dominant.type)?.label : undefined
  switch (action) {
    case 'NAIL':
      return `局部缺陷影响可控，满足规范边距，直接打钉。${matrixNote}`
    case 'PREDRILL_THEN_NAIL':
      return `邻近${dlabel ?? '缺陷'}，${matrixNote || '为避免劈裂先预钻孔再打钉'}（基材：${ctx.substrate}，${ctx.grainRelation}）`
    case 'RELOCATE':
      return `设计钉位受${dlabel ?? '缺陷'}影响，由 KD-tree 换位至最近可行点。${matrixNote}`
    case 'SKIP':
      return `受${dlabel ?? '缺陷/约束'}影响无法安全钉合，跳过。${matrixNote}`
  }
}

/** 距候选点最近的铁钉距离（mm） */
export function nearestNailDistance(pos: Point, defects: Defect[]): number {
  let min = Infinity
  for (const d of defects) {
    if (d.type === 'nail_exposed' || d.type === 'nail_rusted') {
      // 用质心近似
      const bb = d.bbox
      const c = { x: bb[0] + bb[2] / 2, y: bb[1] + bb[3] / 2 }
      min = Math.min(min, distance(pos, c))
    }
  }
  return min
}
