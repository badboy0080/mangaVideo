/**
 * 与 steps/script_split.py 对齐：按行首「分镜 N｜X 秒」切块。
 */

export interface ScriptShotBlock {
  shotNum: string
  seconds: number | null
  headerLine: string
  body: string
}

const SHOT_HDR = /^\s*分镜\s*(\d+)\s*[｜|]\s*(\d+)\s*秒[^\r\n]*$/gm

export function splitShotsByHeaders(script: string): ScriptShotBlock[] {
  const spans: Array<{ start: number; end: number; shotNum: string; seconds: string; headerLine: string }> = []
  let m: RegExpExecArray | null
  const re = new RegExp(SHOT_HDR.source, SHOT_HDR.flags)
  while ((m = re.exec(script)) !== null) {
    spans.push({
      start: m.index,
      end: m.index + m[0].length,
      shotNum: m[1],
      seconds: m[2],
      headerLine: m[0].trimEnd(),
    })
  }
  if (spans.length === 0) return []

  return spans.map((span, i) => {
    const startBody = span.end
    const endBody = i + 1 < spans.length ? spans[i + 1].start : script.length
    const body = script.slice(startBody, endBody).trim()
    let sec: number | null = null
    const parsed = parseInt(span.seconds, 10)
    if (!Number.isNaN(parsed)) sec = Math.max(1, parsed)
    return {
      shotNum: span.shotNum.trim(),
      seconds: sec,
      headerLine: span.headerLine,
      body,
    }
  })
}

/** 无分镜标题行时，整篇作为一块可编辑正文 */
export function splitScriptForEdit(script: string): { preamble: string; shots: ScriptShotBlock[] } {
  const shots = splitShotsByHeaders(script)
  if (shots.length > 0) {
    const firstIdx = script.search(/^\s*分镜\s*\d+\s*[｜|]/m)
    const preamble = firstIdx > 0 ? script.slice(0, firstIdx).trimEnd() : ""
    return { preamble, shots }
  }
  return { preamble: script.trimEnd(), shots: [] }
}

export function mergeScriptBlocks(preamble: string, shots: ScriptShotBlock[]): string {
  const parts: string[] = []
  const pre = preamble.trimEnd()
  if (pre) parts.push(pre)
  for (const s of shots) {
    const header = s.headerLine.trim() || `分镜 ${s.shotNum}｜${s.seconds ?? 10} 秒`
    parts.push(`${header}\n${s.body.trim()}`.trim())
  }
  return parts.join("\n\n").trim()
}
