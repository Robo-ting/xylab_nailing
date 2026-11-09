import { Panel } from '../components/Panel'
import { useSystemStore } from '../store/useSystemStore'

const ACTION_BADGE: Record<string, string> = {
  NAIL: 'badge-green',
  PREDRILL_THEN_NAIL: 'badge-purple',
  RELOCATE: 'badge-amber',
  SKIP: 'badge-red',
}

export function LogsReports() {
  const { logs, plannedNails, defects, substrate, grainRelation, params } = useSystemStore()

  function download(filename: string, content: string, type = 'application/json') {
    const blob = new Blob([content], { type })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  function exportJson() {
    const report = {
      project: 'XYLab 预制竹木结构机械臂智能钉合',
      generatedAt: new Date().toISOString(),
      board: { substrate, grainRelation },
      params,
      defectCount: defects.length,
      nailCount: plannedNails.length,
      logs,
    }
    download('construction_log.json', JSON.stringify(report, null, 2))
  }

  function exportCsv() {
    const header = 'nailId,action,designX,designY,finalX,finalY,offset,compliant,reason\n'
    const rows = logs
      .map(
        (l) =>
          `${l.nailId},${l.action},${l.design.x.toFixed(1)},${l.design.y.toFixed(1)},${l.final.x.toFixed(1)},${l.final.y.toFixed(1)},${l.offset},${l.compliant},"${l.reason}"`,
      )
      .join('\n')
    download('construction_log.csv', header + rows, 'text/csv')
  }

  const compliant = logs.filter((l) => l.compliant).length

  return (
    <div>
      <div className="page-title">日志与报告 · Logs & Reports</div>
      <div className="page-desc">逐钉施工日志、决策原因与规范引用；支持导出 JSON / CSV 施工报告。</div>

      <div className="stat-grid" style={{ marginBottom: 16 }}>
        <div className="stat-card"><div className="num">{logs.length}</div><div className="lbl">日志条数</div></div>
        <div className="stat-card"><div className="num" style={{ color: 'var(--green)' }}>{compliant}</div><div className="lbl">合规钉位</div></div>
        <div className="stat-card"><div className="num" style={{ color: 'var(--red)' }}>{logs.length - compliant}</div><div className="lbl">跳过/不合规</div></div>
        <div className="stat-card"><div className="num" style={{ color: 'var(--amber)' }}>{logs.filter((l) => l.offset > 0.5).length}</div><div className="lbl">偏移钉位</div></div>
      </div>

      <Panel
        title="施工日志"
        tag={
          <span className="row" style={{ gap: 8 }}>
            <button className="btn btn-sm" onClick={exportJson} disabled={logs.length === 0}>导出 JSON</button>
            <button className="btn btn-sm" onClick={exportCsv} disabled={logs.length === 0}>导出 CSV</button>
          </span>
        }
      >
        {logs.length === 0 ? (
          <div className="hint">请先运行规划流水线生成日志。</div>
        ) : (
          <div className="scroll-x">
            <table>
              <thead>
                <tr>
                  <th>钉位</th><th>动作</th><th>设计坐标</th><th>最终坐标</th><th>偏移</th><th>合规</th><th>引用</th><th>原因</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((l) => (
                  <tr key={l.nailId}>
                    <td className="mono">{l.nailId}</td>
                    <td><span className={'badge ' + ACTION_BADGE[l.action]}>{l.action}</span></td>
                    <td className="mono">{l.design.x.toFixed(0)}, {l.design.y.toFixed(0)}</td>
                    <td className="mono">{l.final.x.toFixed(0)}, {l.final.y.toFixed(0)}</td>
                    <td className="mono">{l.offset} mm</td>
                    <td>{l.compliant ? <span className="badge badge-green">✓</span> : <span className="badge badge-red">✗</span>}</td>
                    <td className="hint">{l.citedCodes.join('; ')}</td>
                    <td className="hint" style={{ maxWidth: 280 }}>{l.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  )
}
