import { useState } from 'react'
import { Panel } from '../components/Panel'
import { LongBoardStrip, snapNailMm } from '../components/LongBoardStrip'
import { SliderField } from '../components/Field'
import {
  addIntakeStation,
  createIntakeBoard,
  gradeIntakeBoard,
  removeIntakeStation,
  resizeIntakeBoard,
  adviseStation,
  annotatedImageUrl,
  scanInfrared,
  scanStationPhoto,
  type IntakeBoard,
} from '../api/intake'

const DEFAULT_NAIL_PROMPT =
  '图中的红框是已经识别出的缺陷。请根据这些框和规则，说明离当前钉位最近、仍然符合规范的可钉位置该怎么选。只讲选择逻辑，不要把红框以外的东西当成缺陷。规则：死节、裂缝、腐朽及其外扩范围不能落钉；钉位只能落在给定间距的整数倍上；若当前位置落在禁区内，沿板长选择最近的一格，并说明为什么选这一侧。'

const DEFECT_LABEL: Record<string, string> = {
  knot_live: '活节',
  knot_dead: '死节',
  crack: '裂缝',
  decay: '腐朽',
  wormhole: '虫洞',
  nail_exposed: '外露钉帽',
  nail_rusted: '锈蚀钉帽',
}

export function Intake() {
  const [lengthMm, setLengthMm] = useState(2400)
  const [spacingMm, setSpacingMm] = useState(50)
  const [board, setBoard] = useState<IntakeBoard | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [simulateIr, setSimulateIr] = useState(true)
  const [prompt, setPrompt] = useState(DEFAULT_NAIL_PROMPT)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const selected = board?.stations.find((s) => s.id === selectedId) ?? null

  async function run(task: () => Promise<IntakeBoard>) {
    setBusy(true)
    setError(null)
    try {
      const next = await task()
      setBoard(next)
      return next
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      return null
    } finally {
      setBusy(false)
    }
  }

  async function ensureBoard(): Promise<IntakeBoard | null> {
    if (board) return board
    return run(() => createIntakeBoard(lengthMm, 200))
  }

  async function onAdd(xMm: number) {
    const snapped = snapNailMm(xMm, spacingMm, lengthMm)
    const current = board ?? (await ensureBoard())
    if (!current) return
    const existing = current.stations.find((station) => Math.abs(station.xMm - snapped) < 0.6)
    if (existing) {
      setSelectedId(existing.id)
      return
    }
    const next = await run(() => addIntakeStation(current.id, snapped))
    const added = next?.stations.find((station) => Math.abs(station.xMm - snapped) < 0.6)
    if (added) setSelectedId(added.id)
  }

  async function onLength(value: number) {
    setLengthMm(value)
    if (!board) return
    const next = await run(() => resizeIntakeBoard(board.id, value))
    if (next && selectedId && !next.stations.some((s) => s.id === selectedId)) setSelectedId(null)
  }

  async function onPhoto(file: File) {
    if (!board || !selected) {
      setError('先在长板上点一个钉位，再拍照')
      return
    }
    await run(() => scanStationPhoto(board.id, selected.id, file))
  }

  async function onScanSample() {
    setBusy(true)
    setError(null)
    try {
      let current = board ?? (await createIntakeBoard(lengthMm, 200))
      setBoard(current)
      const targetX = snapNailMm(current.lengthMm / 2, spacingMm, current.lengthMm)
      let station = current.stations.find((item) => item.id === selectedId)
        ?? current.stations.find((item) => Math.abs(item.xMm - targetX) < 0.6)
      if (!station) {
        current = await addIntakeStation(current.id, targetX)
        setBoard(current)
        station = current.stations.find((item) => Math.abs(item.xMm - targetX) < 0.6) ?? null
      }
      if (!station) throw new Error('没有钉位')
      setSelectedId(station.id)
      const res = await fetch('/samples/beech-board.jpg')
      if (!res.ok) throw new Error('样板照片读不到')
      const file = new File([await res.blob()], 'beech-board.jpg', { type: 'image/jpeg' })
      current = await scanStationPhoto(current.id, station.id, file)
      setBoard(current)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  async function onGrade() {
    const current = board ?? (await ensureBoard())
    if (!current) return
    await run(() => gradeIntakeBoard(current.id))
  }

  async function onAdvise() {
    if (!board || !selected) {
      setError('先在长板上点一个钉位')
      return
    }
    await run(() => adviseStation(board.id, selected.id, prompt, spacingMm))
  }

  async function onIr() {
    const current = board ?? (await ensureBoard())
    if (!current) return
    await run(() => scanInfrared(current.id, simulateIr))
  }

  return (
    <div>
      <div className="page-title">钉位扫描</div>
      <div className="page-desc">
        在长板上点出打钉位置，再对钉位拍照。定级和钉位说明都会请求后端，模型返回的文字出现在下面的输出区。
      </div>
      {error && <div className="badge badge-red" style={{ marginBottom: 12 }}>{error}</div>}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 300px', gap: 16, alignItems: 'start' }}>
        <div>
        <Panel title="长板" tag={board ? `${board.stations.length} 个钉位` : '未建板'}>
          <SliderField label="板长" value={lengthMm} min={600} max={6000} step={50} unit="mm" onChange={(v) => void onLength(v)} />
          <SliderField label="钉位间距" value={spacingMm} min={10} max={200} step={5} unit="mm" onChange={setSpacingMm} />
          <LongBoardStrip
            lengthMm={lengthMm}
            spacingMm={spacingMm}
            stations={board?.stations ?? []}
            irHits={board?.ir ?? []}
            selectedId={selectedId}
            onAdd={(x) => void onAdd(x)}
            onSelect={setSelectedId}
          />
        </Panel>
        <Panel title="模型输出" tag={busy ? '正在请求后端' : board?.grade?.grade || '尚未返回'} style={{ marginTop: 16 }}>
          {board?.grade ? (
            <>
              <div className="stat-card">
                <div className="num">{board.grade.grade}</div>
                <div className="lbl">
                  {board.grade.score} · {board.grade.grader === 'qwen' ? '模型' : board.grade.grader === 'ai' ? 'AI' : '规则兜底'}
                  {board.grade.reference ? ` · ${board.grade.reference}` : ''}
                </div>
              </div>
              {board.grade.reasons.map((reason, index) => (
                <div key={`${index}-${reason.slice(0, 12)}`} className="hint" style={{ marginTop: 8, whiteSpace: 'pre-wrap' }}>{reason}</div>
              ))}
              {board.grade.aiError && <div className="badge badge-red" style={{ marginTop: 8 }}>{board.grade.aiError}</div>}
            </>
          ) : (
            <div className="hint">点右侧「按榉木标准定级」。后端返回的等级和理由会显示在这里。</div>
          )}
          <div className="hint" style={{ marginTop: 14 }}>最近合规钉位</div>
          {selected?.advice ? (
            <div className="hint" style={{ marginTop: 6, whiteSpace: 'pre-wrap' }}>{selected.advice}</div>
          ) : (
            <div className="hint" style={{ marginTop: 6 }}>拍照后点「让模型说明最近合规钉位」，说明文字会出现在这里。</div>
          )}
        </Panel>
        </div>
        <div>
          <Panel title="当前钉位" tag={selected ? selected.id : '未选'}>
            <button className="btn btn-primary" type="button" disabled={busy} onClick={() => void onScanSample()} style={{ width: '100%', marginBottom: 8 }}>
              {busy ? '正在调用后端…' : '扫描这块榉木样板'}
            </button>
            {selected ? (
              <>
                <div className="hint" style={{ marginBottom: 8 }}>{selected.xMm} mm{selected.photo ? ' · 已拍照' : ' · 未拍照'}</div>
                <label className="btn btn-sm">
                  拍照扫描这个钉位
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    style={{ display: 'none' }}
                    onChange={(event) => {
                      const file = event.target.files?.[0]
                      if (file) void onPhoto(file)
                      event.target.value = ''
                    }}
                  />
                </label>
                <div style={{ marginTop: 10 }}>
                  {selected.defects.length === 0 && <div className="hint">这张照片上还没有缺陷。</div>}
                  {selected.defects.map((d) => (
                    <div key={d.id} className="hint">{DEFECT_LABEL[d.type] || d.type} {(d.confidence * 100).toFixed(0)}%</div>
                  ))}
                </div>
                {board && selected.hasAnnotated && (
                  <img
                    src={annotatedImageUrl(board.id, selected.id)}
                    alt="缺陷图"
                    style={{ width: '100%', marginTop: 10, borderRadius: 6, border: '1px solid var(--border)' }}
                  />
                )}
                <textarea
                  value={prompt}
                  onChange={(event) => setPrompt(event.target.value)}
                  rows={5}
                  style={{ width: '100%', marginTop: 10 }}
                />
                <button
                  className="btn btn-primary"
                  style={{ width: '100%', marginTop: 8 }}
                  type="button"
                  disabled={busy}
                  onClick={() => void onAdvise()}
                >
                  {busy ? '正在调用后端…' : '让模型说明最近合规钉位'}
                </button>
                <button className="btn btn-sm btn-danger" style={{ marginTop: 10 }} type="button" disabled={!board || busy} onClick={() => board && void run(() => removeIntakeStation(board.id, selected.id)).then(() => setSelectedId(null))}>
                  删除这个钉位
                </button>
              </>
            ) : (
              <div className="hint">先在长板上点一个钉位。</div>
            )}
          </Panel>
          <Panel title="红外探伤" tag={board?.irMode || 'stub'}>
            <label className="checkbox-row" style={{ marginBottom: 8 }}>
              <input type="checkbox" checked={simulateIr} onChange={() => setSimulateIr(!simulateIr)} />
              没有探伤仪时返回一处桩位置
            </label>
            <button className="btn btn-primary" style={{ width: '100%' }} type="button" disabled={busy} onClick={() => void onIr()}>
              {busy ? '正在调用后端…' : '扫描钉位'}
            </button>
            <div style={{ marginTop: 8 }}>
              {(board?.ir ?? []).map((hit) => (
                <div key={hit.id} className="hint">{hit.kind} @ {hit.xMm} mm</div>
              ))}
            </div>
          </Panel>
          <Panel title="选优机定级" tag={board?.grade?.grade || '榉木'}>
            <div className="hint" style={{ marginBottom: 8 }}>
              基材按榉木、阔叶锯材。优选对应特等；只有活节为一等；有死节、但没有腐朽和贯通裂纹为二等；腐朽、贯通裂纹或虫眼成片为等外。活节和不足 15 mm 的节子不降等。
            </div>
            <button className="btn btn-primary" style={{ width: '100%' }} type="button" disabled={busy} onClick={() => void onGrade()}>
              {busy ? '正在调用后端…' : '按榉木标准定级'}
            </button>
            <div className="hint" style={{ marginTop: 8 }}>返回的等级显示在左侧「模型输出」。</div>
          </Panel>
        </div>
      </div>
    </div>
  )
}
