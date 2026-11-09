// ==========================================================================
// 全局状态：贯穿感知 -> 规划 -> 决策 -> 执行 全流程的共享数据与参数
// ==========================================================================
import { create } from 'zustand'
import type {
  Board,
  Defect,
  DesignNail,
  LogEntry,
  NailingDecision,
  NailingPair,
  PlanningParams,
  RobotState,
  Roi,
} from '../lib/types'
import type { MvpForbiddenRegion, MvpNailPoint, SourceKind, SourceRunResult } from '../api/client'
import { SAMPLE_DEFECTS, SAMPLE_BOARD } from '../mock/defects'
import { SAMPLE_BOARDS, SAMPLE_PAIRS, SAMPLE_DESIGN_NAILS } from '../mock/boards'

/** 流程阶段 */
export type Stage =
  | 'input'
  | 'detect'
  | 'forbidden'
  | 'decision'
  | 'coordinate'
  | 'execute'
  | 'log'

export const STAGES: { key: Stage; label: string }[] = [
  { key: 'input', label: '图像输入' },
  { key: 'detect', label: '缺陷检测' },
  { key: 'forbidden', label: '禁区/代价图' },
  { key: 'decision', label: 'Agent 决策' },
  { key: 'coordinate', label: '坐标精算' },
  { key: 'execute', label: '机械臂执行' },
  { key: 'log', label: '施工日志' },
]

export const DEFAULT_PARAMS: PlanningParams = {
  dilationRadius: 10,
  cellSize: 2,
  alpha: 1.0,
  beta: 30,
  sigma: 15,
  costMode: 'hard',
  nailSafeDist: 5,
  confThreshold: 0.6,
}

interface SystemState {
  // 全流程
  stageDone: Record<Stage, boolean>
  markStage: (s: Stage, done?: boolean) => void
  resetStages: () => void

  // 板面
  boardWidth: number
  boardHeight: number
  substrate: string
  grainRelation: '顺纹' | '横纹' | '斜纹'
  setSubstrate: (s: string) => void
  setGrainRelation: (g: '顺纹' | '横纹' | '斜纹') => void

  // 感知
  defects: Defect[]
  detectionSource: 'backend' | 'mock' | null
  setDefects: (d: Defect[], source: 'backend' | 'mock') => void
  enabledTypes: Set<string>
  toggleType: (t: string) => void
  confFilter: number
  setConfFilter: (v: number) => void

  // 装配
  boards: Board[]
  pairs: NailingPair[]
  setBoards: (b: Board[]) => void

  // ROI
  rois: Roi[]
  addRoi: (r: Roi) => void
  removeRoi: (id: string) => void
  toggleRoi: (id: string) => void
  clearRois: () => void

  // 规划参数
  params: PlanningParams
  setParams: (p: Partial<PlanningParams>) => void

  // 钉位
  designNails: DesignNail[]
  setDesignNails: (n: DesignNail[]) => void
  plannedNails: DesignNail[]
  decisions: NailingDecision[]
  setPlanning: (nails: DesignNail[], decisions: NailingDecision[]) => void

  // 日志
  logs: LogEntry[]
  setLogs: (l: LogEntry[]) => void

  // 机器人
  robotState: RobotState
  setRobotState: (s: RobotState) => void

  // 图片 MVP（原图像素坐标；与浏览器 pipeline 隔离）
  imageMvpActive: boolean
  imageId: string | null
  imageUrl: string | null
  imageWidthPx: number | null
  imageHeightPx: number | null
  detectionMode: 'mock' | null
  mvpDefects: Defect[]
  mvpForbidden: MvpForbiddenRegion[]
  mvpNails: MvpNailPoint[]
  edgeMarginPx: number
  knotMarginPx: number
  nailSpacingPx: number
  setMvpParams: (p: Partial<{ edgeMarginPx: number; knotMarginPx: number; nailSpacingPx: number }>) => void
  setImageDetect: (payload: {
    imageId: string
    imageUrl: string
    imageWidthPx: number
    imageHeightPx: number
    detectionMode: 'mock'
    defects: Defect[]
  }) => void
  setImagePlan: (forbidden: MvpForbiddenRegion[], nails: MvpNailPoint[]) => void
  sourceId: string | null
  sourceKind: SourceKind | null
  zonePoints: { x: number; y: number }[] | null
  zoneScaled: boolean
  droppedDefects: number
  applySourceResult: (payload: SourceRunResult) => void
  bumpPreview: (url: string) => void
}

export const useSystemStore = create<SystemState>((set) => ({
  stageDone: {
    input: false,
    detect: false,
    forbidden: false,
    decision: false,
    coordinate: false,
    execute: false,
    log: false,
  },
  markStage: (s, done = true) =>
    set((st) => ({ stageDone: { ...st.stageDone, [s]: done } })),
  resetStages: () =>
    set({
      stageDone: {
        input: false,
        detect: false,
        forbidden: false,
        decision: false,
        coordinate: false,
        execute: false,
        log: false,
      },
    }),

  boardWidth: SAMPLE_BOARD.width,
  boardHeight: SAMPLE_BOARD.height,
  substrate: '重竹',
  grainRelation: '顺纹',
  setSubstrate: (s) => set({ substrate: s }),
  setGrainRelation: (g) => set({ grainRelation: g }),

  defects: SAMPLE_DEFECTS,
  detectionSource: null,
  setDefects: (d, source) => set({ defects: d, detectionSource: source }),
  enabledTypes: new Set([
    'knot_live',
    'knot_dead',
    'crack',
    'decay',
    'wormhole',
    'nail_exposed',
    'nail_rusted',
  ]),
  toggleType: (t) =>
    set((st) => {
      const next = new Set(st.enabledTypes)
      if (next.has(t)) next.delete(t)
      else next.add(t)
      return { enabledTypes: next }
    }),
  confFilter: 0.3,
  setConfFilter: (v) => set({ confFilter: v }),

  boards: SAMPLE_BOARDS,
  pairs: SAMPLE_PAIRS,
  setBoards: (b) => set({ boards: b }),

  rois: [],
  addRoi: (r) => set((st) => ({ rois: [...st.rois, r] })),
  removeRoi: (id) => set((st) => ({ rois: st.rois.filter((r) => r.id !== id) })),
  toggleRoi: (id) =>
    set((st) => ({
      rois: st.rois.map((r) => (r.id === id ? { ...r, enabled: !r.enabled } : r)),
    })),
  clearRois: () => set({ rois: [] }),

  params: DEFAULT_PARAMS,
  setParams: (p) => set((st) => ({ params: { ...st.params, ...p } })),

  designNails: SAMPLE_DESIGN_NAILS,
  setDesignNails: (n) => set({ designNails: n }),
  plannedNails: [],
  decisions: [],
  setPlanning: (nails, decisions) => set({ plannedNails: nails, decisions }),

  logs: [],
  setLogs: (l) => set({ logs: l }),

  robotState: 'HOME',
  setRobotState: (s) => set({ robotState: s }),

  imageMvpActive: false,
  imageId: null,
  imageUrl: null,
  imageWidthPx: null,
  imageHeightPx: null,
  detectionMode: null,
  mvpDefects: [],
  mvpForbidden: [],
  mvpNails: [],
  edgeMarginPx: 40,
  knotMarginPx: 30,
  nailSpacingPx: 80,
  setMvpParams: (p) => set((st) => ({ ...st, ...p })),
  setImageDetect: (payload) =>
    set({
      imageMvpActive: true,
      imageId: payload.imageId,
      imageUrl: payload.imageUrl,
      imageWidthPx: payload.imageWidthPx,
      imageHeightPx: payload.imageHeightPx,
      detectionMode: payload.detectionMode,
      mvpDefects: payload.defects,
      mvpForbidden: [],
      mvpNails: [],
    }),
  setImagePlan: (forbidden, nails) => set({ mvpForbidden: forbidden, mvpNails: nails }),

  sourceId: null,
  sourceKind: null,
  zonePoints: null,
  zoneScaled: false,
  droppedDefects: 0,
  applySourceResult: (payload) =>
    set({
      imageMvpActive: true,
      sourceId: payload.sourceId,
      sourceKind: payload.kind,
      imageId: payload.sourceId,
      imageUrl: payload.imageUrl,
      imageWidthPx: payload.width,
      imageHeightPx: payload.height,
      detectionMode: 'mock',
      mvpDefects: payload.defects,
      mvpForbidden: payload.forbiddenRegions,
      mvpNails: payload.nailPoints,
      zonePoints: payload.zone,
      zoneScaled: payload.zoneScaled,
      droppedDefects: payload.dropped,
    }),
  bumpPreview: (url) => set({ imageUrl: url }),
}))
