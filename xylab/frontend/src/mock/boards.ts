// ==========================================================================
// 模拟装配标定数据（板件轮廓、钉合配对、设计钉位）
// 对应 assembly_T_joint.json，接入后端由 /api/calibration 提供
// ==========================================================================
import type { Board, DesignNail, NailingPair, Point } from '../lib/types'

/** T 型节点标定：下层平板 + 上层竖板（俯视投影） */
export const SAMPLE_BOARDS: Board[] = [
  {
    boardId: 'B1_base',
    role: 'base',
    layer: 0,
    thickness: 25,
    polygon: [
      { x: 0, y: 0 },
      { x: 600, y: 0 },
      { x: 600, y: 400 },
      { x: 0, y: 400 },
    ],
    color: '#a97142',
  },
  {
    boardId: 'B2_vertical',
    role: 'vertical',
    layer: 1,
    thickness: 25,
    polygon: [
      { x: 180, y: 120 },
      { x: 440, y: 120 },
      { x: 440, y: 220 },
      { x: 180, y: 220 },
    ],
    color: '#c89968',
  },
]

export const SAMPLE_PAIRS: NailingPair[] = [
  { upper: 'B2_vertical', lower: 'B1_base', minOverlap: 30 },
]

/** 设计钉合 Pattern：沿竖板中线均布 */
export function generateDesignNails(): DesignNail[] {
  const nails: DesignNail[] = []
  const y = 170
  let idx = 1
  for (let x = 210; x <= 410; x += 40) {
    nails.push({
      id: `N${idx}`,
      design: { x, y },
      status: 'pending',
    })
    idx++
  }
  // 增加两排偏移点，覆盖不同缺陷情形
  for (let x = 220; x <= 400; x += 60) {
    nails.push({ id: `N${idx}`, design: { x, y: 140 }, status: 'pending' })
    idx++
    nails.push({ id: `N${idx}`, design: { x, y: 200 }, status: 'pending' })
    idx++
  }
  return nails
}

export const SAMPLE_DESIGN_NAILS: DesignNail[] = generateDesignNails()

/** 手眼标定矩阵（示意，mm） */
export const HAND_EYE = {
  scale: 0.25, // mm/px
  rotationDeg: 0.3,
  translation: { x: 12.4, y: -8.1 } as Point,
  alignmentError: 0.32, // mm，需 <= 0.5mm
}
