import { useEffect, useRef, useState } from "react"

import { cn } from "@/lib/utils"

export function normalizeRunTopic(topic: string | undefined): string {
  const t = (topic || "").trim()
  if (!t || t.includes("legacy")) return "未命名项目"
  return t
}

/** 顶栏展示：最多 5 个字，超出用 … */
export function truncateTopicDisplay(topic: string, maxLen = 5): string {
  const t = normalizeRunTopic(topic)
  if (t.length <= maxLen) return t
  return `${t.slice(0, maxLen)}...`
}

export interface ProjectRunTitleProps {
  topic: string | undefined
  saving?: boolean
  onSave: (nextTopic: string) => void | Promise<void>
  className?: string
}

/** 点击项目名称可编辑；展示时截断为 5 字 */
export function ProjectRunTitle({ topic, saving, onSave, className }: ProjectRunTitleProps) {
  const full = normalizeRunTopic(topic)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(full)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!editing) setDraft(full)
  }, [full, editing])

  useEffect(() => {
    if (editing) inputRef.current?.focus()
  }, [editing])

  const commit = async () => {
    const next = draft.trim() || "未命名项目"
    setEditing(false)
    if (next !== full) await onSave(next)
  }

  if (editing) {
    return (
      <input
        ref={inputRef}
        type="text"
        maxLength={200}
        disabled={saving}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={() => void commit()}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault()
            void commit()
          }
          if (e.key === "Escape") {
            setDraft(full)
            setEditing(false)
          }
        }}
        className={cn(
          "min-w-0 max-w-[min(100%,20rem)] rounded-md border border-line-soft bg-background/80 px-2 py-1 text-sm font-semibold text-foreground outline-none focus:ring-2 focus:ring-accent-cool/35",
          className,
        )}
        aria-label="项目名称"
      />
    )
  }

  return (
    <button
      type="button"
      title={`${full}（点击修改名称）`}
      disabled={saving}
      onClick={() => setEditing(true)}
      className={cn(
        "min-w-0 truncate text-left font-semibold tracking-tight text-foreground transition-colors hover:text-accent-cool focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cool/35 focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        "[font-size:clamp(1rem,2vw,1.35rem)] leading-tight",
        className,
      )}
    >
      {truncateTopicDisplay(full)}
    </button>
  )
}
