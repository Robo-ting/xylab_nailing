import { useMemo, useState } from 'react'
import { Panel } from '../components/Panel'
import { BoardCanvas } from '../components/BoardCanvas'
import { SliderField } from '../components/Field'
import { useSystemStore } from '../store/useSystemStore'
import { DEFECT_META } from '../mock/defects'
import { detectDefects } from '../api/client'
import { DEFAULT_LAYERS, type Scene } from '../lib/render'
import type { DefectType } from '../lib/types'

const ALL_TYPES = Object.keys(DEFECT_META) as DefectType[]

export function Perception() {
  const {
    defects,
    setDefects,
    detectionSource,
    enabledTypes,
    toggleType,
    confFilter,
    setConfFilter,
    boardWidth,
    boardHeight,
    substrate,
    setSubstrate,
    grainRelation,
    setGrainRelation,
    markStage,
    rois,
  } = useSystemStore()
  const [loading, setLoading] = useState(false)

  const scene: Scene = useMemo(
    () => ({
      boardWidth,
      boardHeight,
      defects,
      rois,
      boards: [],
      designNails: [],
      layers: { ...DEFAULT_LAYERS, designNails: false, rois: false },
      enabledTypes,
      confFilter,
    }),
    [defects, enabledTypes, confFilter, boardWidth, boardHeight, rois],
  )

  const visible = defects.filter(
    (d) => enabledTypes.has(d.type) && d.confidence >= confFilter,
  )

  async function runDetect() {
    setLoading(true)
    const res = await detectDefects('sample_board.jpg')
    setDefects(res.defects, res.source)
    markStage('input')
    markStage('detect')
    setLoading(false)
  }

  const counts = ALL_TYPES.map((t) => ({
    t,
    n: defects.filter((d) => d.type === t).length,
  }))

  return (
    <div>
      <div className="page-title">感知检测 · Perception</div>
      <div className="page-desc">
        YOLOv8-seg 木材缺陷分割检测（7 类）+ 铁钉扫描 + 木纹/基材分析。真实模型由后端
        /api/detect 提供，当前为{detectionSource === 'backend' ? '后端' : '模拟'}数据。
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 16 }}>
        <Panel
          title="检测结果可视化"
          tag={`${visible.length} / ${defects.length} 显示`}
        >
          <div className="canvas-toolbar">
            <button className="btn btn-primary btn-sm" onClick={runDetect} disabled={loading}>
              {loading ? '检测中…' : '▶ 运行缺陷检测'}
            </button>
            <span className="badge badge-blue">
              相机 5MP · 2448×2048 · 0.25 mm/px
            </span>
          </div>
          <BoardCanvas scene={scene} width={760} height={500} mode="none" />
          <div className="legend" style={{ marginTop: 12 }}>
            {ALL_TYPES.map((t) => (
              <div className="item" key={t}>
                <span className="swatch" style={{ background: DEFECT_META[t].color }} />
                {DEFECT_META[t].label}
              </div>
            ))}
          </div>
        </Panel>

        <div>
          <Panel title="检测类别开关">
            {ALL_TYPES.map((t) => (
              <label className="checkbox-row" key={t} style={{ marginBottom: 8 }}>
                <input
                  type="checkbox"
                  checked={enabledTypes.has(t)}
                  onChange={() => toggleType(t)}
                />
                <span className="swatch" style={{ width: 12, height: 12, borderRadius: 3, background: DEFECT_META[t].color }} />
                <span style={{ flex: 1 }}>
                  {DEFECT_META[t].label}
                  <span className="hint"> · {DEFECT_META[t].en}</span>
                </span>
                <span className="badge badge-gray">
                  {counts.find((c) => c.t === t)?.n ?? 0}
                </span>
              </label>
            ))}
          </Panel>

          <Panel title="置信度阈值">
            <SliderField
              label="最小置信度"
              value={confFilter}
              min={0}
              max={1}
              step={0.05}
              onChange={setConfFilter}
            />
            <div className="hint">低于阈值的检测将被过滤，不参与后续禁区构建。</div>
          </Panel>

          <Panel title="基材 / 木纹分析">
            <div className="field">
              <label>基材（树种）</label>
              <select value={substrate} onChange={(e) => setSubstrate(e.target.value)}>
                <option value="重竹">重竹</option>
                <option value="松木">松木</option>
                <option value="杉木">杉木</option>
                <option value="胶合板">胶合板</option>
              </select>
            </div>
            <div className="field">
              <label>木纹关系</label>
              <div className="pill-toggle">
                {(['顺纹', '横纹', '斜纹'] as const).map((g) => (
                  <button
                    key={g}
                    className={grainRelation === g ? 'active' : ''}
                    onClick={() => setGrainRelation(g)}
                  >
                    {g}
                  </button>
                ))}
              </div>
            </div>
            <div className="hint">
              重竹顺纹劈裂风险极高，决策时将触发强制预钻孔。
            </div>
          </Panel>
        </div>
      </div>

      <Panel title="检测明细" tag="Detection Table">
        <div className="scroll-x">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>类型</th>
                <th>置信度</th>
                <th>面积 (mm²)</th>
                <th>包围盒 (x,y,w,h)</th>
                <th>严重度</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((d) => (
                <tr key={d.id}>
                  <td className="mono">{d.id}</td>
                  <td>
                    <span className="badge" style={{ background: DEFECT_META[d.type].color + '33', color: DEFECT_META[d.type].color }}>
                      {DEFECT_META[d.type].label}
                    </span>
                  </td>
                  <td className="mono">{(d.confidence * 100).toFixed(0)}%</td>
                  <td className="mono">{d.area}</td>
                  <td className="mono">
                    {d.bbox.map((v) => v.toFixed(0)).join(', ')}
                  </td>
                  <td>
                    <span className={'badge ' + (d.severity === 'severe' ? 'badge-red' : d.severity === 'moderate' ? 'badge-amber' : 'badge-gray')}>
                      {d.severity === 'severe' ? '严重' : d.severity === 'moderate' ? '中等' : '轻微'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  )
}
