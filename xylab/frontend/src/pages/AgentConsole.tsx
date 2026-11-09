import { useState } from 'react'
import { Panel } from '../components/Panel'
import { useSystemStore } from '../store/useSystemStore'
import type { NailingDecision } from '../lib/types'

const ACTION_LABEL: Record<string, string> = {
  NAIL: '直接打钉',
  PREDRILL_THEN_NAIL: '预钻后打钉',
  RELOCATE: '换位',
  SKIP: '跳过',
}
const ACTION_BADGE: Record<string, string> = {
  NAIL: 'badge-green',
  PREDRILL_THEN_NAIL: 'badge-purple',
  RELOCATE: 'badge-amber',
  SKIP: 'badge-red',
}
const STAGE_LABEL: Record<string, string> = {
  hard_rule: '硬规则',
  matrix: '决策矩阵',
  llm: 'RAG+LLM',
}

export function AgentConsole() {
  const { decisions, params } = useSystemStore()
  const [selected, setSelected] = useState<NailingDecision | null>(null)

  const humanReview = decisions.filter((d) => d.riskFlags.some((f) => f.includes('复核')))

  return (
    <div>
      <div className="page-title">决策智能体 · Agent Console</div>
      <div className="page-desc">
        分层决策：装配约束 → 规范硬规则 → 缺陷矩阵先验 → RAG+LLM。LLM 仅输出策略，坐标由确定性算法计算。
        真实 LLM 由后端 /api/decide 提供。
      </div>

      {decisions.length === 0 && (
        <Panel title="尚无决策">
          <div className="hint">请先在「钉位规划」页运行规划流水线，生成逐钉决策。</div>
        </Panel>
      )}

      {decisions.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 16 }}>
          <Panel title="逐钉决策列表" tag={`${decisions.length} 条 · 置信阈值 ${params.confThreshold}`}>
            <div className="scroll-x">
              <table>
                <thead>
                  <tr><th>钉位</th><th>动作</th><th>决策层</th><th>置信度</th><th>风险</th></tr>
                </thead>
                <tbody>
                  {decisions.map((d) => (
                    <tr key={d.nailId} style={{ cursor: 'pointer' }} onClick={() => setSelected(d)}>
                      <td className="mono">{d.nailId}</td>
                      <td><span className={'badge ' + ACTION_BADGE[d.action]}>{ACTION_LABEL[d.action]}</span></td>
                      <td><span className="badge badge-gray">{STAGE_LABEL[d.stage]}</span></td>
                      <td className="mono" style={{ color: d.confidence < params.confThreshold ? 'var(--red)' : 'var(--green)' }}>
                        {(d.confidence * 100).toFixed(0)}%
                      </td>
                      <td>
                        {d.riskFlags.length === 0 ? <span className="hint">—</span> : d.riskFlags.map((f) => (
                          <span key={f} className="badge badge-amber" style={{ marginRight: 4 }}>{f}</span>
                        ))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>

          <div>
            <Panel title="决策详情 (JSON)">
              {!selected ? (
                <div className="hint">点击左侧钉位查看决策 JSON 与引用。</div>
              ) : (
                <>
                  <div className="row spread" style={{ marginBottom: 10 }}>
                    <span className="mono">{selected.nailId}</span>
                    <span className={'badge ' + ACTION_BADGE[selected.action]}>{ACTION_LABEL[selected.action]}</span>
                  </div>
                  <div className="mono-block">
{JSON.stringify(
  {
    action: selected.action,
    target: { x: +selected.target.x.toFixed(1), y: +selected.target.y.toFixed(1) },
    reason: selected.reason,
    cited_rules: selected.citedCodes,
    confidence: selected.confidence,
    params: selected.params,
    risk_flags: selected.riskFlags,
    stage: selected.stage,
  },
  null,
  2,
)}
                  </div>
                </>
              )}
            </Panel>

            <Panel title="人工复核队列" tag={`${humanReview.length} 项`}>
              {humanReview.length === 0 ? (
                <div className="hint">无需人工复核的钉位。</div>
              ) : (
                humanReview.map((d) => (
                  <div className="row spread" key={d.nailId} style={{ marginBottom: 6 }}>
                    <span className="mono">{d.nailId}</span>
                    <span className="badge badge-amber">{d.riskFlags.join('/')}</span>
                  </div>
                ))
              )}
            </Panel>
          </div>
        </div>
      )}
    </div>
  )
}
