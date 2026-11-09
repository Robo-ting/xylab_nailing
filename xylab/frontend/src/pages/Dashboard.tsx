import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Panel } from '../components/Panel'
import { BoardCanvas } from '../components/BoardCanvas'
import { useSystemStore, STAGES } from '../store/useSystemStore'
import { runPipeline } from '../lib/pipeline'
import { DEFAULT_LAYERS, type Scene } from '../lib/render'

export function Dashboard() {
  const store = useSystemStore()
  const nav = useNavigate()
  const {
    defects,
    rois,
    boardWidth,
    boardHeight,
    designNails,
    params,
    substrate,
    grainRelation,
    plannedNails,
    decisions,
    stageDone,
    setDesignNails,
    setPlanning,
    setLogs,
    markStage,
  } = store

  const scene: Scene = useMemo(
    () => ({
      boardWidth,
      boardHeight,
      defects,
      rois,
      boards: [],
      designNails: plannedNails.length ? plannedNails : designNails,
      layers: { ...DEFAULT_LAYERS, finalNails: plannedNails.length > 0, rois: true },
      enabledTypes: store.enabledTypes,
      confFilter: store.confFilter,
    }),
    [boardWidth, boardHeight, defects, rois, plannedNails, designNails, store.enabledTypes, store.confFilter],
  )

  function runAll() {
    const filtered = defects.filter(
      (d) => store.enabledTypes.has(d.type) && d.confidence >= store.confFilter,
    )
    const res = runPipeline({
      boardWidth,
      boardHeight,
      defects: filtered,
      rois,
      designNails,
      params,
      substrate,
      grainRelation,
    })
    setDesignNails(res.nails)
    setPlanning(res.nails, res.decisions)
    setLogs(res.logs)
    STAGES.forEach((s) => markStage(s.key))
  }

  const total = plannedNails.length || designNails.length
  const skipped = plannedNails.filter((n) => n.action === 'SKIP').length
  const relocated = plannedNails.filter((n) => n.status === 'relocated').length
  const doneCount = Object.values(stageDone).filter(Boolean).length

  const modules = [
    { to: '/calibration', label: '装配标定', desc: 'T型节点重合区约束' },
    { to: '/perception', label: '感知检测', desc: 'YOLOv8-seg 7类缺陷' },
    { to: '/planning', label: '钉位规划', desc: 'ROI + 膨胀 + KD-tree' },
    { to: '/rulebase', label: '规范规则库', desc: 'Eurocode 5 RAG 检索' },
    { to: '/matrix', label: '决策矩阵', desc: '缺陷×基材×纹理' },
    { to: '/agent', label: '决策智能体', desc: '四类动作决策' },
    { to: '/robot', label: '机器人执行', desc: 'Skill 原语 + 状态机' },
    { to: '/twin', label: '数字孪生', desc: '上料→扫描→打钉' },
    { to: '/logs', label: '日志与报告', desc: '施工日志 JSON/报告' },
  ]

  return (
    <div>
      <div className="page-title">总控台 · Dashboard</div>
      <div className="page-desc">
        XYLab 预制竹木结构机械臂智能钉合控制系统 · 全流程一体化控制与监视
      </div>

      <div className="stat-grid" style={{ marginBottom: 16 }}>
        <div className="stat-card"><div className="num" style={{ color: 'var(--accent)' }}>{defects.length}</div><div className="lbl">检出缺陷</div></div>
        <div className="stat-card"><div className="num">{total}</div><div className="lbl">钉位总数</div></div>
        <div className="stat-card"><div className="num" style={{ color: 'var(--amber)' }}>{relocated}</div><div className="lbl">换位钉位</div></div>
        <div className="stat-card"><div className="num" style={{ color: 'var(--red)' }}>{skipped}</div><div className="lbl">跳过钉位</div></div>
        <div className="stat-card"><div className="num" style={{ color: 'var(--green)' }}>{doneCount}/{STAGES.length}</div><div className="lbl">流程完成</div></div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16 }}>
        <Panel title="全局板面视图" tag={plannedNails.length ? '已规划' : '待规划'}>
          <div className="canvas-toolbar">
            <button className="btn btn-primary btn-sm" onClick={runAll}>▶ 一键运行全流程</button>
            <button className="btn btn-sm" onClick={() => nav('/planning')}>进入规划页</button>
          </div>
          <BoardCanvas scene={scene} width={780} height={480} mode="none" />
        </Panel>

        <div>
          <Panel title="流程状态">
            {STAGES.map((s) => (
              <div className="row spread" key={s.key} style={{ marginBottom: 8 }}>
                <span>
                  <span
                    className="status-dot"
                    style={{ background: stageDone[s.key] ? 'var(--green)' : 'var(--text-mute)' }}
                  />
                  {s.label}
                </span>
                <span className={'badge ' + (stageDone[s.key] ? 'badge-green' : 'badge-gray')}>
                  {stageDone[s.key] ? '完成' : '待处理'}
                </span>
              </div>
            ))}
          </Panel>
          <Panel title="决策概览">
            {decisions.length === 0 ? (
              <div className="hint">运行流程后显示各钉位决策摘要。</div>
            ) : (
              <div className="hint">
                共 {decisions.length} 条决策，其中跳过 {skipped}、换位 {relocated}。
                详见决策智能体与日志页。
              </div>
            )}
          </Panel>
        </div>
      </div>

      <Panel title="功能模块导航">
        <div className="grid-3">
          {modules.map((m) => (
            <div
              key={m.to}
              className="stat-card module-card"
              onClick={() => nav(m.to)}
            >
              <div style={{ fontWeight: 600, marginBottom: 4 }}>{m.label}</div>
              <div className="lbl">{m.desc}</div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}
