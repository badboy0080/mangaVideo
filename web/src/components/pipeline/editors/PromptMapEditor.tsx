import type { PromptMapEditState } from "@/lib/artifact-parse"

import { EditSection, editInputClass, editTextareaMediumClass, editItemFrameClass } from "./shared"

export function PromptMapEditor({
  state,
  onChange,
}: {
  state: PromptMapEditState
  onChange: (next: PromptMapEditState) => void
}) {
  return (
    <div className="space-y-4">
      {state.assets.length > 0 && (
        <EditSection title="资产提示词">
          {state.assets.map((item, i) => (
            <div key={item.tag} className={editItemFrameClass()}>
              <input
                className={editInputClass("font-medium")}
                value={item.name}
                onChange={(e) => {
                  const assets = [...state.assets]
                  assets[i] = { ...item, name: e.target.value }
                  onChange({ ...state, assets })
                }}
                placeholder="资产名称"
              />
              {item.tagLabel ? (
                <p className="text-xs text-zinc-500">标签：{item.tagLabel}</p>
              ) : null}
              <textarea
                className={editTextareaMediumClass("text-xs")}
                value={item.prompt}
                onChange={(e) => {
                  const assets = [...state.assets]
                  assets[i] = { ...item, prompt: e.target.value }
                  onChange({ ...state, assets })
                }}
                placeholder="生图提示词…"
              />
              {item.refs ? (
                <p className="text-xs text-zinc-500">关联分镜：{item.refs}</p>
              ) : null}
            </div>
          ))}
        </EditSection>
      )}

      {state.shots.length > 0 && (
        <EditSection title="分镜引用">
          {state.shots.map((item, i) => (
            <div key={item.key} className={editItemFrameClass("space-y-1")}>
              <input
                className={editInputClass("font-medium text-sm")}
                value={item.name}
                onChange={(e) => {
                  const shots = [...state.shots]
                  shots[i] = { ...item, name: e.target.value }
                  onChange({ ...state, shots })
                }}
                placeholder="分镜名称"
              />
              {item.refs ? (
                <p className="text-xs text-zinc-500">本镜资产：{item.refs}</p>
              ) : null}
            </div>
          ))}
        </EditSection>
      )}
    </div>
  )
}
