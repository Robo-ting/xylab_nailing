// ==========================================================================
// KD-Tree：二维最近邻查询，用于在可行域中查找距设计钉位最近的可行点
// 对应 scipy.spatial.KDTree，构建 O(N log N)，查询 O(log N)
// ==========================================================================
import type { Point } from './types'

interface KDNode {
  point: Point
  axis: number
  left: KDNode | null
  right: KDNode | null
  index: number
}

export class KDTree {
  private root: KDNode | null

  constructor(points: Point[]) {
    const indexed = points.map((p, i) => ({ p, i }))
    this.root = this.build(indexed, 0)
  }

  private build(items: Array<{ p: Point; i: number }>, depth: number): KDNode | null {
    if (items.length === 0) return null
    const axis = depth % 2
    items.sort((a, b) => (axis === 0 ? a.p.x - b.p.x : a.p.y - b.p.y))
    const mid = Math.floor(items.length / 2)
    const item = items[mid]
    return {
      point: item.p,
      index: item.i,
      axis,
      left: this.build(items.slice(0, mid), depth + 1),
      right: this.build(items.slice(mid + 1), depth + 1),
    }
  }

  /** 查询最近点，返回 {point, index, dist}；树为空返回 null */
  nearest(target: Point): { point: Point; index: number; dist: number } | null {
    if (!this.root) return null
    let best: KDNode | null = null
    let bestDist = Infinity

    const search = (node: KDNode | null) => {
      if (!node) return
      const d = this.dist2(node.point, target)
      if (d < bestDist) {
        bestDist = d
        best = node
      }
      const diff =
        node.axis === 0 ? target.x - node.point.x : target.y - node.point.y
      const near = diff < 0 ? node.left : node.right
      const far = diff < 0 ? node.right : node.left
      search(near)
      // 若分割超平面距离仍可能存在更近点，则搜索另一侧
      if (diff * diff < bestDist) search(far)
    }

    search(this.root)
    if (!best) return null
    const node = best as KDNode
    return { point: node.point, index: node.index, dist: Math.sqrt(bestDist) }
  }

  private dist2(a: Point, b: Point): number {
    const dx = a.x - b.x
    const dy = a.y - b.y
    return dx * dx + dy * dy
  }
}
