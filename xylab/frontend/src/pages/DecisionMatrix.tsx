import { useState } from 'react'
import { Panel } from '../components/Panel'
import { DEFECT_DECISION_MATRIX } from '../lib/decision'
import { DEFECT_META } from '../mock/defects'
import { computeEC5, embeddingStrength, withdrawalStrength } from '../lib/ec5'

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

const SUBSTRATE_RULES = [
  { substrate: '重竹', grain: '顺纹', risk: '极高', strategy: '强制预钻孔，孔径≈0.8d，可斜向打入' },
  { substrate: '重竹', grain: '横纹', risk: '中', strategy: '可直接打钉' },
  { substrate: '重竹', grain: '斜纹', risk: '高', strategy: '建议预钻' },
  { substrate: '松木', grain: '顺纹', risk: '中', strategy: '边距不足时预钻' },
  { substrate: '松木', grain: '横纹', risk: '低', strategy: '直接打钉' },
]

export function DecisionMatrix() {
  const [d, setD] = useState(3.1)
  const [rho, setRho] = useState(410)
  const [alpha, setAlpha] = useState(0)
  const [predrill, setPredrill] = useState(false)

  const ec5 = computeEC5({ d, rhoK: rho, alphaDeg: alpha, predrilled: predrill })

  return (
    <div>
      <div className="page-title">决策矩阵 · Decision Matrix</div>
      <div className="page-desc">
        缺陷 × 基材 × 纹理决策矩阵，为 LLM 提供确定性专业先验；EC5 边距/端距/间距在线计算。
      </div>

      <Panel title="缺陷决策矩阵" tag="Defect × Action">
        <div className="scroll-x">
          <table>
            <thead>
              <tr>
                <th>缺陷类型</th>
                <th>默认策略</th>
                <th>附加安全距 (mm)</th>
                <th>说明</th>
              </tr>
            </thead>
            <tbody>
              {DEFECT_DECISION_MATRIX.map((r) => (
                <tr key={r.type}>
                  <td>
                    <span className="badge" style={{ background: DEFECT_META[r.type].color + '33', color: DEFECT_META[r.type].color }}>
                      {r.label}
                    </span>
                  </td>
                  <td><span className={'badge ' + ACTION_BADGE[r.defaultAction]}>{ACTION_LABEL[r.defaultAction]}</span></td>
                  <td className="mono">+{r.extraSafeDist}</td>
                  <td className="hint">{r.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <div className="grid-2">
        <Panel title="基材 × 纹理 修正层">
          <div className="scroll-x">
            <table>
              <thead>
                <tr><th>基材</th><th>纹理</th><th>劈裂风险</th><th>策略</th></tr>
              </thead>
              <tbody>
                {SUBSTRATE_RULES.map((r, i) => (
                  <tr key={i}>
                    <td>{r.substrate}</td>
                    <td>{r.grain}</td>
                    <td>
                      <span className={'badge ' + (r.risk === '极高' || r.risk === '高' ? 'badge-red' : r.risk === '中' ? 'badge-amber' : 'badge-green')}>{r.risk}</span>
                    </td>
                    <td className="hint">{r.strategy}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Eurocode 5 间距计算器" tag="EN 1995-1-1 Table 8.2">
          <div className="grid-2">
            <div className="field">
              <label>钉径 d (mm)</label>
              <input type="number" value={d} step={0.1} onChange={(e) => setD(Number(e.target.value))} />
            </div>
            <div className="field">
              <label>特征密度 ρk (kg/m³)</label>
              <input type="number" value={rho} onChange={(e) => setRho(Number(e.target.value))} />
            </div>
            <div className="field">
              <label>纹理角 α (°)</label>
              <input type="number" value={alpha} onChange={(e) => setAlpha(Number(e.target.value))} />
            </div>
            <div className="field">
              <label>是否预钻孔</label>
              <div className="pill-toggle">
                <button className={!predrill ? 'active' : ''} onClick={() => setPredrill(false)}>未预钻</button>
                <button className={predrill ? 'active' : ''} onClick={() => setPredrill(true)}>预钻</button>
              </div>
            </div>
          </div>
          <div className="divider" />
          <table>
            <tbody>
              <tr><td>顺纹间距 a₁</td><td className="mono">{ec5.a1} mm</td><td>横纹间距 a₂</td><td className="mono">{ec5.a2} mm</td></tr>
              <tr><td>受荷端距 a₃,t</td><td className="mono">{ec5.a3t} mm</td><td>无荷端距 a₃,c</td><td className="mono">{ec5.a3c} mm</td></tr>
              <tr><td>受荷边距 a₄,t</td><td className="mono">{ec5.a4t} mm</td><td>无荷边距 a₄,c</td><td className="mono">{ec5.a4c} mm</td></tr>
            </tbody>
          </table>
          <div className="divider" />
          <div className="row spread"><span className="hint">嵌入强度 f_h,k</span><span className="mono">{embeddingStrength(d, rho)} MPa</span></div>
          <div className="row spread"><span className="hint">钢钉轴向拔出 f_ax,k</span><span className="mono">{withdrawalStrength(rho)} MPa</span></div>
          <div className="row spread"><span className="hint">推荐最小边距</span><span className="badge badge-blue">{ec5.minEdge} mm</span></div>
        </Panel>
      </div>
    </div>
  )
}
