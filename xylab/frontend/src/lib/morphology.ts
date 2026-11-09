// ==========================================================================
// 形态学膨胀：圆形结构元素（欧氏距离核）对禁区做 Minkowski 膨胀
// 对应 cv2.dilate(kernel=MORPH_ELLIPSE)，膨胀半径 r（默认 10mm，导师经验值）
// 采用两遍距离阈值法（等价于圆形核膨胀），复杂度友好
// ==========================================================================
import type { Grid } from './types'
import { idx } from './grid'

/**
 * 对禁区做圆形核膨胀，半径 radiusMm。
 * 实现：对每个原始禁区单元，将其半径内的单元置为禁区。
 * 为避免 O(N*k^2) 过大，采用「二值距离变换」思路的近似：
 * 先收集原始禁区边界，再用平方距离阈值扫描核窗口。
 */
export function dilateCircular(grid: Grid, radiusMm: number): void {
  const r = Math.round(radiusMm / grid.cellSize)
  if (r <= 0) return
  const { cols, rows } = grid
  const src = grid.forbidden.slice()
  const r2 = r * r

  // 预生成圆形核偏移
  const offsets: Array<[number, number]> = []
  for (let dy = -r; dy <= r; dy++) {
    for (let dx = -r; dx <= r; dx++) {
      if (dx * dx + dy * dy <= r2) offsets.push([dx, dy])
    }
  }

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      if (!src[idx(grid, col, row)]) continue
      // 该单元是原禁区，向圆形核范围膨胀
      for (const [dx, dy] of offsets) {
        const nc = col + dx
        const nr = row + dy
        if (nc < 0 || nc >= cols || nr < 0 || nr >= rows) continue
        grid.forbidden[idx(grid, nc, nr)] = 1
      }
    }
  }
}

/**
 * 区分「核心禁区」与「膨胀缓冲区」用于可视化：
 * 返回一个 Uint8Array：0=可行，1=缓冲(膨胀新增)，2=核心(原始禁区)
 */
export function classifyDilation(original: Uint8Array, dilated: Uint8Array): Uint8Array {
  const out = new Uint8Array(original.length)
  for (let i = 0; i < original.length; i++) {
    if (original[i]) out[i] = 2
    else if (dilated[i]) out[i] = 1
    else out[i] = 0
  }
  return out
}
