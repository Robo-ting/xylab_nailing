// ==========================================================================
// API 服务层：统一封装后端接口，后端不可用时自动回退到本地模拟数据
// 预留真实 YOLO / RAG / LLM / ROS 服务对接（见 backend/main.py 桩）
// ==========================================================================
import type { Defect, RuleChunk } from '../lib/types'
import { SAMPLE_DEFECTS, SAMPLE_BOARD } from '../mock/defects'
import { RULE_CHUNKS, searchRules } from '../mock/rules'

const BASE = '/api'

/** 后端是否在线（首次探测后缓存） */
let backendOnline: boolean | null = null

async function probe(): Promise<boolean> {
  if (backendOnline !== null) return backendOnline
  try {
    const ctrl = new AbortController()
    const t = setTimeout(() => ctrl.abort(), 1200)
    const res = await fetch(`${BASE}/health`, { signal: ctrl.signal })
    clearTimeout(t)
    backendOnline = res.ok
  } catch {
    backendOnline = false
  }
  return backendOnline
}

export interface DetectResponse {
  defects: Defect[]
  board: { width: number; height: number }
  source: 'backend' | 'mock'
}

/** 缺陷检测：真实后端跑 YOLOv8-seg，回退用模拟数据 */
export async function detectDefects(imageName?: string): Promise<DetectResponse> {
  if (await probe()) {
    try {
      const res = await fetch(`${BASE}/detect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: imageName }),
      })
      if (res.ok) {
        const data = await res.json()
        return { ...data, source: 'backend' }
      }
    } catch {
      /* fall through to mock */
    }
  }
  // 本地模拟
  return {
    defects: SAMPLE_DEFECTS,
    board: SAMPLE_BOARD,
    source: 'mock',
  }
}

export interface RagResponse {
  chunks: RuleChunk[]
  source: 'backend' | 'mock'
}

/** RAG 检索规范条款 */
export async function ragSearch(query: string, topK = 5): Promise<RagResponse> {
  if (await probe()) {
    try {
      const res = await fetch(`${BASE}/rules/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: topK }),
      })
      if (res.ok) {
        const data = await res.json()
        return { chunks: data.chunks, source: 'backend' }
      }
    } catch {
      /* fall through */
    }
  }
  return { chunks: searchRules(query, topK), source: 'mock' }
}

/** 列出已 ingest 的规范条款总数（示意） */
export async function listRules(): Promise<RuleChunk[]> {
  if (await probe()) {
    try {
      const res = await fetch(`${BASE}/rules`)
      if (res.ok) return (await res.json()).chunks
    } catch {
      /* fall through */
    }
  }
  return RULE_CHUNKS
}

/** 手动重置后端探测状态（用于「重新连接」按钮） */
export function resetBackendProbe(): void {
  backendOnline = null
}

export async function isBackendOnline(): Promise<boolean> {
  return probe()
}

/** 后端 [x1,y1,x2,y2] -> 前端既有 [x,y,w,h] */
function xyxyToXywh(bbox: number[]): [number, number, number, number] {
  const [x1, y1, x2, y2] = bbox
  return [x1, y1, x2 - x1, y2 - y1]
}

function xywhToXyxy(bbox: [number, number, number, number]): [number, number, number, number] {
  const [x, y, w, h] = bbox
  return [x, y, x + w, y + h]
}

function backendTypeToFrontend(t: string): Defect['type'] {
  if (t === 'dead_knot') return 'knot_dead'
  return t as Defect['type']
}

function frontendTypeToBackend(t: string): string {
  if (t === 'knot_dead') return 'dead_knot'
  return t
}

function defectFromApi(raw: {
  id: string
  type: string
  confidence: number
  bbox: number[]
}): Defect {
  const bbox = xyxyToXywh(raw.bbox)
  const [x, y, w, h] = bbox
  return {
    id: raw.id,
    type: backendTypeToFrontend(raw.type),
    confidence: raw.confidence,
    bbox,
    polygon: [
      { x, y },
      { x: x + w, y },
      { x: x + w, y: y + h },
      { x, y: y + h },
    ],
    area: Math.round(w * h),
    severity: 'moderate',
  }
}

export interface ImageDetectResult {
  imageId: string
  imageUrl: string
  imageWidthPx: number
  imageHeightPx: number
  detectionMode: 'mock'
  defects: Defect[]
}

/** 上传木板图。当前后端为 MockDetector，不是真实死节识别。 */
export async function detectBoardImage(file: File): Promise<ImageDetectResult> {
  resetBackendProbe()
  const body = new FormData()
  body.append('image', file)
  const res = await fetch(`${BASE}/detect`, { method: 'POST', body })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `detect failed ${res.status}`)
  }
  const data = await res.json()
  return {
    imageId: data.image_id,
    imageUrl: data.image_url,
    imageWidthPx: data.width,
    imageHeightPx: data.height,
    detectionMode: 'mock',
    defects: (data.defects as { id: string; type: string; confidence: number; bbox: number[] }[]).map(
      defectFromApi,
    ),
  }
}

export interface MvpForbiddenRegion {
  x: number
  y: number
  w: number
  h: number
}

export interface MvpNailPoint {
  id: string
  x: number
  y: number
}

export interface ImagePlanResult {
  forbiddenRegions: MvpForbiddenRegion[]
  nailPoints: MvpNailPoint[]
}

/** 钉位规划。请求前把前端结构转回后端协议；响应再转回前端。 */
export async function planNailsOnImage(input: {
  imageWidthPx: number
  imageHeightPx: number
  defects: Defect[]
  edgeMarginPx: number
  knotMarginPx: number
  nailSpacingPx: number
}): Promise<ImagePlanResult> {
  const res = await fetch(`${BASE}/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      image_width: input.imageWidthPx,
      image_height: input.imageHeightPx,
      defects: input.defects.map((d) => ({
        id: d.id,
        type: frontendTypeToBackend(d.type),
        confidence: d.confidence,
        bbox: xywhToXyxy(d.bbox),
      })),
      edge_margin_px: input.edgeMarginPx,
      knot_margin_px: input.knotMarginPx,
      nail_spacing_px: input.nailSpacingPx,
    }),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `plan failed ${res.status}`)
  }
  const data = await res.json()
  const forbiddenRegions: MvpForbiddenRegion[] = (data.forbidden_regions as number[][]).map((b) => {
    const [x, y, w, h] = xyxyToXywh(b)
    return { x, y, w, h }
  })
  const nailPoints: MvpNailPoint[] = (data.nail_points as { id: number | string; x: number; y: number }[]).map(
    (n) => ({ id: String(n.id), x: n.x, y: n.y }),
  )
  return { forbiddenRegions, nailPoints }
}

async function readError(res: Response): Promise<string> {
  const text = await res.text()
  try {
    const data = JSON.parse(text) as { detail?: unknown }
    if (typeof data.detail === 'string') return data.detail
  } catch {
    /* 非 JSON 错误体 */
  }
  return text || `请求失败 ${res.status}`
}

export type SourceKind = 'image' | 'video' | 'camera'

export interface SourceFrame {
  sourceId: string
  kind: SourceKind
  width: number
  height: number
  imageUrl: string
  zone: { x: number; y: number }[] | null
  zoneScaled: boolean
}

export interface SourceRunResult extends SourceFrame {
  defects: Defect[]
  dropped: number
  forbiddenRegions: MvpForbiddenRegion[]
  nailPoints: MvpNailPoint[]
}

function asPoints(raw: number[][] | null | undefined): { x: number; y: number }[] | null {
  if (!raw || raw.length < 3) return null
  return raw.map(([x, y]) => ({ x, y }))
}

function zoneJson(zone: { x: number; y: number }[] | null): string {
  if (!zone || zone.length < 3) return ''
  return JSON.stringify(zone.map((p) => [Math.round(p.x), Math.round(p.y)]))
}

function frameFromApi(data: {
  source_id: string
  kind: SourceKind
  width: number
  height: number
  image_url: string
  zone: number[][] | null
  zone_scaled: boolean
}): SourceFrame {
  return {
    sourceId: data.source_id,
    kind: data.kind,
    width: data.width,
    height: data.height,
    imageUrl: data.image_url,
    zone: asPoints(data.zone),
    zoneScaled: Boolean(data.zone_scaled),
  }
}

export async function createImageSource(
  file: File,
  zone: { x: number; y: number }[] | null,
  zoneW: number,
  zoneH: number,
): Promise<SourceFrame> {
  resetBackendProbe()
  const body = new FormData()
  body.append('image', file)
  const encoded = zoneJson(zone)
  if (encoded) {
    body.append('zone', encoded)
    body.append('zone_w', String(zoneW))
    body.append('zone_h', String(zoneH))
  }
  const res = await fetch(`${BASE}/sources/image`, { method: 'POST', body })
  if (!res.ok) throw new Error(await readError(res))
  return frameFromApi(await res.json())
}

export async function replaceSourceImage(sourceId: string, file: File): Promise<SourceFrame> {
  const body = new FormData()
  body.append('image', file)
  const res = await fetch(`${BASE}/sources/${sourceId}/image`, { method: 'POST', body })
  if (!res.ok) throw new Error(await readError(res))
  return frameFromApi(await res.json())
}

export async function createVideoSource(
  file: File,
  zone: { x: number; y: number }[] | null,
  zoneW: number,
  zoneH: number,
): Promise<SourceFrame> {
  resetBackendProbe()
  const body = new FormData()
  body.append('video', file)
  const encoded = zoneJson(zone)
  if (encoded) {
    body.append('zone', encoded)
    body.append('zone_w', String(zoneW))
    body.append('zone_h', String(zoneH))
  }
  const res = await fetch(`${BASE}/sources/video`, { method: 'POST', body })
  if (!res.ok) throw new Error(await readError(res))
  return frameFromApi(await res.json())
}

export async function createCameraSource(
  cameraIndex: number,
  zone: { x: number; y: number }[] | null,
  zoneW: number,
  zoneH: number,
): Promise<SourceFrame> {
  resetBackendProbe()
  const params = new URLSearchParams({ camera_index: String(cameraIndex) })
  const encoded = zoneJson(zone)
  if (encoded) {
    params.set('zone', encoded)
    params.set('zone_w', String(zoneW))
    params.set('zone_h', String(zoneH))
  }
  const res = await fetch(`${BASE}/sources/camera?${params.toString()}`, { method: 'POST' })
  if (!res.ok) throw new Error(await readError(res))
  return frameFromApi(await res.json())
}

export async function pauseSource(sourceId: string): Promise<void> {
  const res = await fetch(`${BASE}/sources/${sourceId}/pause`, { method: 'POST' })
  if (!res.ok) throw new Error(await readError(res))
}

export async function resumeSource(sourceId: string): Promise<void> {
  const res = await fetch(`${BASE}/sources/${sourceId}/resume`, { method: 'POST' })
  if (!res.ok) throw new Error(await readError(res))
}

export async function fetchSnapshot(sourceId: string): Promise<{ url: string; width: number; height: number }> {
  const res = await fetch(`${BASE}/sources/${sourceId}/snapshot?t=${Date.now()}`)
  if (!res.ok) throw new Error(await readError(res))
  const width = Number(res.headers.get('X-Frame-Width') || 0)
  const height = Number(res.headers.get('X-Frame-Height') || 0)
  const blob = await res.blob()
  return { url: URL.createObjectURL(blob), width, height }
}

export async function fetchZone(sourceId: string): Promise<{ x: number; y: number }[] | null> {
  const res = await fetch(`${BASE}/sources/${sourceId}/zone`)
  if (!res.ok) throw new Error(await readError(res))
  const data = await res.json()
  return asPoints(data.zone)
}

export async function saveZone(
  sourceId: string,
  points: { x: number; y: number }[],
  frameW: number,
  frameH: number,
): Promise<SourceFrame> {
  const res = await fetch(`${BASE}/sources/${sourceId}/zone`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      points: points.map((p) => [Math.round(p.x), Math.round(p.y)]),
      frame_w: frameW,
      frame_h: frameH,
    }),
  })
  if (!res.ok) throw new Error(await readError(res))
  return frameFromApi(await res.json())
}

export async function deleteZone(sourceId: string): Promise<SourceFrame> {
  const res = await fetch(`${BASE}/sources/${sourceId}/zone`, { method: 'DELETE' })
  if (!res.ok) throw new Error(await readError(res))
  return frameFromApi(await res.json())
}

export async function runSource(
  sourceId: string,
  margins: { edgeMarginPx: number; knotMarginPx: number; nailSpacingPx: number },
): Promise<SourceRunResult> {
  const res = await fetch(`${BASE}/sources/${sourceId}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      edge_margin_px: margins.edgeMarginPx,
      knot_margin_px: margins.knotMarginPx,
      nail_spacing_px: margins.nailSpacingPx,
    }),
  })
  if (!res.ok) throw new Error(await readError(res))
  const data = await res.json()
  const frame = frameFromApi(data)
  const jpeg = typeof data.frame_jpeg === 'string' ? data.frame_jpeg : ''
  return {
    ...frame,
    imageUrl: jpeg ? `data:image/jpeg;base64,${jpeg}` : `${frame.imageUrl}?t=${Date.now()}`,
    defects: (data.defects as { id: string; type: string; confidence: number; bbox: number[] }[]).map(defectFromApi),
    dropped: Number(data.dropped || 0),
    forbiddenRegions: (data.forbidden_regions as number[][]).map((b) => {
      const [x, y, w, h] = xyxyToXywh(b)
      return { x, y, w, h }
    }),
    nailPoints: (data.nail_points as { id: number | string; x: number; y: number }[]).map((n) => ({
      id: String(n.id),
      x: n.x,
      y: n.y,
    })),
  }
}
