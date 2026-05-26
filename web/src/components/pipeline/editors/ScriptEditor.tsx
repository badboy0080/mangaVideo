import type { ScriptShotBlock } from "@/lib/script-split"

import { EditSection, editInputClass, editTextareaMediumClass, editTextareaTallClass } from "./shared"

export function ScriptEditor({
  preamble,
  shots,
  onPreambleChange,
  onShotsChange,
}: {
  preamble: string
  shots: ScriptShotBlock[]
  onPreambleChange: (v: string) => void
  onShotsChange: (v: ScriptShotBlock[]) => void
}) {
  const updateShot = (index: number, patch: Partial<ScriptShotBlock>) => {
    const next = [...shots]
    next[index] = { ...next[index], ...patch }
    onShotsChange(next)
  }

  return (
    <div className="space-y-4">
      {shots.length === 0 ? (
        <EditSection title="分镜正文">
          <textarea
            className={editTextareaTallClass("font-mono text-xs")}
            value={preamble}
            onChange={(e) => onPreambleChange(e.target.value)}
            placeholder="未识别到「分镜 N｜X 秒」标题行，可在此编辑全文…"
          />
        </EditSection>
      ) : (
        <>
          <EditSection title="标题与幕结构">
            <textarea
              className={editTextareaMediumClass("text-xs")}
              value={preamble}
              onChange={(e) => onPreambleChange(e.target.value)}
              placeholder="标题、分幕说明等（分镜标题行之前的内容）…"
            />
          </EditSection>
          {shots.map((shot, i) => (
            <EditSection
              key={`${shot.shotNum}-${i}`}
              title={`分镜 ${shot.shotNum}${shot.seconds != null ? ` · ${shot.seconds} 秒` : ""}`}
            >
              <input
                className={editInputClass("font-mono text-xs")}
                value={shot.headerLine}
                onChange={(e) => updateShot(i, { headerLine: e.target.value })}
                placeholder="分镜 N｜X 秒｜场景简述"
              />
              <textarea
                className={editTextareaMediumClass("text-xs")}
                value={shot.body}
                onChange={(e) => updateShot(i, { body: e.target.value })}
                placeholder="该镜表格、T2V/I2V 提示词等…"
              />
            </EditSection>
          ))}
        </>
      )}
    </div>
  )
}
