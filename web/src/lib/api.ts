/** 后端 FastAPI（默认由 VITE_API_URL 指向，如 http://127.0.0.1:8765） */

function apiOrigin(): string {
  const raw =
    typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL
      ? String(import.meta.env.VITE_API_URL)
      : ""
  return raw.replace(/\/$/, "")
}

export const API_BASE = apiOrigin()

async function fetchApi(path: string, init?: RequestInit): Promise<Response> {
  const url = `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`
  const headers = new Headers(init?.headers)
  if (
    init?.body != null &&
    !(init.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json")
  }
  const res = await fetch(url, { ...init, headers })
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`
    try {
      const t = await res.text()
      if (t) msg = `${msg}: ${t.slice(0, 800)}`
    } catch {
      /* ignore */
    }
    throw new Error(msg)
  }
  return res
}

export async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetchApi(path, init)
  return res.json() as Promise<T>
}

export async function apiText(path: string, init?: RequestInit): Promise<string> {
  const res = await fetchApi(path, init)
  return res.text()
}

/** 排队：步骤 1→5 在同一后台队列里依次执行（与单步共用同一把运行锁）。 */
export async function postRunPipelineAll(
  runId: string,
  force = false,
): Promise<{ queued: boolean; run_id: string; mode: string; force: boolean }> {
  return apiJson(
    `/api/runs/${encodeURIComponent(runId)}/run-all?force=${force ? "true" : "false"}`,
    { method: "POST" },
  )
}

/** 请求停止：当前步骤尽量收尾后不再继续（一键全流程会停在下一步之前）。 */
export async function postStopRun(
  runId: string,
): Promise<{ run_id?: string; stop_requested: boolean; cancelled_steps: string[] }> {
  return apiJson(`/api/runs/${encodeURIComponent(runId)}/stop`, { method: "POST" })
}

/** 移入回收站（outputs/_trash），首页与历史列表不再显示。 */
export async function deleteRun(
  runId: string,
): Promise<{ run_id: string; deleted: boolean; trash_path: string }> {
  return apiJson(`/api/runs/${encodeURIComponent(runId)}`, { method: "DELETE" })
}

/** 保存用户编辑的步骤文本产物 */
export async function putStepArtifactText(
  runId: string,
  step: number,
  body: { text: string; text_kind: "json" | "markdown" },
): Promise<{ ok: boolean; step: number; text_kind: string; downstream_steps: number[] }> {
  return apiJson(`/api/runs/${encodeURIComponent(runId)}/steps/${step}/artifacts/text`, {
    method: "PUT",
    body: JSON.stringify(body),
  })
}

/** 运行单个步骤（force=true 可重做已成功的步骤） */
export async function postRunStep(
  runId: string,
  step: number,
  force = false,
): Promise<{ queued: boolean; run_id: string; step: number }> {
  return apiJson(
    `/api/runs/${encodeURIComponent(runId)}/steps/${step}/run?force=${force ? "true" : "false"}`,
    { method: "POST" },
  )
}

/** 按 Step1 审核意见重新生成剧本；本次不再触发 review */
export async function postRewriteStep1FromReview(
  runId: string,
): Promise<{ queued: boolean; run_id: string; step: number; mode: string }> {
  return apiJson(`/api/runs/${encodeURIComponent(runId)}/steps/1/rewrite-from-review`, {
    method: "POST",
  })
}

/** 使用修改后的提示词重新生成 Step3 单张图片 */
export async function postRegenerateStep3Image(
  runId: string,
  body: { path: string; prompt: string },
): Promise<{ ok: boolean; path: string; prompt: string; updated_at: string }> {
  return apiJson(`/api/runs/${encodeURIComponent(runId)}/steps/3/images/regenerate`, {
    method: "POST",
    body: JSON.stringify(body),
  })
}

/** 修改项目名称（topic） */
export async function patchRunTopic(
  runId: string,
  topic: string,
): Promise<{ ok: boolean; run_id: string; topic: string }> {
  return apiJson(`/api/runs/${encodeURIComponent(runId)}`, {
    method: "PATCH",
    body: JSON.stringify({ topic }),
  })
}

export type StepStatus = "pending" | "running" | "success" | "failed" | "cancelled"

export interface StepRow {
  key?: string
  title: string
  status: StepStatus
  error: string | null
  updated_at: string | null
}

export interface RunSummary {
  run_id: string
  out_dir: string
  topic: string
  created_at: string | null
  /** 最后编辑时间（各步骤 updated_at 最大值，或创建时间） */
  updated_at?: string | null
  /** 后端 list_runs 返回的每个 step 状态简表 */
  summary?: Record<string, string>
  /** 成片相对 outputs/<run_id>/ 的路径（如 final.mp4），无时为 null/省略 */
  final_mp4?: string | null
  /** 封面图相对路径（如 images/xxx.png），用于首页项目卡 */
  cover_image?: string | null
}

export interface RunDetail {
  run_id: string
  out_dir: string
  topic: string
  duration?: number
  style?: string
  img_concurrency?: number
  video_concurrency?: number
  created_at: string | null
  steps: Record<string, StepRow>
  last_global_error?: string | null
  /** Step 5 完成后后端可写入的最终 mp4 相对路径 */
  final_mp4?: string | null
}

export interface ArtifactMediaRef {
  path: string
  label: string
  ref_id?: string
  prompt?: string
  updated_at?: string
}

export interface StepArtifacts {
  step: number
  text: string | null
  text_kind: string | null
  images: ArtifactMediaRef[]
  videos: ArtifactMediaRef[]
}

/** 审核结果（各步骤通用） */
export interface ReviewResult {
  passed?: boolean
  score?: number
  issues?: string[]
  revision_prompt?: string
  skipped?: boolean
  note?: string
}

/** 创意总监指导纲要 */
export interface DirectorGuidance {
  tone?: string
  visual_style?: string
  color_palette?: string
  pacing?: string
  key_themes?: string[]
  character_note?: string
  story_constraints?: string[]
  shot_advice?: string
  audio_direction?: string
  error?: string
}

/** API /api/runs/{runId}/reviews 返回 */
export interface RunReviews {
  director_guidance: DirectorGuidance | null
  reviews: Record<string, ReviewResult>
}

/** 运行在 outputs/<run_id> 下的文件的只读预览 URL */
export function fileUrl(runId: string, relPath: string): string {
  const q = encodeURIComponent(relPath.replace(/\\/g, "/"))
  return `${API_BASE}/api/runs/${encodeURIComponent(runId)}/file?path=${q}`
}

export interface SeedreamStatus {
  configured: boolean
  model: string
  default_model: string
  assets_dir: string
}

export interface SeedreamGenerateResult {
  ok: boolean
  asset_id: string
  filename: string
  rel_path: string
  path: string
  purpose: string
  model: string
  url: string
}

export async function getSeedreamStatus(): Promise<SeedreamStatus> {
  return apiJson("/api/seedream/status")
}

/** 获取所有步骤的审核结果和创意总监指导 */
export async function getRunReviews(runId: string): Promise<RunReviews> {
  return apiJson(`/api/runs/${encodeURIComponent(runId)}/reviews`)
}

/** 调用 Seedream 4.5 生成 UI 资产（落盘 outputs/_ui_assets） */
export async function postSeedreamGenerate(body: {
  prompt: string
  purpose?: string
  save_as?: string
  size?: string
  reference_paths?: string[]
}): Promise<SeedreamGenerateResult> {
  return apiJson("/api/seedream/generate", {
    method: "POST",
    body: JSON.stringify(body),
  })
}

/** 即时生图结果的预览 URL */
export function uiAssetUrl(filename: string): string {
  return `${API_BASE}/api/ui-assets/${encodeURIComponent(filename)}`
}
