import type { VideoPromptEdit } from "@/lib/artifact-parse"

import { EditSection, editTextareaMediumClass } from "./shared"

export function VideoPromptsEditor({
  items,
  onChange,
}: {
  items: VideoPromptEdit[]
  onChange: (next: VideoPromptEdit[]) => void
}) {
  return (
    <div className="space-y-4">
      {items.map((item, i) => {
        const label = item.key.replace(/^shot_/i, "分镜 ")
        const meta: string[] = []
        if (item.durationMs != null) meta.push(`时长约 ${Math.round(item.durationMs / 1000)} 秒`)
        if (item.charsInShot) meta.push(`角色/资产：${item.charsInShot}`)
        if (item.promptSource) meta.push(`来源：${item.promptSource}`)

        return (
          <EditSection key={item.key} title={label}>
            <textarea
              className={editTextareaMediumClass("text-xs")}
              value={item.prompt}
              onChange={(e) => {
                const next = [...items]
                next[i] = { ...item, prompt: e.target.value }
                onChange(next)
              }}
              placeholder="图生视频提示词"
            />
            <textarea
              className={editTextareaMediumClass("min-h-20 text-xs")}
              value={item.manualReferenceImagePaths}
              onChange={(e) => {
                const next = [...items]
                next[i] = { ...item, manualReferenceImagePaths: e.target.value }
                onChange(next)
              }}
              placeholder="manual_reference_image_paths，每行或用顿号/逗号分隔一个参考图路径"
            />
            {meta.length > 0 ? <p className="text-xs text-zinc-500">{meta.join(" · ")}</p> : null}
          </EditSection>
        )
      })}
    </div>
  )
}
