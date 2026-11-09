// ==========================================================================
// 模拟规范知识库（RAG）：已 ingest 的规范条款块
// 接入后端由 /api/rules/search 返回向量检索结果
// ==========================================================================
import type { RuleChunk } from '../lib/types'

export interface IngestedSource {
  code: string
  standard: string
  category: RuleChunk['category']
  lang: string
  chunks: number
  status: 'ready' | 'processing'
}

export const INGESTED_SOURCES: IngestedSource[] = [
  { code: 'EN 1995-1-1', standard: 'Eurocode 5 木结构设计', category: 'design', lang: 'en', chunks: 128, status: 'ready' },
  { code: 'EN 1382', standard: '木结构紧固件拔出承载力试验', category: 'test', lang: 'en', chunks: 34, status: 'ready' },
  { code: 'EN 1380', standard: '承重钉连接试验方法', category: 'test', lang: 'en', chunks: 28, status: 'ready' },
  { code: 'EN 26891', standard: '紧固件连接力学性能测定', category: 'test', lang: 'en', chunks: 22, status: 'ready' },
  { code: 'EN 384', standard: '结构木材特征值测定', category: 'material', lang: 'en', chunks: 41, status: 'ready' },
  { code: 'GB/T 50005', standard: '木结构设计标准', category: 'design', lang: 'zh', chunks: 96, status: 'ready' },
]

export const RULE_CHUNKS: RuleChunk[] = [
  {
    ruleId: 'EN1995-8.3.1.2',
    text: '钉连接最小间距、边距和端距应符合 Table 8.2 规定。未预钻孔时，密度 ρk≤420kg/m³ 的软木，顺纹间距 a1=(5+7|cosα|)d，横纹间距 a2=5d，受荷端距 a3,t=(10+5cosα)d。',
    source: 'Eurocode 5',
    code: 'EN 1995-1-1',
    category: 'design',
    priority: 'hard',
    page: 62,
  },
  {
    ruleId: 'EN1995-8.3.1.1',
    text: '当木材密度 ρk>500kg/m³ 或钉径 d≥6mm 时，应预钻孔，以避免劈裂。预钻孔直径不应超过钉径的 0.8 倍。',
    source: 'Eurocode 5',
    code: 'EN 1995-1-1',
    category: 'design',
    priority: 'hard',
    page: 61,
  },
  {
    ruleId: 'EN1382-6.2',
    text: '拔出试验加载应使试件在 (300±120)s 内破坏，即破坏时间处于 180–420s 区间。宜采用恒定位移速率控制。',
    source: 'EN 1382',
    code: 'EN 1382',
    category: 'test',
    priority: 'high',
    page: 8,
  },
  {
    ruleId: 'EN26891-7.1',
    text: '试验加载程序：先加至预估破坏荷载的 40%，保持 30s，卸载至 10%，保持 30s，再以 0.2Fest/min 速率加载至破坏。滑移模量按 Kser=0.4·Fest/vi,mod 计算。',
    source: 'EN 26891',
    code: 'EN 26891',
    category: 'test',
    priority: 'high',
    page: 5,
  },
  {
    ruleId: 'EXP-knot-dilation',
    text: '经验规则（导师肖岩确认）：钉位距缺陷边缘的膨胀安全半径取 10mm，作为规范边距外的附加避让，兼顾检测误差与承载力折减。',
    source: '课题组经验',
    code: 'LAB-EXP',
    category: 'experience',
    priority: 'high',
  },
  {
    ruleId: 'EXP-bamboo-predrill',
    text: '经验规则：重竹基材顺纹方向劈裂风险极高，靠近缺陷或边距不足时强制预钻孔，孔径约 0.8d；必要时采用斜向打入。',
    source: '课题组经验',
    code: 'LAB-EXP',
    category: 'experience',
    priority: 'medium',
  },
  {
    ruleId: 'EN384-5',
    text: '结构木材特征密度 ρk 取 5% 分位值，含水率修正至 12% 标准状态。嵌入强度随密度线性增长。',
    source: 'EN 384',
    code: 'EN 384',
    category: 'material',
    priority: 'medium',
    page: 11,
  },
]

/** 简易关键词检索（模拟向量检索），返回按相关度排序的 Top-K */
export function searchRules(query: string, topK = 5): RuleChunk[] {
  const q = query.toLowerCase()
  const terms = q.split(/[\s,，、]+/).filter(Boolean)
  const scored = RULE_CHUNKS.map((r) => {
    const hay = (r.text + ' ' + r.code + ' ' + r.source).toLowerCase()
    let score = 0
    for (const t of terms) {
      if (hay.includes(t)) score += 1
    }
    // 硬规则加权
    if (r.priority === 'hard') score += 0.3
    return { r, score: score + Math.random() * 0.05 }
  })
  return scored
    .filter((s) => s.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, topK)
    .map((s) => ({ ...s.r, score: Number(s.score.toFixed(2)) }))
}
