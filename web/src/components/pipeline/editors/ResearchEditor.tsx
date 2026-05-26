import type { ResearchEditState } from "@/lib/artifact-parse"

import { EditSection, MetaLine, editInputClass, editTextareaMediumClass, editTextareaTallClass } from "./shared"

export function ResearchEditor({
  state,
  onChange,
}: {
  state: ResearchEditState
  onChange: (next: ResearchEditState) => void
}) {
  const meta: string[] = []
  if (state.topic) meta.push(`主题：${state.topic}`)
  if (state.style) meta.push(`风格：${state.style}`)
  if (state.durationSeconds != null) meta.push(`时长：${state.durationSeconds} 秒`)

  return (
    <div className="space-y-4">
      {meta.length > 0 && (
        <EditSection title="项目信息（只读）">
          <MetaLine label="摘要" value={meta.join("　·　")} />
        </EditSection>
      )}

      <EditSection title="剧本纲要">
        <textarea
          className={editTextareaTallClass("font-mono text-xs")}
          value={state.creativeBrief}
          onChange={(e) => onChange({ ...state, creativeBrief: e.target.value })}
          placeholder="剧本纲要正文…"
        />
      </EditSection>

      {state.findings.length > 0 && (
        <EditSection title="补充说明">
          {state.findings.map((f, i) => (
            <div key={i} className="space-y-2 rounded-md border border-zinc-800/80 bg-zinc-900/50 p-3">
              <input
                className={editInputClass("font-medium")}
                value={f.title}
                onChange={(e) => {
                  const findings = [...state.findings]
                  findings[i] = { ...f, title: e.target.value }
                  onChange({ ...state, findings })
                }}
                placeholder="小节标题"
              />
              <textarea
                className={editTextareaMediumClass("text-xs")}
                value={f.content}
                onChange={(e) => {
                  const findings = [...state.findings]
                  findings[i] = { ...f, content: e.target.value }
                  onChange({ ...state, findings })
                }}
                placeholder="正文…"
              />
            </div>
          ))}
        </EditSection>
      )}
    </div>
  )
}
