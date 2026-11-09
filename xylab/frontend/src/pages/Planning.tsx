import { useEffect, useMemo, useRef, useState } from 'react'
import { Panel } from '../components/Panel'
import { BoardCanvas, type InteractionMode } from '../components/BoardCanvas'
import { ZoneEditor } from '../components/ZoneEditor'
import { SliderField } from '../components/Field'
import { useSystemStore } from '../store/useSystemStore'
import { runPipeline, type PipelineResult } from '../lib/pipeline'
import { DEFAULT_LAYERS, type Scene, type SceneLayers } from '../lib/render'
import { polygonIntersection, erodePolygon } from '../lib/geometry'
import { SAMPLE_DEFECTS_BOARD2 } from '../mock/defects'
import {
  createCameraSource,
  createImageSource,
  createVideoSource,
  replaceSourceImage,
  runSource,
  type SourceFrame,
} from '../api/client'
import type { Board, Point, Roi } from '../lib/types'

type Step = 1 | 2 | 3 | 4

const STEP_LABELS: Record<Step, string> = {
  1: 'Step 1 · 缺陷检测',
  2: 'Step 2 · 原始禁区',
  3: 'Step 3 · 膨胀禁区 (r)',
  4: 'Step 4 · KD-tree 选点',
}

export function Planning() {
  const store = useSystemStore()
  const {
    defects,
    rois,
    addRoi,
    removeRoi,
    toggleRoi,
    clearRois,
    boardWidth,
    boardHeight,
    params,
    setParams,
    designNails,
    setDesignNails,
    substrate,
    grainRelation,
    setPlanning,
    setLogs,
    markStage,
    boards,
    pairs,
    imageMvpActive,
    imageUrl,
    imageWidthPx,
    imageHeightPx,
    mvpDefects,
    mvpForbidden,
    knotMarginPx,
    setMvpParams,
    sourceId,
    sourceKind,
    zonePoints,
    zoneScaled,
    droppedDefects,
    applySourceResult,
  } = store

  const [step, setStep] = useState<Step>(1)
  const [tool, setTool] = useState<InteractionMode>('none')
  const [result, setResult] = useState<PipelineResult | null>(null)
  // 两块板层叠：装配约束（仅重合区可钉）/ 显示板件 / 叠合第二块板缺陷
  const [assemblyOn, setAssemblyOn] = useState(false)
  const [showBoards, setShowBoards] = useState(false)
  const [fuseBoard2, setFuseBoard2] = useState(false)
  const [busy, setBusy] = useState(false)
  const [mvpError, setMvpError] = useState<string | null>(null)
  const [zoneOpen, setZoneOpen] = useState(false)
  const [autoRun, setAutoRun] = useState(false)
  const [cameraIndex, setCameraIndex] = useState(0)
  const fileRef = useRef<HTMLInputElement>(null)
  const videoRef = useRef<HTMLInputElement>(null)
  const runLock = useRef(false)

  // 计算两块板的重合区（可钉合区）：交集后按最小搭接内缩
  const overlapRegion = useMemo(() => {
    const pair = pairs[0]
    if (!pair) return [] as Point[]
    const upper = boards.find((b) => b.boardId === pair.upper)
    const lower = boards.find((b) => b.boardId === pair.lower)
    if (!upper || !lower) return [] as Point[]
    const region = polygonIntersection(upper.polygon, lower.polygon)
    return erodePolygon(region, pair.minOverlap / 2)
  }, [boards, pairs])

  // 显示用缺陷（可叠合第二块板）
  const displayDefects = useMemo(
    () => (imageMvpActive ? mvpDefects : fuseBoard2 ? [...defects, ...SAMPLE_DEFECTS_BOARD2] : defects),
    [imageMvpActive, mvpDefects, defects, fuseBoard2],
  )

  const logicalWidth = imageMvpActive && imageWidthPx ? imageWidthPx : boardWidth
  const logicalHeight = imageMvpActive && imageHeightPx ? imageHeightPx : boardHeight

  // 场景中的板件层（含重合区伪板）
  const sceneBoards = useMemo<Board[]>(() => {
    if (!showBoards) return []
    const overlap: Board[] =
      overlapRegion.length >= 3
        ? [{ boardId: '重合区', role: 'panel', layer: 2, thickness: 0, polygon: overlapRegion, color: '#22d3ee' }]
        : []
    return [...boards, ...overlap]
  }, [showBoards, boards, overlapRegion])

  // 根据当前步骤决定显示图层
  const layers: SceneLayers = useMemo(() => {
    if (imageMvpActive) {
      return {
        ...DEFAULT_LAYERS,
        rois: true,
        boards: false,
        designNails: false,
        finalNails: false,
        defects: true,
        masks: true,
        forbiddenOriginal: false,
        forbiddenDilated: false,
        costMap: false,
      }
    }
    const base = { ...DEFAULT_LAYERS, rois: true, designNails: false, finalNails: false }
    switch (step) {
      case 1:
        return { ...base, defects: true, masks: true }
      case 2:
        return { ...base, forbiddenOriginal: true, masks: false }
      case 3:
        return { ...base, forbiddenOriginal: true, forbiddenDilated: true, masks: false }
      case 4:
        return {
          ...base,
          forbiddenDilated: true,
          costMap: params.costMode === 'soft',
          finalNails: false,
          designNails: false,
        }
    }
  }, [step, params.costMode, imageMvpActive])

  const zoneRoi = useMemo<Roi[]>(() => {
    if (!zonePoints || zonePoints.length < 3) return []
    return [{ id: 'plan-zone', shape: 'polygon', polygon: zonePoints, enabled: true, label: '选区' }]
  }, [zonePoints])

  const scene: Scene = useMemo(
    () => ({
      boardWidth: logicalWidth,
      boardHeight: logicalHeight,
      defects: displayDefects,
      rois: imageMvpActive ? zoneRoi : rois,
      boards: imageMvpActive ? [] : sceneBoards,
      designNails: [],
      grid: imageMvpActive ? null : result?.grid ?? null,
      dilationClass: imageMvpActive ? null : result?.dilationClass ?? null,
      layers: imageMvpActive ? layers : { ...layers, boards: showBoards },
      enabledTypes: store.enabledTypes,
      confFilter: store.confFilter,
      boardImageUrl: imageMvpActive ? imageUrl ?? undefined : undefined,
      mvpForbidden: imageMvpActive ? mvpForbidden : undefined,
      coordUnit: imageMvpActive ? 'px' : 'mm',
    }),
    [
      logicalWidth,
      logicalHeight,
      displayDefects,
      rois,
      sceneBoards,
      showBoards,
      result,
      designNails,
      layers,
      store.enabledTypes,
      store.confFilter,
      imageMvpActive,
      imageUrl,
      mvpForbidden,
      zoneRoi,
    ],
  )

  function rememberFrame(frame: SourceFrame) {
    useSystemStore.setState({
      imageMvpActive: true,
      sourceId: frame.sourceId,
      sourceKind: frame.kind,
      imageId: frame.sourceId,
      imageUrl: `${frame.imageUrl}?t=${Date.now()}`,
      imageWidthPx: frame.width,
      imageHeightPx: frame.height,
      zonePoints: frame.zone,
      zoneScaled: frame.zoneScaled,
    })
  }

  async function refreshSource(id: string) {
    if (runLock.current) return
    runLock.current = true
    const st = useSystemStore.getState()
    try {
      const res = await runSource(id, {
        edgeMarginPx: st.edgeMarginPx,
        knotMarginPx: st.knotMarginPx,
        nailSpacingPx: st.nailSpacingPx,
      })
      applySourceResult(res)
      markStage('input')
      markStage('detect')
      markStage('forbidden')
      markStage('coordinate')
      setMvpError(null)
    } catch (err) {
      setMvpError(err instanceof Error ? err.message : String(err))
    } finally {
      runLock.current = false
    }
  }

  async function openStill(file: File) {
    setMvpError(null)
    setBusy(true)
    setAutoRun(false)
    try {
      const st = useSystemStore.getState()
      const frame =
        st.sourceId && st.sourceKind === 'image'
          ? await replaceSourceImage(st.sourceId, file)
          : await createImageSource(file, st.zonePoints, st.imageWidthPx ?? 0, st.imageHeightPx ?? 0)
      rememberFrame(frame)
      await refreshSource(frame.sourceId)
    } catch (err) {
      setMvpError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  async function openVideo(file: File) {
    setMvpError(null)
    setBusy(true)
    try {
      const st = useSystemStore.getState()
      const frame = await createVideoSource(file, st.zonePoints, st.imageWidthPx ?? 0, st.imageHeightPx ?? 0)
      rememberFrame(frame)
      setAutoRun(true)
      await refreshSource(frame.sourceId)
    } catch (err) {
      setMvpError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
      if (videoRef.current) videoRef.current.value = ''
    }
  }

  async function openCamera() {
    setMvpError(null)
    setBusy(true)
    try {
      const st = useSystemStore.getState()
      const frame = await createCameraSource(cameraIndex, st.zonePoints, st.imageWidthPx ?? 0, st.imageHeightPx ?? 0)
      rememberFrame(frame)
      setAutoRun(true)
      await refreshSource(frame.sourceId)
    } catch (err) {
      setMvpError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  const refreshRef = useRef(refreshSource)
  refreshRef.current = refreshSource

  useEffect(() => {
    if (!autoRun || !sourceId || zoneOpen || (sourceKind !== 'video' && sourceKind !== 'camera')) return
    let cancelled = false
    let timer = 0
    const loop = async () => {
      await refreshRef.current(sourceId)
      if (cancelled) return
      timer = window.setTimeout(loop, 450)
    }
    void loop()
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [autoRun, sourceId, sourceKind, zoneOpen])

  async function runPlan() {
    if (imageMvpActive) {
      if (!sourceId) {
        setMvpError('先上传图片、视频，或打开摄像头')
        return
      }
      setBusy(true)
      await refreshSource(sourceId)
      setBusy(false)
      return
    }

    const filtered = displayDefects.filter(
      (d) => store.enabledTypes.has(d.type) && d.confidence >= store.confFilter,
    )
    const res = runPipeline({
      boardWidth,
      boardHeight,
      defects: filtered,
      rois,
      designNails,
      params,
      substrate,
      grainRelation,
      nailableRegion: assemblyOn ? overlapRegion : undefined,
    })
    setResult(res)
    setDesignNails(res.nails)
    setPlanning(res.nails, res.decisions)
    setLogs(res.logs)
    setStep(4)
    markStage('detect')
    markStage('forbidden')
    markStage('decision')
    markStage('coordinate')
    markStage('log')
  }

  function onNailAdd(pt: Point) {
    const id = 'N' + (designNails.length + 1) + '_' + Date.now().toString().slice(-4)
    setDesignNails([...designNails, { id, design: pt, status: 'pending' }])
  }

  const stats = result?.stats

  return (
    <div>
      <div className="page-title">选区检测</div>
      <div className="page-desc">
        上传图片、视频或打开摄像头后，停在一帧上画出矩形、圆形或多边形。留在选区内的缺陷会外扩成禁区。视频和摄像头会按新画面反复更新禁区。钉点先不铺。
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 16 }}>
        <Panel
          title={imageMvpActive ? '画面' : '四步流水线'}
          tag={
            imageMvpActive
              ? imageWidthPx && imageHeightPx
                ? `${imageWidthPx} × ${imageHeightPx} px`
                : '图片规划'
              : result
                ? `采纳缺陷 ${result.acceptedDefects} · 可行格 ${stats?.feasibleCells}`
                : '未运行'
          }
        >
          {!imageMvpActive && <div className="canvas-toolbar">
            {([1, 2, 3, 4] as Step[]).map((s) => (
              <div
                key={s}
                className={'toolbar-btn' + (step === s ? ' active' : '')}
                onClick={() => setStep(s)}
              >
                {STEP_LABELS[s]}
              </div>
            ))}
          </div>}

          <div className="canvas-toolbar">
            <input
              ref={fileRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              style={{ display: 'none' }}
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) void openStill(f)
              }}
            />
            <input
              ref={videoRef}
              type="file"
              accept="video/mp4,video/webm,video/quicktime,.avi,.mkv"
              style={{ display: 'none' }}
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) void openVideo(f)
              }}
            />
            <div className="toolbar-btn" onClick={() => fileRef.current?.click()}>
              {busy ? '处理中…' : '上传图片'}
            </div>
            <div className="toolbar-btn" onClick={() => videoRef.current?.click()}>
              上传视频
            </div>
            <input
              className="source-index"
              type="number"
              min={0}
              max={8}
              value={cameraIndex}
              onChange={(e) => setCameraIndex(Number(e.target.value))}
              aria-label="摄像头序号"
            />
            <div className="toolbar-btn" onClick={() => void openCamera()}>
              打开摄像头
            </div>
            {imageMvpActive && (
              <div className="toolbar-btn" onClick={() => sourceId && setZoneOpen(true)}>
                画选区
              </div>
            )}
            {imageMvpActive && imageWidthPx && imageHeightPx && (
              <span className="hint" style={{ alignSelf: 'center' }}>
                {sourceKind === 'camera' ? '摄像头' : sourceKind === 'video' ? '视频' : '图片'}
                {' '}
                {imageWidthPx} × {imageHeightPx} px
              </span>
            )}
          </div>
          {mvpError && (
            <div className="badge badge-red" style={{ marginBottom: 8 }}>
              {mvpError}
            </div>
          )}
          {!imageMvpActive && <div className="canvas-toolbar">
            <span className="hint" style={{ alignSelf: 'center' }}>ROI 工具：</span>
            <div className={'toolbar-btn' + (tool === 'none' ? ' active' : '')} onClick={() => setTool('none')}>
              ↖ 选择
            </div>
            <div className={'toolbar-btn' + (tool === 'roi-rect' ? ' active' : '')} onClick={() => setTool('roi-rect')}>
              ▭ 矩形框选
            </div>
            <div className={'toolbar-btn' + (tool === 'roi-circle' ? ' active' : '')} onClick={() => setTool('roi-circle')}>
              ◯ 圆形框选
            </div>
            <div className={'toolbar-btn' + (tool === 'roi-poly' ? ' active' : '')} onClick={() => setTool('roi-poly')}>
              ⬡ 任意形状
            </div>
          </div>}

          <BoardCanvas
            scene={scene}
            width={760}
            height={500}
            mode={imageMvpActive ? 'none' : tool}
            onRoiCreate={(r) => {
              addRoi(r)
              setTool('none')
            }}
            onNailAdd={onNailAdd}
          />

          <div className="legend" style={{ marginTop: 12 }}>
            {!imageMvpActive && <div className="item"><span className="swatch" style={{ background: 'rgba(239,68,68,0.6)' }} />原始禁区</div>}
            {!imageMvpActive && <div className="item"><span className="swatch" style={{ background: 'rgba(245,158,11,0.5)' }} />膨胀缓冲 (r={params.dilationRadius}mm)</div>}
            {imageMvpActive && <div className="item"><span className="swatch" style={{ background: 'rgba(56,139,253,0.85)' }} />选区</div>}
            {imageMvpActive && <div className="item"><span className="swatch" style={{ background: '#f85149' }} />保留的检测框</div>}
            {imageMvpActive && <div className="item"><span className="swatch" style={{ background: 'rgba(239,68,68,0.55)' }} />禁区外扩</div>}
          </div>
        </Panel>

        <div>
          {!imageMvpActive && <Panel title="叠合装配（两块板层叠）" tag="Assembly">
            <label className="checkbox-row" style={{ marginBottom: 8 }}>
              <input type="checkbox" checked={showBoards} onChange={() => setShowBoards(!showBoards)} />
              显示板件与重合区
            </label>
            <label className="checkbox-row" style={{ marginBottom: 8 }}>
              <input type="checkbox" checked={assemblyOn} onChange={() => setAssemblyOn(!assemblyOn)} />
              启用装配约束（仅重合区可钉）
            </label>
            <label className="checkbox-row" style={{ marginBottom: 8 }}>
              <input type="checkbox" checked={fuseBoard2} onChange={() => setFuseBoard2(!fuseBoard2)} />
              叠合第二块板缺陷（多板融合）
            </label>
            <div className="hint">
              开启装配约束后，重合区外的设计钉位会自动移入重合区最近可行点；无可行点则跳过。
              用上方「✚ 添加钉位」可在重合区内手动规划钉合位置。
            </div>
            {assemblyOn && overlapRegion.length < 3 && (
              <div className="badge badge-red" style={{ marginTop: 8 }}>未检测到有效重合区，请在装配标定页检查板件</div>
            )}
          </Panel>}

          {imageMvpActive ? (
            <Panel title="选区" tag={zonePoints && zonePoints.length >= 3 ? `${zonePoints.length} 点` : '未设置'}>
              <div className="hint" style={{ marginBottom: 10 }}>
                矩形和圆形按住拖拽，多边形逐点点击。保存后，后续画面都用这块选区筛框。没画选区时保留全部检测框。
              </div>
              <button className="btn btn-sm btn-primary" type="button" disabled={!sourceId} onClick={() => setZoneOpen(true)}>
                绘制选区
              </button>
              {zoneScaled && <div className="badge badge-amber" style={{ marginTop: 8 }}>已按新画面的宽高缩放</div>}
              <div className="hint" style={{ marginTop: 8 }}>筛掉检测框 {droppedDefects} 个</div>
              {sourceKind !== 'image' && sourceKind !== null && (
                <label className="checkbox-row" style={{ marginTop: 8 }}>
                  <input type="checkbox" checked={autoRun} onChange={() => setAutoRun(!autoRun)} />
                  闭环检测（新画面回来再判一次）
                </label>
              )}
            </Panel>
          ) : (
            <Panel title="ROI 关注区" tag={`${rois.length} 个`}>
              <div className="hint" style={{ marginBottom: 10 }}>
                用上方工具在板面框选：仅落在启用 ROI 内的缺陷才纳入禁区计算。无 ROI 时全板考虑。
              </div>
              {rois.length === 0 && <div className="hint">（暂无 ROI，默认全板）</div>}
              {rois.map((r) => (
                <div className="row spread" key={r.id} style={{ marginBottom: 6 }}>
                  <label className="checkbox-row">
                    <input type="checkbox" checked={r.enabled} onChange={() => toggleRoi(r.id)} />
                    <span className="badge badge-blue">{r.label}</span>
                  </label>
                  <button className="btn btn-sm btn-danger" onClick={() => removeRoi(r.id)}>删除</button>
                </div>
              ))}
              {rois.length > 0 && (
                <button className="btn btn-sm" style={{ marginTop: 8 }} onClick={clearRois}>清空全部 ROI</button>
              )}
            </Panel>
          )}

          {!imageMvpActive && <Panel title="规划参数">
              <>
                <SliderField label="膨胀半径 r" value={params.dilationRadius} min={0} max={30} step={1} unit="mm" onChange={(v) => setParams({ dilationRadius: v })} />
                <div className="hint" style={{ marginTop: -6, marginBottom: 10 }}>导师确认经验值 10mm</div>
                <SliderField label="栅格单元" value={params.cellSize} min={1} max={5} step={1} unit="mm" onChange={(v) => setParams({ cellSize: v })} />
                <div className="field">
                  <label>代价模式</label>
                  <div className="pill-toggle">
                    <button className={params.costMode === 'hard' ? 'active' : ''} onClick={() => setParams({ costMode: 'hard' })}>硬禁区</button>
                    <button className={params.costMode === 'soft' ? 'active' : ''} onClick={() => setParams({ costMode: 'soft' })}>软代价图</button>
                  </div>
                </div>
                {params.costMode === 'soft' && (
                  <>
                    <SliderField label="距离权重 α" value={params.alpha} min={0} max={5} step={0.1} onChange={(v) => setParams({ alpha: v })} />
                    <SliderField label="代价权重 β" value={params.beta} min={0} max={100} step={5} onChange={(v) => setParams({ beta: v })} />
                    <SliderField label="高斯 σ" value={params.sigma} min={5} max={40} step={1} unit="mm" onChange={(v) => setParams({ sigma: v })} />
                  </>
                )}
              </>
            <button className="btn btn-primary" style={{ width: '100%', marginTop: 8 }} onClick={() => void runPlan()} disabled={busy}>
              ▶ {busy ? '处理中…' : '运行规划流水线'}
            </button>
          </Panel>}

          {imageMvpActive && sourceId && (
            <Panel title="禁区规划" tag={`${mvpForbidden.length} 块`}>
              <div className="hint" style={{ marginBottom: 10 }}>
                选区内的死节按外扩距离生成禁区。禁区画在画面上，钉点仍然不铺。
              </div>
              <SliderField
                label="禁区外扩"
                value={knotMarginPx}
                min={0}
                max={150}
                step={1}
                unit="px"
                onChange={(v) => {
                  setMvpParams({ knotMarginPx: v })
                  if (sourceId) void refreshSource(sourceId)
                }}
              />
            </Panel>
          )}

          {imageMvpActive && sourceId && (
            <Panel title="检测">
              <button className="btn btn-primary" style={{ width: '100%' }} onClick={() => void runPlan()} disabled={busy} type="button">
                {busy ? '检测中…' : '检测当前帧'}
              </button>
              <div className="stat-grid" style={{ marginTop: 12 }}>
                <div className="stat-card"><div className="num" style={{ color: 'var(--red)' }}>{mvpDefects.length}</div><div className="lbl">保留框</div></div>
                <div className="stat-card"><div className="num" style={{ color: 'var(--amber)' }}>{mvpForbidden.length}</div><div className="lbl">禁区</div></div>
                <div className="stat-card"><div className="num">{droppedDefects}</div><div className="lbl">筛掉</div></div>
              </div>
            </Panel>
          )}

          {stats && !imageMvpActive && (
            <Panel title="规划统计">
              <div className="stat-grid">
                <div className="stat-card"><div className="num" style={{ color: 'var(--green)' }}>{stats.direct}</div><div className="lbl">直接打钉</div></div>
                <div className="stat-card"><div className="num" style={{ color: 'var(--amber)' }}>{stats.relocated}</div><div className="lbl">换位</div></div>
                <div className="stat-card"><div className="num" style={{ color: 'var(--purple)' }}>{stats.predrill}</div><div className="lbl">预钻</div></div>
                <div className="stat-card"><div className="num" style={{ color: 'var(--red)' }}>{stats.skipped}</div><div className="lbl">跳过</div></div>
              </div>
              <div className="hint" style={{ marginTop: 10 }}>
                禁区单元 {stats.forbiddenCells} · 可行单元 {stats.feasibleCells} · 钉位总数 {stats.total}
              </div>
            </Panel>
          )}
        </div>
      </div>
      {sourceId && (
        <ZoneEditor
          sourceId={sourceId}
          open={zoneOpen}
          onClose={() => setZoneOpen(false)}
          onChanged={() => {
            if (sourceId) void refreshSource(sourceId)
          }}
        />
      )}
    </div>
  )
}
