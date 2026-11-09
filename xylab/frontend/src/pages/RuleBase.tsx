import { useState } from 'react'
import { Panel } from '../components/Panel'
import { ragSearch } from '../api/client'
import { INGESTED_SOURCES } from '../mock/rules'
import type { RuleChunk } from '../lib/types'

const PRIORITY_BADGE: Record<string, string> = {
  hard: 'badge-red',
  high: 'badge-amber',
  medium: 'badge-blue',
  low: 'badge-gray',
}

const CATEGORY_LABEL: Record<string, string> = {
  design: '设计规范',
  test: '试验规范',
  material: '材料规范',
  experience: '课题组经验',
}

export function RuleBase() {
  const [query, setQuery] = useState('钉 最小间距 边距 预钻')
  const [results, setResults] = useState<RuleChunk[]>([])
  const [source, setSource] = useState<'backend' | 'mock' | null>(null)
  const [loading, setLoading] = useState(false)

  async function doSearch() {
    setLoading(true)
    const res = await ragSearch(query, 5)
    setResults(res.chunks)
    setSource(res.source)
    setLoading(false)
  }

  return (
    <div>
      <div className="page-title">规范规则库 · Rule Base (RAG)</div>
      <div className="page-desc">
        规范知识库与检索增强：规范 PDF 经 ingest() 切块入向量库，决策时按语义检索相关条款。
        真实检索由后端 /api/rules/search 提供（bge-m3 + Chroma），当前为模拟。
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 16 }}>
        <div>
          <Panel title="已入库规范" tag={`${INGESTED_SOURCES.length} 部`}>
            {INGESTED_SOURCES.map((s) => (
              <div key={s.code} style={{ marginBottom: 10 }}>
                <div className="row spread">
                  <span className="mono">{s.code}</span>
                  <span className={'badge ' + PRIORITY_BADGE.medium}>{CATEGORY_LABEL[s.category]}</span>
                </div>
                <div className="hint">{s.standard} · {s.chunks} 块 · {s.lang}</div>
              </div>
            ))}
            <div className="divider" />
            <button className="btn btn-sm" style={{ width: '100%' }}>＋ 上传规范 PDF 并 ingest</button>
            <div className="hint" style={{ marginTop: 8 }}>
              切块策略 by_clause · max_tokens 400 · overlap 50
            </div>
          </Panel>
        </div>

        <div>
          <Panel title="RAG 检索调试" tag={source ? (source === 'backend' ? '后端' : '模拟') : ''}>
            <div className="row" style={{ marginBottom: 12 }}>
              <input
                type="text"
                style={{ flex: 1 }}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="输入自然语言检索，如：重竹 预钻孔 劈裂"
                onKeyDown={(e) => e.key === 'Enter' && doSearch()}
              />
              <button className="btn btn-primary" onClick={doSearch} disabled={loading}>
                {loading ? '检索中…' : '🔍 检索 Top-5'}
              </button>
            </div>

            {results.length === 0 && <div className="hint">输入查询并检索，返回按相关度排序的规范条款块。</div>}

            {results.map((r, i) => (
              <div key={r.ruleId} className="stat-card" style={{ marginBottom: 10 }}>
                <div className="row spread" style={{ marginBottom: 6 }}>
                  <span>
                    <span className="badge badge-blue" style={{ marginRight: 6 }}>#{i + 1}</span>
                    <span className="mono">{r.code}</span>
                    {r.page && <span className="hint"> · p.{r.page}</span>}
                  </span>
                  <span>
                    <span className={'badge ' + PRIORITY_BADGE[r.priority]} style={{ marginRight: 6 }}>{r.priority}</span>
                    {r.score !== undefined && <span className="badge badge-gray">score {r.score}</span>}
                  </span>
                </div>
                <div style={{ fontSize: 13 }}>{r.text}</div>
                <div className="hint" style={{ marginTop: 6 }}>{r.source} · {CATEGORY_LABEL[r.category]}</div>
              </div>
            ))}
          </Panel>

          <Panel title="防幻觉 · 引用校验">
            <div className="hint">
              LLM 输出的 cited_rules 必须命中检索结果，且不得违反 priority=hard 条款；
              校验失败则回退安全动作 SKIP。
            </div>
            <div className="mono-block" style={{ marginTop: 10 }}>
{`verify_citation(decision, retrieved) -> PASS/FAIL
check_hard_rule_conflict(decision, retrieved) -> PASS/FAIL
if FAIL: fallback_to_safe(SKIP) + log.warning`}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  )
}
