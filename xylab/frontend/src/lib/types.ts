// ==========================================================================
// XYLab 预制竹木结构机械臂智能钉合控制系统 - 公共类型定义
// ==========================================================================

/** 二维点，单位：毫米（板面物理坐标系） */
export interface Point {
  x: number
  y: number
}

/** 缺陷类别（YOLOv8-seg 7 类） */
export type DefectType =
  | 'knot_live' // 活节
  | 'knot_dead' // 死节
  | 'crack' // 裂缝
  | 'decay' // 腐朽
  | 'wormhole' // 虫洞
  | 'nail_exposed' // 外露钉帽
  | 'nail_rusted' // 锈蚀钉帽

/** 缺陷严重程度 */
export type Severity = 'minor' | 'moderate' | 'severe'

/** 单个缺陷检测结果 */
export interface Defect {
  id: string
  type: DefectType
  /** 置信度 0~1 */
  confidence: number
  /** 分割掩码多边形（物理坐标 mm），非凸 */
  polygon: Point[]
  /** 外接矩形 [x, y, w, h] */
  bbox: [number, number, number, number]
  /** 面积 mm^2 */
  area: number
  /** 严重程度 */
  severity: Severity
  /** 所属板 id（多板叠合时） */
  boardId?: string
}

/** 设计钉位 */
export interface DesignNail {
  id: string
  /** 设计原始坐标 mm */
  design: Point
  /** 规划后的最终坐标 mm */
  final?: Point
  /** 偏移量 mm */
  offset?: number
  /** 决策状态 */
  status?: NailStatus
  /** 决策动作 */
  action?: NailAction
  /** 决策原因 */
  reason?: string
}

export type NailStatus = 'pending' | 'direct' | 'relocated' | 'rejected'

/** 四类决策动作 */
export type NailAction = 'NAIL' | 'PREDRILL_THEN_NAIL' | 'RELOCATE' | 'SKIP'

/** ROI 感兴趣区域（框选） */
export interface Roi {
  id: string
  /** 形状类型 */
  shape: 'rect' | 'circle' | 'polygon'
  /** 多边形顶点（统一转成多边形表示，mm） */
  polygon: Point[]
  /** 是否启用 */
  enabled: boolean
  label?: string
}

/** 板件（装配标定） */
export interface Board {
  boardId: string
  role: 'base' | 'vertical' | 'panel'
  layer: number
  thickness: number
  /** 俯视轮廓多边形 mm（机器人基坐标系） */
  polygon: Point[]
  color?: string
}

/** 钉合配对（T 型节点） */
export interface NailingPair {
  upper: string
  lower: string
  minOverlap: number
}

/** 栅格代价图 */
export interface Grid {
  cols: number
  rows: number
  cellSize: number
  /** 原点（物理坐标 mm） */
  origin: Point
  /** 布尔禁区（true=禁区），长度 cols*rows */
  forbidden: Uint8Array
  /** 软代价 0~1，长度 cols*rows */
  cost: Float32Array
}

/** 规范规则块（RAG） */
export interface RuleChunk {
  ruleId: string
  text: string
  source: string
  code: string
  category: 'design' | 'test' | 'material' | 'experience'
  priority: 'hard' | 'high' | 'medium' | 'low'
  page?: number
  score?: number
}

/** 决策智能体输出 */
export interface NailingDecision {
  nailId: string
  action: NailAction
  target: Point
  reason: string
  citedCodes: string[]
  confidence: number
  params: {
    force?: number
    predrillDepth?: number
    insertionAngle?: number
  }
  riskFlags: string[]
  /** 决策链：硬规则 / 矩阵先验 / LLM */
  stage: 'hard_rule' | 'matrix' | 'llm'
}

/** 施工日志条目 */
export interface LogEntry {
  timestamp: string
  nailId: string
  action: NailAction
  design: Point
  final: Point
  offset: number
  reason: string
  citedCodes: string[]
  compliant: boolean
}

/** 机械臂状态 */
export type RobotState = 'HOME' | 'SCANNING' | 'MOVING' | 'NAILING' | 'PREDRILL' | 'ESTOP'

/** 规划参数（全局） */
export interface PlanningParams {
  /** 膨胀半径 mm（导师确认经验值 10mm） */
  dilationRadius: number
  /** 栅格单元 mm */
  cellSize: number
  /** 距离权重 */
  alpha: number
  /** 代价权重 */
  beta: number
  /** 高斯衰减 sigma mm */
  sigma: number
  /** 代价模式 */
  costMode: 'hard' | 'soft'
  /** 铁钉安全距 mm */
  nailSafeDist: number
  /** 置信度阈值：低于此人工复核 */
  confThreshold: number
}
