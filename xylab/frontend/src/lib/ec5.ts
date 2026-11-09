// ==========================================================================
// Eurocode 5 (EN 1995-1-1) 钉连接最小间距/边距/端距计算 (Table 8.2)
// 以钉径 d 的倍数表示，随木材密度 rho_k、纹理角 alpha、是否预钻变化
// ==========================================================================

export interface EC5Input {
  /** 钉径 mm */
  d: number
  /** 特征密度 kg/m^3 */
  rhoK: number
  /** 纹理角 度（0=顺纹，90=横纹） */
  alphaDeg: number
  /** 是否预钻孔 */
  predrilled: boolean
}

export interface EC5Result {
  a1: number // 顺纹间距
  a2: number // 横纹间距
  a3t: number // 受荷端距
  a3c: number // 无荷端距
  a4t: number // 受荷边距
  a4c: number // 无荷边距
  /** 用于禁区膨胀的最小推荐边距（取端距/边距较大者与经验值） */
  minEdge: number
}

/** 计算 EC5 Table 8.2 各项间距（mm） */
export function computeEC5(input: EC5Input): EC5Result {
  const { d, rhoK, alphaDeg, predrilled } = input
  const alpha = (alphaDeg * Math.PI) / 180
  const cosA = Math.abs(Math.cos(alpha))
  const sinA = Math.abs(Math.sin(alpha))

  let a1: number
  let a2: number
  let a3t: number
  let a3c: number
  let a4t: number
  let a4c: number

  if (predrilled) {
    a1 = (4 + Math.abs(cosA)) * d
    a2 = 3 * d
    a3t = (7 + 5 * cosA) * d
    a3c = 7 * d
    a4t = (3 + 2 * sinA) * d
    a4c = 3 * d
  } else if (rhoK <= 420) {
    a1 = (5 + 7 * cosA) * d
    a2 = 5 * d
    a3t = (10 + 5 * cosA) * d
    a3c = 10 * d
    a4t = (5 + 2 * sinA) * d
    a4c = 5 * d
  } else {
    // 420 < rho_k <= 500
    a1 = (7 + 8 * cosA) * d
    a2 = 7 * d
    a3t = (15 + 5 * cosA) * d
    a3c = 15 * d
    a4t = (7 + 2 * sinA) * d
    a4c = 7 * d
  }

  const minEdge = Math.max(a4c, a4t)
  return {
    a1: round1(a1),
    a2: round1(a2),
    a3t: round1(a3t),
    a3c: round1(a3c),
    a4t: round1(a4t),
    a4c: round1(a4c),
    minEdge: round1(minEdge),
  }
}

/** EC5 无预钻嵌入强度 f_h,k = 0.082 * (1 - 0.01d) * rho_k [MPa] */
export function embeddingStrength(d: number, rhoK: number): number {
  return round1(0.082 * (1 - 0.01 * d) * rhoK)
}

/** 钢钉轴向拔出特征强度 f_ax,k = 20e-6 * rho_k^2 [MPa] */
export function withdrawalStrength(rhoK: number): number {
  return Number((20e-6 * rhoK * rhoK).toFixed(3))
}

function round1(x: number): number {
  return Math.round(x * 10) / 10
}
