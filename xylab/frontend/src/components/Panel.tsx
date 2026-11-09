import type { ReactNode } from 'react'

interface PanelProps {
  title?: ReactNode
  tag?: ReactNode
  children: ReactNode
  style?: React.CSSProperties
}

/** 通用信息面板容器 */
export function Panel({ title, tag, children, style }: PanelProps) {
  return (
    <div className="panel" style={style}>
      {title && (
        <div className="panel-title">
          {title}
          {tag && <span className="tag">{tag}</span>}
        </div>
      )}
      {children}
    </div>
  )
}
