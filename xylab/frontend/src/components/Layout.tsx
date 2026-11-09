import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { PipelineBar } from './PipelineBar'
import { useSystemStore } from '../store/useSystemStore'

export function Layout() {
  const robotState = useSystemStore((s) => s.robotState)
  const source = useSystemStore((s) => s.detectionSource)
  const stateColor: Record<string, string> = {
    HOME: 'var(--text-mute)',
    SCANNING: 'var(--accent)',
    MOVING: 'var(--amber)',
    NAILING: 'var(--green)',
    PREDRILL: 'var(--purple)',
    ESTOP: 'var(--red)',
  }
  return (
    <div className="app">
      <Sidebar />
      <header className="app-header">
        <PipelineBar />
        <div className="header-status">
          <span className="status-chip">
            <span className="status-dot" style={{ background: source === 'backend' ? 'var(--green)' : 'var(--amber)' }} />
            {source === 'backend' ? '后端在线' : '模拟数据'}
          </span>
          <span className="status-chip">
            <span className="status-dot" style={{ background: stateColor[robotState] }} />
            机械臂 {robotState}
          </span>
        </div>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
