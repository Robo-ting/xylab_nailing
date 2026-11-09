import { useMemo, useState } from 'react'
import { Panel } from '../components/Panel'
import { BoardCanvas } from '../components/BoardCanvas'
import { useSystemStore } from '../store/useSystemStore'
import { DEFAULT_LAYERS, type Scene } from '../lib/render'
import { polygonIntersection, erodePolygon, polygonArea, maxInscribedDimension } from '../lib/geometry'
import { HAND_EYE } from '../mock/boards'

export function Calibration() {
  const { boards, pairs, boardWidth, boardHeight, markStage } = useSystemStore()
  const [showOverlap, setShowOverlap] = useState(true)

  // 计算重合区
  const overlaps = useMemo(() => {
    return pairs.map((pair) => {
      const upper = boards.find((b) => b.boardId === pair.upper)
      const lower = boards.find((b) => b.boardId === pair.lower)
      if (!upper || !lower) return { pair, region: [], eroded: [], area: 0, ok: false }
      const region = polygonIntersection(upper.polygon, lower.polygon)
      const eroded = erodePolygon(region, pair.minOverlap / 2)
      const area = polygonArea(region)
      const ok = maxInscribedDimension(region) >= pair.minOverlap
      return { pair, region, eroded, area: Math.round(area), ok }
    })
  }, [boards, pairs])

  const overlapBoards = useMemo(() => {
    if (!showOverlap) return boards
    // 把重合区作为一个"板"叠加显示
    const extra = overlaps
      .filter((o) => o.region.length >= 3)
      .map((o, i) => ({
        boardId: '重合区' + (i + 1),
        role: 'panel' as const,
        layer: 2,
        thickness: 0,
        polygon: o.region,
        color: '#22d3ee',
      }))
    return [...boards, ...extra]
  }, [boards, overlaps, showOverlap])

  const scene: Scene = {
    boardWidth,
    boardHeight,
    defects: [],
    rois: [],
    boards: overlapBoards,
    designNails: [],
    layers: { ...DEFAULT_LAYERS, boardOutline: true, boards: true, defects: false, designNails: false, rois: false },
  }

  const jsonPreview = JSON.stringify(
    {
      coordinate_frame: 'robot_base',
      unit: 'mm',
      boards: boards.map((b) => ({
        board_id: b.boardId,
        role: b.role,
        layer: b.layer,
        thickness: b.thickness,
        polygon: b.polygon.map((p) => [p.x, p.y]),
      })),
      nailing_pairs: pairs,
    },
    null,
    2,
  )

  return (
    <div>
      <div className="page-title">装配标定 · Calibration</div>
      <div className="page-desc">
        T 型节点板件人工标定（机器人基坐标系，俯视投影）。仅上下板重合区可钉合（Layer-0 装配约束）。
        手眼标定用于视觉系与机器人系对齐。
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16 }}>
        <Panel title="板件俯视图 + 重合区" tag="Top-view Projection">
          <div className="canvas-toolbar">
            <label className="checkbox-row">
              <input type="checkbox" checked={showOverlap} onChange={() => setShowOverlap(!showOverlap)} />
              显示重合区
            </label>
            <button className="btn btn-sm" onClick={() => markStage('input')}>确认标定</button>
          </div>
          <BoardCanvas scene={scene} width={760} height={500} mode="none" />
          <div className="legend" style={{ marginTop: 12 }}>
            <div className="item"><span className="swatch" style={{ background: '#a97142' }} />下层平板 (base)</div>
            <div className="item"><span className="swatch" style={{ background: '#c89968' }} />上层竖板 (vertical)</div>
            <div className="item"><span className="swatch" style={{ background: '#22d3ee' }} />可钉合重合区</div>
          </div>
        </Panel>

        <div>
          <Panel title="手眼标定 / 对齐">
            <div className="row spread"><span className="hint">尺度</span><span className="mono">{HAND_EYE.scale} mm/px</span></div>
            <div className="row spread"><span className="hint">旋转</span><span className="mono">{HAND_EYE.rotationDeg}°</span></div>
            <div className="row spread"><span className="hint">平移</span><span className="mono">({HAND_EYE.translation.x}, {HAND_EYE.translation.y})</span></div>
            <div className="divider" />
            <div className="row spread">
              <span className="hint">标记点对齐误差</span>
              <span className={'badge ' + (HAND_EYE.alignmentError <= 0.5 ? 'badge-green' : 'badge-red')}>
                {HAND_EYE.alignmentError} mm {HAND_EYE.alignmentError <= 0.5 ? '✓ ≤0.5' : '✗ 超差'}
              </span>
            </div>
          </Panel>

          <Panel title="钉合配对校验">
            {overlaps.map((o) => (
              <div key={o.pair.upper} style={{ marginBottom: 10 }}>
                <div className="row spread">
                  <span>{o.pair.upper} → {o.pair.lower}</span>
                  <span className={'badge ' + (o.ok ? 'badge-green' : 'badge-red')}>
                    {o.ok ? '搭接足够' : '搭接不足'}
                  </span>
                </div>
                <div className="hint">
                  重合面积 {o.area} mm² · 最小搭接要求 {o.pair.minOverlap} mm
                </div>
              </div>
            ))}
          </Panel>
        </div>
      </div>

      <Panel title="标定文件 (assembly_T_joint.json)" tag="可上传替换">
        <div className="mono-block">{jsonPreview}</div>
      </Panel>
    </div>
  )
}
