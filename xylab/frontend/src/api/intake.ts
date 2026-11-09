/** 钉位扫描接口。与选区检测的 client.ts 分开，避免再堆进同一个文件。 */
const BASE = '/api'

export interface IntakeDefect {
  id: string
  type: string
  confidence: number
  bbox: number[]
}

export interface IntakeStation {
  id: string
  xMm: number
  photo: boolean
  defects: IntakeDefect[]
  hasAnnotated: boolean
  advice: string | null
}

export interface IntakeIrHit {
  id: string
  xMm: number
  yMm: number
  kind: string
  confidence: number
  note: string
}

export interface IntakeGrade {
  grade: string
  score: number
  reasons: string[]
  grader: string
  reference: string
  aiError?: string
}

export interface IntakeBoard {
  id: string
  lengthMm: number
  widthMm: number
  label: string
  stations: IntakeStation[]
  ir: IntakeIrHit[]
  grade: IntakeGrade | null
  irMode?: string
}

async function readError(res: Response): Promise<string> {
  const text = await res.text()
  try {
    const data = JSON.parse(text) as { detail?: unknown }
    if (typeof data.detail === 'string') return data.detail
  } catch {
    /* 非 JSON */
  }
  return text || `请求失败 ${res.status}`
}

function fromApi(data: {
  id: string
  length_mm: number
  width_mm: number
  label: string
  stations: {
    id: string
    x_mm: number
    photo: boolean
    defects: IntakeDefect[]
    has_annotated?: boolean
    advice?: string | null
  }[]
  ir: { id: string; x_mm: number; y_mm: number; kind: string; confidence: number; note: string }[]
  grade: { grade: string; score: number; reasons: string[]; grader: string; reference: string; ai_error?: string } | null
  ir_mode?: string
}): IntakeBoard {
  return {
    id: data.id,
    lengthMm: data.length_mm,
    widthMm: data.width_mm,
    label: data.label,
    stations: data.stations.map((s) => ({
      id: s.id,
      xMm: s.x_mm,
      photo: s.photo,
      defects: s.defects || [],
      hasAnnotated: Boolean(s.has_annotated),
      advice: s.advice ?? null,
    })),
    ir: (data.ir || []).map((h) => ({
      id: h.id,
      xMm: h.x_mm,
      yMm: h.y_mm,
      kind: h.kind,
      confidence: h.confidence,
      note: h.note,
    })),
    grade: data.grade
      ? {
          grade: data.grade.grade,
          score: data.grade.score,
          reasons: data.grade.reasons || [],
          grader: data.grade.grader,
          reference: data.grade.reference,
          aiError: data.grade.ai_error,
        }
      : null,
    irMode: data.ir_mode,
  }
}

export async function createIntakeBoard(lengthMm: number, widthMm: number): Promise<IntakeBoard> {
  const res = await fetch(`${BASE}/intake/boards`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ length_mm: lengthMm, width_mm: widthMm, label: '长板' }),
  })
  if (!res.ok) throw new Error(await readError(res))
  return fromApi(await res.json())
}

export async function resizeIntakeBoard(boardId: string, lengthMm: number): Promise<IntakeBoard> {
  const res = await fetch(`${BASE}/intake/boards/${boardId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ length_mm: lengthMm }),
  })
  if (!res.ok) throw new Error(await readError(res))
  return fromApi(await res.json())
}

export async function addIntakeStation(boardId: string, xMm: number): Promise<IntakeBoard> {
  const res = await fetch(`${BASE}/intake/boards/${boardId}/stations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ x_mm: xMm }),
  })
  if (!res.ok) throw new Error(await readError(res))
  return fromApi(await res.json())
}

export async function removeIntakeStation(boardId: string, stationId: string): Promise<IntakeBoard> {
  const res = await fetch(`${BASE}/intake/boards/${boardId}/stations/${stationId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(await readError(res))
  return fromApi(await res.json())
}

export async function scanStationPhoto(boardId: string, stationId: string, file: File): Promise<IntakeBoard> {
  const body = new FormData()
  body.append('image', file)
  const res = await fetch(`${BASE}/intake/boards/${boardId}/stations/${stationId}/photo`, { method: 'POST', body })
  if (!res.ok) throw new Error(await readError(res))
  return fromApi(await res.json())
}

export async function scanInfrared(boardId: string, simulate: boolean): Promise<IntakeBoard> {
  const res = await fetch(`${BASE}/intake/boards/${boardId}/ir`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ simulate }),
  })
  if (!res.ok) throw new Error(await readError(res))
  return fromApi(await res.json())
}

export function annotatedImageUrl(boardId: string, stationId: string): string {
  return `${BASE}/intake/boards/${boardId}/stations/${stationId}/annotated`
}

export async function adviseStation(
  boardId: string,
  stationId: string,
  prompt: string,
  spacingMm: number,
): Promise<IntakeBoard> {
  const res = await fetch(`${BASE}/intake/boards/${boardId}/stations/${stationId}/advise`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, spacing_mm: spacingMm }),
  })
  if (!res.ok) throw new Error(await readError(res))
  return fromApi(await res.json())
}

export async function gradeIntakeBoard(boardId: string): Promise<IntakeBoard> {
  const res = await fetch(`${BASE}/intake/boards/${boardId}/grade`, { method: 'POST' })
  if (!res.ok) throw new Error(await readError(res))
  return fromApi(await res.json())
}
