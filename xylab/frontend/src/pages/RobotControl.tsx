import { useState } from 'react'
import { Panel } from '../components/Panel'
import { useSystemStore } from '../store/useSystemStore'
import type { NailAction, RobotState } from '../lib/types'

interface SkillDef {
  name: string
  group: string
  desc: string
  safety?: string
}

const SKILLS: SkillDef[] = [
  { name: 'skill_move_to', group: '执行', desc: '移动到目标点上方', safety: '碰撞检测+工作空间边界' },
  { name: 'skill_nail', group: '执行', desc: '下压打钉', safety: '须先 validate_decision' },
  { name: 'skill_predrill', group: '执行', desc: '预钻孔', safety: '钻头就位' },
  { name: 'skill_retract', group: '执行', desc: '抬升复位' },
  { name: 'skill_skip', group: '执行', desc: '跳过当前钉位' },
  { name: 'skill_emergency_stop', group: '安全', desc: '急停（最高优先级）' },
  { name: 'skill_detect_defects', group: '感知', desc: '缺陷检测' },
  { name: 'skill_scan_existing_nails', group: '感知', desc: '既有铁钉扫描' },
  { name: 'skill_build_cost_map', group: '决策', desc: '构建代价图/禁区' },
  { name: 'skill_find_optimal_position', group: '决策', desc: 'KD-tree 最近可行点' },
  { name: 'skill_log_decision', group: '记录', desc: '写施工日志' },
  { name: 'skill_generate_report', group: '记录', desc: '生成 JSON/PDF 报告' },
]

const ACTION_SEQ: Record<NailAction, string[]> = {
  NAIL: ['move_to', 'nail', 'retract'],
  PREDRILL_THEN_NAIL: ['move_to', 'predrill', 'nail', 'retract'],
  RELOCATE: ['move_to(relocated)', 'nail', 'retract'],
  SKIP: ['skip', 'flag_for_human'],
}

export function RobotControl() {
  const { robotState, setRobotState, plannedNails, markStage } = useSystemStore()
  const [log, setLog] = useState<string[]>([])
  const [running, setRunning] = useState(false)

  function push(msg: string) {
    setLog((l) => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...l].slice(0, 200))
  }

  function setState(s: RobotState) {
    setRobotState(s)
    push(`状态 -> ${s}`)
  }

  async function executeAll() {
    if (plannedNails.length === 0) {
      push('无规划钉位，请先运行规划')
      return
    }
    setRunning(true)
    setState('SCANNING')
    await sleep(400)
    for (const n of plannedNails) {
      if (!n.action) continue
      const seq = ACTION_SEQ[n.action]
      for (const step of seq) {
        if (step.startsWith('move')) setState('MOVING')
        else if (step === 'nail') setState('NAILING')
        else if (step === 'predrill') setState('PREDRILL')
        push(`${n.id}: ${step}`)
        await sleep(120)
      }
    }
    setState('HOME')
    markStage('execute')
    setRunning(false)
    push('全部钉位执行完成')
  }

  const stateColor: Record<RobotState, string> = {
    HOME: 'var(--text-mute)',
    SCANNING: 'var(--accent)',
    MOVING: 'var(--amber)',
    NAILING: 'var(--green)',
    PREDRILL: 'var(--purple)',
    ESTOP: 'var(--red)',
  }

  return (
    <div>
      <div className="page-title">机器人执行 · Robot Control</div>
      <div className="page-desc">
        KUKA 机械臂技能原语（Skill）调度与状态机。真实执行经后端 ROS2 (MoveIt) 下发，当前为仿真时序。
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 16 }}>
        <div>
          <Panel title="状态机" tag="INIT / IDLE / TASK / SWITCHING / FAULT">
            <div className="row" style={{ gap: 12, marginBottom: 16 }}>
              <div
                style={{
                  width: 120,
                  height: 120,
                  borderRadius: '50%',
                  border: `4px solid ${stateColor[robotState]}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  fontSize: 18,
                  color: stateColor[robotState],
                  boxShadow: `0 0 24px ${stateColor[robotState]}55`,
                }}
              >
                {robotState}
              </div>
              <div style={{ flex: 1 }}>
                <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
                  <button className="btn btn-primary" onClick={executeAll} disabled={running}>
                    {running ? '执行中…' : '▶ 执行全部钉位'}
                  </button>
                  <button className="btn" onClick={() => setState('HOME')}>回 Home</button>
                  <button className="btn" onClick={() => setState('SCANNING')}>扫描</button>
                  <button className="btn btn-danger" onClick={() => setState('ESTOP')}>■ 急停</button>
                </div>
                <div className="hint" style={{ marginTop: 10 }}>
                  待执行钉位 {plannedNails.filter((n) => n.action !== 'SKIP').length} · 跳过 {plannedNails.filter((n) => n.action === 'SKIP').length}
                </div>
              </div>
            </div>
          </Panel>

          <Panel title="技能原语 (Skill Primitives)">
            <div className="grid-2">
              {SKILLS.map((s) => (
                <div key={s.name} className="stat-card" style={{ cursor: 'pointer' }} onClick={() => push(`调用 ${s.name}()`)}>
                  <div className="row spread">
                    <span className="mono" style={{ fontSize: 12 }}>{s.name}</span>
                    <span className="badge badge-gray">{s.group}</span>
                  </div>
                  <div className="hint" style={{ marginTop: 4 }}>{s.desc}</div>
                  {s.safety && <div className="hint" style={{ color: 'var(--amber)' }}>⚠ {s.safety}</div>}
                </div>
              ))}
            </div>
          </Panel>
        </div>

        <Panel title="执行日志" tag={`${log.length}`}>
          <div className="mono-block" style={{ height: 460, overflowY: 'auto' }}>
            {log.length === 0 ? '（等待执行）' : log.join('\n')}
          </div>
        </Panel>
      </div>
    </div>
  )
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}
