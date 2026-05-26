import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

/** 分段编辑外层卡片：暗色底框 */
export function EditSection({
  title,
  children,
  className,
}: {
  title: string
  children: ReactNode
  className?: string
}) {
  return (
    <section
      className={cn(
        "overflow-hidden rounded-lg border border-zinc-800/90 bg-zinc-950/75 shadow-inner",
        className,
      )}
    >
      <h4 className="border-b border-zinc-800/80 bg-zinc-900/60 px-3 py-2 text-xs font-semibold text-zinc-100">
        {title}
      </h4>
      <div className="space-y-3 p-3">{children}</div>
    </section>
  )
}

/** 编辑区内嵌小块（如 findings 条目） */
export function editItemFrameClass(extra = ""): string {
  return cn(
    "space-y-2 rounded-md border border-zinc-800/80 bg-zinc-900/50 p-3",
    extra,
  )
}

/** 主内容 textarea：暗色、可拉高、编辑时默认展示更多行 */
export function editTextareaClass(extra = ""): string {
  return cn(
    "w-full min-h-[12rem] resize-y rounded-md border border-zinc-700/80 bg-zinc-900/90 px-3 py-2.5 text-sm leading-relaxed text-zinc-100",
    "placeholder:text-zinc-500 outline-none transition-colors",
    "focus:border-accent-cool/55 focus:ring-2 focus:ring-accent-cool/25",
    extra,
  )
}

/** 长文档主编辑框（剧本纲要、分镜全文等） */
export function editTextareaTallClass(extra = ""): string {
  return editTextareaClass(cn("min-h-[min(50vh,28rem)] max-h-[70vh]", extra))
}

/** 分镜块 / 补充说明等中等高度 */
export function editTextareaMediumClass(extra = ""): string {
  return editTextareaClass(cn("min-h-[min(36vh,18rem)] max-h-[60vh]", extra))
}

export function editInputClass(extra = ""): string {
  return cn(
    "w-full rounded-md border border-zinc-700/80 bg-zinc-900/90 px-3 py-1.5 text-sm text-zinc-100",
    "placeholder:text-zinc-500 outline-none transition-colors",
    "focus:border-accent-cool/55 focus:ring-2 focus:ring-accent-cool/25",
    extra,
  )
}

export function MetaLine({ label, value }: { label: string; value: string }) {
  return (
    <p className="text-xs text-zinc-400">
      <span className="font-medium text-zinc-200">{label}：</span>
      {value || "—"}
    </p>
  )
}
