/**
 * 将流水线 JSON 产物转为易读 Markdown（不展示 JSON 字段名堆叠）。
 */

function looksLikeMarkdown(s: string): boolean {
  const t = s.trim()
  return /^#{1,6}\s/m.test(t) || /\*\*[^*]+\*\*/.test(t) || /^-\s/m.test(t) || /^---\s*$/m.test(t)
}

function basename(path: string): string {
  const p = path.replace(/\\/g, "/")
  return p.split("/").pop() ?? path
}

function joinRefs(refs: unknown): string {
  if (!Array.isArray(refs) || refs.length === 0) return ""
  return refs.map(String).join("、")
}

function normalizeMarkdownBlock(s: string): string {
  return s.replace(/\r\n/g, "\n").trim()
}

function researchToMarkdown(obj: Record<string, unknown>): string {
  const brief = typeof obj.creative_brief === "string" ? normalizeMarkdownBlock(obj.creative_brief) : ""
  if (brief) return brief
  const parts: string[] = []
  const findings = obj.findings
  if (Array.isArray(findings)) {
    for (const item of findings) {
      if (!item || typeof item !== "object") continue
      const row = item as Record<string, unknown>
      const content = typeof row.content === "string" ? normalizeMarkdownBlock(row.content) : ""
      if (!content || content === brief) continue
      const ft = typeof row.title === "string" ? row.title : "补充说明"
      parts.push("")
      parts.push(`## ${ft}`)
      parts.push(content)
    }
  }

  return parts.join("\n\n").trim()
}

function assetListToMarkdown(
  items: unknown,
  sectionTitle: string,
): string {
  if (!Array.isArray(items) || items.length === 0) return ""
  const blocks: string[] = [`## ${sectionTitle}`]
  for (const item of items) {
    if (!item || typeof item !== "object") continue
    const row = item as Record<string, unknown>
    const name = typeof row.name === "string" ? row.name : sectionTitle
    blocks.push(`### ${name}`)
    if (typeof row.description === "string" && row.description.trim()) {
      blocks.push(row.description.trim())
    }
    const refs = joinRefs(row.refs ?? row.refs_from_script)
    if (refs) blocks.push(`**出现分镜：** ${refs}`)
  }
  return blocks.join("\n\n")
}

function assetsToMarkdown(obj: Record<string, unknown>): string {
  const parts = [
    "# 资产清单",
    assetListToMarkdown(obj.characters, "角色"),
    assetListToMarkdown(obj.scenes, "场景"),
    assetListToMarkdown(obj.props, "道具"),
  ].filter(Boolean)
  return parts.join("\n\n").trim()
}

function promptMapToMarkdown(obj: Record<string, unknown>): string {
  const parts: string[] = []

  const script = typeof obj.script === "string" ? normalizeMarkdownBlock(obj.script) : ""
  if (script) {
    parts.push(script)
  }

  const assets = obj.assets
  if (assets && typeof assets === "object") {
    parts.push("")
    parts.push("## 资产提示词")
    const entries = Object.entries(assets as Record<string, unknown>).sort(([a], [b]) => a.localeCompare(b, "zh"))
    for (const [tag, raw] of entries) {
      if (!raw || typeof raw !== "object") continue
      const row = raw as Record<string, unknown>
      const name = typeof row.name === "string" ? row.name : tag
      const tagLabel = typeof row.tag === "string" ? row.tag : ""
      parts.push("")
      parts.push(`### ${name}${tagLabel ? `（${tagLabel}）` : ""}`)
      const body =
        (typeof row.prompt === "string" && row.prompt.trim()) ||
        (typeof row.description === "string" && row.description.trim()) ||
        ""
      if (body) parts.push(body)
      const refs = joinRefs(row.refs_from_script)
      if (refs) parts.push(`**关联分镜：** ${refs}`)
    }
  }

  const shots = obj.shots
  if (shots && typeof shots === "object") {
    parts.push("")
    parts.push("## 分镜引用")
    const entries = Object.entries(shots as Record<string, unknown>).sort(([a], [b]) => a.localeCompare(b))
    for (const [, raw] of entries) {
      if (!raw || typeof raw !== "object") continue
      const row = raw as Record<string, unknown>
      const num = row.shot_num ?? "?"
      const name = typeof row.name === "string" ? row.name : `分镜 ${num}`
      parts.push("")
      parts.push(`### ${name}`)
      const refs = joinRefs(row.refs_in_shot)
      if (refs) parts.push(`**本镜资产：** ${refs}`)
    }
  }

  return parts.join("\n\n").trim()
}

function videoPromptsToMarkdown(obj: Record<string, unknown>): string {
  const parts: string[] = []
  const entries = Object.entries(obj).sort(([a], [b]) => a.localeCompare(b))
  for (const [key, raw] of entries) {
    if (!raw || typeof raw !== "object") continue
    const row = raw as Record<string, unknown>
    const label = key.replace(/^shot_/i, "分镜 ")
    parts.push("")
    parts.push(`## ${label}`)
    const prompt = typeof row.prompt === "string" ? row.prompt.trim() : ""
    if (prompt) parts.push(prompt)
  }
  return parts.join("\n\n").trim()
}

function imgResultsToMarkdown(obj: Record<string, unknown>): string {
  const parts: string[] = ["# 生图结果", "", "| 名称 | 输出文件 |", "| --- | --- |"]
  const seen = new Set<string>()
  for (const [name, path] of Object.entries(obj)) {
    if (typeof path !== "string") continue
    const file = basename(path)
    const rowKey = `${name}::${file}`
    if (seen.has(rowKey)) continue
    seen.add(rowKey)
    parts.push(`| ${name} | ${file} |`)
  }
  return parts.join("\n")
}

function genericValueToMarkdown(value: unknown, depth = 0): string {
  if (value == null) return ""
  if (typeof value === "string") {
    if (looksLikeMarkdown(value)) return normalizeMarkdownBlock(value)
    return value.trim()
  }
  if (typeof value === "number" || typeof value === "boolean") return String(value)
  if (Array.isArray(value)) {
    if (value.every((x) => typeof x === "string" || typeof x === "number")) {
      return value.map(String).join("、")
    }
    return value
      .map((item, i) => {
        const body = genericValueToMarkdown(item, depth + 1)
        if (!body) return ""
        const heading = depth === 0 ? `## 第 ${i + 1} 项` : `-`
        return depth === 0 ? `${heading}\n\n${body}` : `- ${body.replace(/\n/g, "\n  ")}`
      })
      .filter(Boolean)
      .join("\n\n")
  }
  if (typeof value === "object") {
    const obj = value as Record<string, unknown>
    const blocks: string[] = []
    for (const [k, v] of Object.entries(obj)) {
      const body = genericValueToMarkdown(v, depth + 1)
      if (!body) continue
      if (depth === 0 && looksLikeMarkdown(body) && body.startsWith("#")) {
        blocks.push(body)
        continue
      }
      const headingLevel = depth === 0 ? "##" : "###"
      blocks.push(`${headingLevel} ${k}\n\n${body}`)
    }
    return blocks.join("\n\n")
  }
  return String(value)
}

function detectShape(obj: Record<string, unknown>): string {
  if ("creative_brief" in obj || ("findings" in obj && "topic" in obj)) return "research"
  if ("characters" in obj || "scenes" in obj || "props" in obj) return "assets"
  if ("assets" in obj && "shots" in obj) return "prompt_map"
  if (Object.keys(obj).some((k) => /^shot_/i.test(k) && typeof obj[k] === "object")) return "video_prompts"
  if (Object.values(obj).every((v) => typeof v === "string" && (v.includes("/") || v.includes("\\")))) {
    return "img_results"
  }
  return "generic"
}

/** 解析 JSON 字符串为排版好的 Markdown；失败返回 null */
export function jsonToReadableMarkdown(raw: string): string | null {
  const trimmed = raw.trim()
  if (!trimmed) return null
  try {
    const parsed = JSON.parse(trimmed) as unknown
    if (parsed == null) return null
    if (typeof parsed === "string") {
      return looksLikeMarkdown(parsed) ? normalizeMarkdownBlock(parsed) : parsed
    }
    if (typeof parsed !== "object" || Array.isArray(parsed)) {
      return genericValueToMarkdown(parsed)
    }
    const obj = parsed as Record<string, unknown>
    switch (detectShape(obj)) {
      case "research":
        return researchToMarkdown(obj)
      case "assets":
        return assetsToMarkdown(obj)
      case "prompt_map":
        return promptMapToMarkdown(obj)
      case "video_prompts":
        return videoPromptsToMarkdown(obj)
      case "img_results":
        return imgResultsToMarkdown(obj)
      default:
        return genericValueToMarkdown(obj)
    }
  } catch {
    return null
  }
}
