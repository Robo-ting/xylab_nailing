import { NavLink } from 'react-router-dom'

interface NavDef {
  to: string
  label: string
  ico: string
  idx: string
}

const GROUPS: { title: string; items: NavDef[] }[] = [
  {
    title: '总览',
    items: [{ to: '/', label: '总控台', ico: '◉', idx: '01' }],
  },
  {
    title: '感知与规划',
    items: [
      { to: '/calibration', label: '装配标定', ico: '▤', idx: '02' },
      { to: '/perception', label: '感知检测', ico: '◎', idx: '03' },
      { to: '/intake', label: '钉位扫描', ico: '▣', idx: '04' },
      { to: '/planning', label: '选区检测', ico: '⊹', idx: '05' },
    ],
  },
  {
    title: '决策',
    items: [
      { to: '/rulebase', label: '规范规则库', ico: '❏', idx: '06' },
      { to: '/matrix', label: '决策矩阵', ico: '▦', idx: '07' },
      { to: '/agent', label: '决策智能体', ico: '✦', idx: '08' },
    ],
  },
  {
    title: '执行与产出',
    items: [
      { to: '/robot', label: '机器人执行', ico: '⚙', idx: '09' },
      { to: '/twin', label: '数字孪生', ico: '◈', idx: '10' },
      { to: '/logs', label: '日志与报告', ico: '☰', idx: '11' },
    ],
  },
]

export function Sidebar() {
  return (
    <aside className="app-sidebar">
      <div className="brand">
        <div className="brand-mark" aria-hidden="true" />
        <div className="logo">XYLab</div>
        <div className="sub">预制竹木结构机械臂智能钉合控制系统</div>
      </div>
      <nav className="nav">
        {GROUPS.map((g) => (
          <div key={g.title}>
            <div className="nav-group-title">{g.title}</div>
            {g.items.map((it) => (
              <NavLink
                key={it.to}
                to={it.to}
                end={it.to === '/'}
                className={({ isActive }) => 'nav-item' + (isActive ? ' active' : '')}
              >
                <span className="ico">{it.ico}</span>
                <span>{it.label}</span>
                <span className="idx">{it.idx}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
    </aside>
  )
}
