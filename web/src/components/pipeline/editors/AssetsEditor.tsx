import type { AssetItemEdit, AssetsEditState } from "@/lib/artifact-parse"

import { EditSection, editInputClass, editTextareaMediumClass, editItemFrameClass } from "./shared"

function AssetGroup({
  title,
  items,
  onChange,
}: {
  title: string
  items: AssetItemEdit[]
  onChange: (items: AssetItemEdit[]) => void
}) {
  if (items.length === 0) return null
  return (
    <EditSection title={title}>
      {items.map((item, i) => (
        <div key={`${item.name}-${i}`} className={editItemFrameClass()}>
          <input
            className={editInputClass("font-medium")}
            value={item.name}
            onChange={(e) => {
              const next = [...items]
              next[i] = { ...item, name: e.target.value }
              onChange(next)
            }}
            placeholder="名称"
          />
          <textarea
            className={editTextareaMediumClass("text-xs")}
            value={item.description}
            onChange={(e) => {
              const next = [...items]
              next[i] = { ...item, description: e.target.value }
              onChange(next)
            }}
            placeholder="描述…"
          />
          {item.refs ? (
            <p className="text-xs text-zinc-500">
              <span className="font-medium text-zinc-300">出现分镜：</span>
              {item.refs}
            </p>
          ) : null}
        </div>
      ))}
    </EditSection>
  )
}

export function AssetsEditor({
  state,
  onChange,
}: {
  state: AssetsEditState
  onChange: (next: AssetsEditState) => void
}) {
  return (
    <div className="space-y-4">
      <AssetGroup
        title="角色"
        items={state.characters}
        onChange={(characters) => onChange({ ...state, characters })}
      />
      <AssetGroup title="场景" items={state.scenes} onChange={(scenes) => onChange({ ...state, scenes })} />
      <AssetGroup title="道具" items={state.props} onChange={(props) => onChange({ ...state, props })} />
    </div>
  )
}
