import { Fragment } from 'react'
import { useSystemStore, STAGES } from '../store/useSystemStore'

/** 顶部全流程状态条 */
export function PipelineBar() {
  const stageDone = useSystemStore((s) => s.stageDone)
  return (
    <div className="pipeline-bar">
      {STAGES.map((s, i) => (
        <Fragment key={s.key}>
          {i > 0 && <span className="pipe-arrow">→</span>}
          <div className={'pipe-step' + (stageDone[s.key] ? ' done' : '')}>
            <span className="dot" />
            {s.label}
          </div>
        </Fragment>
      ))}
    </div>
  )
}
