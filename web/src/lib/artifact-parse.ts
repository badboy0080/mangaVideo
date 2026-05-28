export interface ResearchFindingEdit {
  title: string
  content: string
}

export interface ResearchEditState {
  topic: string
  style: string
  durationSeconds: number | null
  creativeBrief: string
  findings: ResearchFindingEdit[]
}

export interface AssetItemEdit {
  name: string
  description: string
  refs: string
}

export interface AssetsEditState {
  characters: AssetItemEdit[]
  scenes: AssetItemEdit[]
  props: AssetItemEdit[]
}

export interface PromptAssetEdit {
  tag: string
  name: string
  tagLabel: string
  prompt: string
  refs: string
}

export interface PromptShotEdit {
  key: string
  shotNum: string | number
  name: string
  refs: string
}

export interface PromptMapEditState {
  assets: PromptAssetEdit[]
  shots: PromptShotEdit[]
}

export interface VideoPromptEdit {
  key: string
  prompt: string
  durationMs: number | null
  charsInShot: string
  manualReferenceImagePaths: string
  promptSource: string
}

function joinRefs(refs: unknown): string {
  if (!Array.isArray(refs) || refs.length === 0) return ""
  return refs.map(String).join("\n")
}

function parseRefsText(text: string): string[] {
  return text
    .split(/[\n,，、]+/)
    .map((s) => s.trim())
    .filter(Boolean)
}

export function parseResearchJson(raw: string): ResearchEditState {
  const obj = JSON.parse(raw) as Record<string, unknown>
  const findings: ResearchFindingEdit[] = []
  if (Array.isArray(obj.findings)) {
    for (const item of obj.findings) {
      if (!item || typeof item !== "object") continue
      const row = item as Record<string, unknown>
      findings.push({
        title: typeof row.title === "string" ? row.title : "补充说明",
        content: typeof row.content === "string" ? row.content : "",
      })
    }
  }
  return {
    topic:
      (typeof obj.theme === "string" && obj.theme) ||
      (typeof obj.topic === "string" ? obj.topic : ""),
    style: typeof obj.style === "string" ? obj.style : "",
    durationSeconds: typeof obj.duration_seconds === "number" ? obj.duration_seconds : null,
    creativeBrief:
      (typeof obj.body === "string" && obj.body) ||
      (typeof obj.creative_brief === "string" ? obj.creative_brief : ""),
    findings,
  }
}

export function mergeResearchJson(raw: string, state: ResearchEditState): string {
  const obj = JSON.parse(raw) as Record<string, unknown>
  obj.theme = state.topic
  obj.topic = state.topic
  obj.body = state.creativeBrief
  obj.creative_brief = state.creativeBrief
  const prevFindings = Array.isArray(obj.findings) ? obj.findings : []
  obj.findings = state.findings.map((f, i) => {
    const orig =
      prevFindings[i] && typeof prevFindings[i] === "object"
        ? (prevFindings[i] as Record<string, unknown>)
        : {}
    return { ...orig, title: f.title, content: f.content }
  })
  return JSON.stringify(obj, null, 2)
}

export function parsePromptMapJson(raw: string): PromptMapEditState {
  const obj = JSON.parse(raw) as Record<string, unknown>
  const assets: PromptAssetEdit[] = []
  if (obj.assets && typeof obj.assets === "object") {
    for (const [tag, rawRow] of Object.entries(obj.assets as Record<string, unknown>).sort(([a], [b]) =>
      a.localeCompare(b, "zh"),
    )) {
      if (!rawRow || typeof rawRow !== "object") continue
      const row = rawRow as Record<string, unknown>
      assets.push({
        tag,
        name: typeof row.name === "string" ? row.name : tag,
        tagLabel: typeof row.tag === "string" ? row.tag : "",
        prompt:
          (typeof row.prompt === "string" && row.prompt) ||
          (typeof row.description === "string" && row.description) ||
          "",
        refs: joinRefs(row.refs_from_script),
      })
    }
  }
  const shots: PromptShotEdit[] = []
  if (obj.shots && typeof obj.shots === "object") {
    for (const [key, rawRow] of Object.entries(obj.shots as Record<string, unknown>).sort(([a], [b]) =>
      a.localeCompare(b),
    )) {
      if (!rawRow || typeof rawRow !== "object") continue
      const row = rawRow as Record<string, unknown>
      shots.push({
        key,
        shotNum: row.shot_num != null ? String(row.shot_num) : "?",
        name: typeof row.name === "string" ? row.name : key,
        refs: joinRefs(row.refs_in_shot),
      })
    }
  }
  return { assets, shots }
}

export function mergePromptMapJson(raw: string, state: PromptMapEditState): string {
  const obj = JSON.parse(raw) as Record<string, unknown>
  const assetsObj =
    obj.assets && typeof obj.assets === "object" ? (obj.assets as Record<string, unknown>) : {}
  for (const item of state.assets) {
    const existing =
      assetsObj[item.tag] && typeof assetsObj[item.tag] === "object"
        ? (assetsObj[item.tag] as Record<string, unknown>)
        : {}
    assetsObj[item.tag] = {
      ...existing,
      name: item.name,
      prompt: item.prompt,
      ...(item.tagLabel ? { tag: item.tagLabel } : {}),
    }
  }
  obj.assets = assetsObj

  const shotsObj =
    obj.shots && typeof obj.shots === "object" ? (obj.shots as Record<string, unknown>) : {}
  for (const item of state.shots) {
    const existing =
      shotsObj[item.key] && typeof shotsObj[item.key] === "object"
        ? (shotsObj[item.key] as Record<string, unknown>)
        : {}
    shotsObj[item.key] = { ...existing, name: item.name }
  }
  obj.shots = shotsObj
  return JSON.stringify(obj, null, 2)
}

export function parseVideoPromptsJson(raw: string): VideoPromptEdit[] {
  const obj = JSON.parse(raw) as Record<string, unknown>
  return Object.entries(obj)
    .filter(([, v]) => v && typeof v === "object")
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, rawRow]) => {
      const row = rawRow as Record<string, unknown>
      return {
        key,
        prompt: typeof row.prompt === "string" ? row.prompt : "",
        durationMs: typeof row.duration_ms === "number" ? row.duration_ms : null,
        charsInShot: joinRefs(row.chars_in_shot),
        manualReferenceImagePaths: joinRefs(row.manual_reference_image_paths),
        promptSource: typeof row.prompt_source === "string" ? row.prompt_source : "",
      }
    })
}

export function mergeVideoPromptsJson(raw: string, items: VideoPromptEdit[]): string {
  const obj = JSON.parse(raw) as Record<string, unknown>
  for (const item of items) {
    const existing =
      obj[item.key] && typeof obj[item.key] === "object" ? (obj[item.key] as Record<string, unknown>) : {}
    obj[item.key] = {
      ...existing,
      prompt: item.prompt,
      manual_reference_image_paths: parseRefsText(item.manualReferenceImagePaths),
    }
  }
  return JSON.stringify(obj, null, 2)
}

export function primaryBodyForStep(step: number, raw: string): string {
  const obj = JSON.parse(raw) as Record<string, unknown>
  if (step === 1) {
    return (
      (typeof obj.body === "string" && obj.body) ||
      (typeof obj.creative_brief === "string" && obj.creative_brief) ||
      ""
    )
  }
  if (step === 2) {
    return typeof obj.script === "string" ? obj.script : ""
  }
  if (step === 4) {
    return Object.entries(obj)
      .filter(([, v]) => v && typeof v === "object")
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, rawRow]) => {
        const row = rawRow as Record<string, unknown>
        const prompt = typeof row.prompt === "string" ? row.prompt.trim() : ""
        return prompt ? `## ${key.replace(/^shot_/i, "分镜 ")}\n\n${prompt}` : ""
      })
      .filter(Boolean)
      .join("\n\n")
  }
  return ""
}

export function mergePrimaryBodyJson(step: number, raw: string, body: string): string {
  const obj = JSON.parse(raw) as Record<string, unknown>
  if (step === 1) {
    obj.body = body
    obj.creative_brief = body
    if (Array.isArray(obj.findings) && obj.findings[0] && typeof obj.findings[0] === "object") {
      ;(obj.findings[0] as Record<string, unknown>).content = body
    }
    return JSON.stringify(obj, null, 2)
  }
  if (step === 2) {
    obj.script = body
    return JSON.stringify(obj, null, 2)
  }
  if (step === 4) {
    const sections = body
      .split(/(?=^##\s+)/m)
      .map((s) => s.trim())
      .filter(Boolean)
    if (sections.length) {
      for (const section of sections) {
        const m = section.match(/^##\s+(.+?)\s*\n+([\s\S]*)$/)
        if (!m) continue
        const label = m[1].trim()
        const shotId = /^shot_/i.test(label)
          ? label
          : `shot_${String(label.replace(/[^\d]/g, "") || "").padStart(2, "0")}`
        if (!/^shot_\d+/i.test(shotId)) continue
        const existing =
          obj[shotId] && typeof obj[shotId] === "object" ? (obj[shotId] as Record<string, unknown>) : {}
        obj[shotId] = { ...existing, prompt: m[2].trim() }
      }
      return JSON.stringify(obj, null, 2)
    }
    const firstKey = Object.keys(obj).find((k) => /^shot_/i.test(k))
    if (firstKey) {
      const existing =
        obj[firstKey] && typeof obj[firstKey] === "object" ? (obj[firstKey] as Record<string, unknown>) : {}
      obj[firstKey] = { ...existing, prompt: body }
    }
    return JSON.stringify(obj, null, 2)
  }
  return raw
}

export function isEditableStep(step: number): boolean {
  return step === 1 || step === 2 || step === 4
}
