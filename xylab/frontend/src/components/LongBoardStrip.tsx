import { useState, type MouseEvent } from 'react'
import type { IntakeIrHit, IntakeStation } from '../api/intake'

interface LongBoardStripProps {
  lengthMm: number
  spacingMm: number
  stations: IntakeStation[]
  irHits: IntakeIrHit[]
  selectedId: string | null
  onAdd: (xMm: number) => void
  onSelect: (id: string) => void
}

/** 把点击位置吸到间距的整数倍。间距 50 时，50 附近落到 50，100 附近落到 100。 */
export function snapNailMm(xMm: number, spacingMm: number, lengthMm: number): number {
  const spacing = Math.max(1, spacingMm)
  const snapped = Math.round(xMm / spacing) * spacing
  return Math.max(0, Math.min(lengthMm, snapped))
}

/** 长板条：点击板面添加钉位，按间距吸附。红外结果标在对应毫米位置。 */
export function LongBoardStrip({ lengthMm, spacingMm, stations, irHits, selectedId, onAdd, onSelect }: LongBoardStripProps) {
  const [hoverMm, setHoverMm] = useState<number | null>(null)
  const ticks = snapTicks(lengthMm, spacingMm)
  const ordered = stations.slice().sort((a, b) => a.xMm - b.xMm)

  function xFromEvent(event: MouseEvent<HTMLDivElement>): number {
    const rect = event.currentTarget.getBoundingClientRect()
    const ratio = (event.clientX - rect.left) / Math.max(rect.width, 1)
    const raw = Math.max(0, Math.min(1, ratio)) * lengthMm
    return snapNailMm(raw, spacingMm, lengthMm)
  }

  function addAt(event: MouseEvent<HTMLDivElement>) {
    onAdd(xFromEvent(event))
  }

  return (
    <div>
      <div className="hint" style={{ marginBottom: 8 }}>
        点击板面设置钉位，会吸到 {spacingMm} mm 的整数倍。橙点是红外返回的位置。
        {hoverMm !== null ? ` 当前吸附 ${hoverMm} mm` : ''}
      </div>
      <div
        className="long-board"
        onClick={addAt}
        onMouseMove={(event) => setHoverMm(xFromEvent(event))}
        onMouseLeave={() => setHoverMm(null)}
      >
        <div className="long-board-face" />
        {ticks.map((tick) => (
          <span key={tick} className="long-board-tick" style={{ left: `${(tick / lengthMm) * 100}%` }} />
        ))}
        {hoverMm !== null && (
          <span className="long-board-hover" style={{ left: `${(hoverMm / lengthMm) * 100}%` }} />
        )}
        {ordered.slice(0, -1).map((station, index) => {
          const next = ordered[index + 1]
          const mid = (station.xMm + next.xMm) / 2
          const gap = Math.round(next.xMm - station.xMm)
          return (
            <span key={`${station.id}-${next.id}`} className="long-board-gap" style={{ left: `${(mid / lengthMm) * 100}%` }}>
              {gap}
            </span>
          )
        })}
        {irHits.map((hit) => (
          <span
            key={hit.id}
            className="long-board-ir"
            style={{ left: `${(hit.xMm / lengthMm) * 100}%` }}
            title={hit.note}
          />
        ))}
        {stations.map((station) => (
          <button
            key={station.id}
            type="button"
            className={'long-board-nail' + (station.id === selectedId ? ' active' : '') + (station.photo ? ' scanned' : '')}
            style={{ left: `${(station.xMm / lengthMm) * 100}%` }}
            onClick={(event) => {
              event.stopPropagation()
              onSelect(station.id)
            }}
          >
            {station.id}
          </button>
        ))}
      </div>
      <div className="long-board-scale">
        <span>0</span>
        <span>{Math.round(lengthMm / 2)} mm</span>
        <span>{lengthMm} mm</span>
      </div>
    </div>
  )
}

function snapTicks(lengthMm: number, spacingMm: number): number[] {
  const spacing = Math.max(1, spacingMm)
  const count = Math.floor(lengthMm / spacing)
  const stride = Math.max(1, Math.ceil((count + 1) / 60))
  const ticks: number[] = []
  for (let i = 0; i <= count; i += stride) ticks.push(i * spacing)
  if (ticks[ticks.length - 1] !== count * spacing) ticks.push(count * spacing)
  return ticks
}
