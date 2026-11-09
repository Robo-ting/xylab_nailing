import { useEffect, useRef, useState } from 'react'
import { Panel } from '../components/Panel'
import { useSystemStore } from '../store/useSystemStore'

type Phase = 'idle' | 'upload' | 'scan' | 'nailing' | 'done'

const PHASE_LABEL: Record<Phase, string> = {
  idle: '待机',
  upload: '上料',
  scan: '扫描',
  nailing: '打钉',
  done: '完成',
}

export function DigitalTwin() {
  const { plannedNails, boardWidth, boardHeight, markStage } = useSystemStore()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [phase, setPhase] = useState<Phase>('idle')
  const [playing, setPlaying] = useState(false)
  const stateRef = useRef({ t: 0, phase: 'idle' as Phase, nailIdx: 0 })

  useEffect(() => {
    let raf = 0
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    const W = canvas.width
    const H = canvas.height

    const render = () => {
      const st = stateRef.current
      ctx.clearRect(0, 0, W, H)
      // 背景
      ctx.fillStyle = '#0a0f1c'
      ctx.fillRect(0, 0, W, H)
      // 传送带
      ctx.fillStyle = '#1b2947'
      ctx.fillRect(0, H - 60, W, 60)
      for (let x = ((st.t * 2) % 40) - 40; x < W; x += 40) {
        ctx.strokeStyle = '#33436e'
        ctx.beginPath()
        ctx.moveTo(x, H - 60)
        ctx.lineTo(x + 20, H)
        ctx.stroke()
      }

      // 板面位置
      const boardW = 360
      const boardH = 240
      const bx0 = -boardW - 20
      const bxTarget = (W - boardW) / 2
      let bx = bxTarget
      if (st.phase === 'upload') {
        const p = Math.min(1, st.t / 90)
        bx = bx0 + (bxTarget - bx0) * easeOut(p)
      } else if (st.phase === 'idle') {
        bx = bx0
      }
      const by = 90

      // 板
      ctx.fillStyle = '#2a1e12'
      ctx.fillRect(bx, by, boardW, boardH)
      ctx.strokeStyle = '#5a4632'
      ctx.lineWidth = 2
      ctx.strokeRect(bx, by, boardW, boardH)
      // 木纹
      ctx.strokeStyle = '#3a2b1c'
      ctx.lineWidth = 1
      for (let y = 15; y < boardH; y += 20) {
        ctx.beginPath()
        for (let x = 0; x <= boardW; x += 8) {
          const yy = by + y + Math.sin((x / boardW) * 9 + y) * 3
          if (x === 0) ctx.moveTo(bx + x, yy)
          else ctx.lineTo(bx + x, yy)
        }
        ctx.stroke()
      }

      const sx = boardW / boardWidth
      const sy = boardH / boardHeight

      // 缺陷 + 钉位（板到位后）
      if (st.phase === 'scan' || st.phase === 'nailing' || st.phase === 'done') {
        // 扫描线
        if (st.phase === 'scan') {
          const scanX = bx + ((st.t % 120) / 120) * boardW
          ctx.strokeStyle = 'rgba(56,189,248,0.8)'
          ctx.lineWidth = 2
          ctx.beginPath()
          ctx.moveTo(scanX, by)
          ctx.lineTo(scanX, by + boardH)
          ctx.stroke()
          ctx.fillStyle = 'rgba(56,189,248,0.08)'
          ctx.fillRect(bx, by, scanX - bx, boardH)
        }
        // 钉位
        plannedNails.forEach((n, i) => {
          if (!n.final || !n.action) return
          const px = bx + n.final.x * sx
          const py = by + n.final.y * sy
          const placed = st.phase === 'done' || (st.phase === 'nailing' && i <= st.nailIdx)
          if (n.action === 'SKIP') {
            ctx.strokeStyle = '#ef4444'
            ctx.lineWidth = 1.5
            ctx.beginPath()
            ctx.moveTo(px - 4, py - 4)
            ctx.lineTo(px + 4, py + 4)
            ctx.moveTo(px + 4, py - 4)
            ctx.lineTo(px - 4, py + 4)
            ctx.stroke()
          } else if (placed) {
            ctx.fillStyle = n.action === 'PREDRILL_THEN_NAIL' ? '#8b5cf6' : n.action === 'RELOCATE' ? '#f59e0b' : '#22c55e'
            ctx.beginPath()
            ctx.arc(px, py, 4, 0, Math.PI * 2)
            ctx.fill()
          } else {
            ctx.strokeStyle = '#93c5fd'
            ctx.lineWidth = 1
            ctx.beginPath()
            ctx.arc(px, py, 3, 0, Math.PI * 2)
            ctx.stroke()
          }
        })
        // 机械臂末端（打钉阶段）
        if (st.phase === 'nailing' && plannedNails[st.nailIdx]?.final) {
          const n = plannedNails[st.nailIdx]
          const px = bx + n.final!.x * sx
          const py = by + n.final!.y * sy
          const impact = Math.abs(Math.sin(st.t * 0.4)) * 10
          ctx.strokeStyle = '#e6edf7'
          ctx.lineWidth = 4
          ctx.beginPath()
          ctx.moveTo(px, by - 60)
          ctx.lineTo(px, py - 12 - impact)
          ctx.stroke()
          ctx.fillStyle = '#38bdf8'
          ctx.beginPath()
          ctx.arc(px, py - 8 - impact, 5, 0, Math.PI * 2)
          ctx.fill()
        }
      }

      // 阶段标题
      ctx.fillStyle = '#e6edf7'
      ctx.font = 'bold 16px sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText(`阶段：${PHASE_LABEL[st.phase]}`, 16, 28)

      // 推进时间线
      if (playing) {
        st.t += 1
        advance(st)
      }
      setPhase(st.phase)
      raf = requestAnimationFrame(render)
    }
    raf = requestAnimationFrame(render)
    return () => cancelAnimationFrame(raf)
  }, [playing, plannedNails, boardWidth, boardHeight])

  function advance(st: { t: number; phase: Phase; nailIdx: number }) {
    const validNails = plannedNails.filter((n) => n.action && n.action !== 'SKIP')
    if (st.phase === 'upload' && st.t > 90) {
      st.phase = 'scan'
      st.t = 0
    } else if (st.phase === 'scan' && st.t > 120) {
      st.phase = 'nailing'
      st.t = 0
      st.nailIdx = 0
    } else if (st.phase === 'nailing') {
      if (st.t > 20) {
        st.t = 0
        st.nailIdx += 1
        if (st.nailIdx >= plannedNails.length) {
          st.phase = 'done'
          markStage('execute')
          setPlaying(false)
        }
      }
    }
    void validNails
  }

  function start() {
    if (plannedNails.length === 0) return
    stateRef.current = { t: 0, phase: 'upload', nailIdx: 0 }
    setPlaying(true)
  }

  return (
    <div>
      <div className="page-title">数字孪生 · Digital Twin</div>
      <div className="page-desc">
        全流程 2D 仿真演示：上料 → S 形扫描 → 逐钉打钉。对应 RoboDK / ROS2 Gazebo 数字孪生方案。
      </div>

      <Panel title="仿真演示" tag={`钉位 ${plannedNails.length} · ${PHASE_LABEL[phase]}`}>
        <div className="canvas-toolbar">
          <button className="btn btn-primary btn-sm" onClick={start} disabled={plannedNails.length === 0}>▶ 开始演示</button>
          <button className="btn btn-sm" onClick={() => setPlaying((p) => !p)}>{playing ? '⏸ 暂停' : '▶ 继续'}</button>
          <button className="btn btn-sm" onClick={() => { stateRef.current = { t: 0, phase: 'idle', nailIdx: 0 }; setPlaying(false) }}>⟲ 重置</button>
          {plannedNails.length === 0 && <span className="hint" style={{ alignSelf: 'center' }}>请先在规划页生成钉位</span>}
        </div>
        <div className="canvas-wrap">
          <canvas ref={canvasRef} width={780} height={440} style={{ width: '100%' }} />
        </div>
        <div className="legend" style={{ marginTop: 12 }}>
          <div className="item"><span className="swatch" style={{ background: '#22c55e' }} />打钉完成</div>
          <div className="item"><span className="swatch" style={{ background: '#8b5cf6' }} />预钻</div>
          <div className="item"><span className="swatch" style={{ background: '#f59e0b' }} />换位</div>
          <div className="item"><span className="swatch" style={{ background: '#ef4444' }} />跳过</div>
          <div className="item"><span className="swatch" style={{ background: '#38bdf8' }} />扫描线</div>
        </div>
      </Panel>

      <div className="grid-3">
        <Panel title="方案 A · RoboDK"><div className="hint">路径 demo 视频，Upload/Scan/Nailing 三段 Program，KUKA KR10。周期 1-2 天。</div></Panel>
        <Panel title="方案 B · ROS2 Gazebo"><div className="hint">MoveIt! + RViz2，nail_publisher/nail_executor 节点，/nail_targets PoseArray。周期 4-6 周。</div></Panel>
        <Panel title="流程动画"><div className="hint">Python matplotlib 18s 1080p H.264，答辩演示视频。</div></Panel>
      </div>
    </div>
  )
}

function easeOut(x: number): number {
  return 1 - Math.pow(1 - x, 3)
}
