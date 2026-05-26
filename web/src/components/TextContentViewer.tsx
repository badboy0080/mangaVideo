import { useEffect, useMemo, useState, type ReactNode } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import { jsonToReadableMarkdown } from "@/lib/json-to-markdown"

export type TextViewMode = "plain" | "markdown" | "json"

function defaultMode(textKind: string | null | undefined): TextViewMode {
  if (textKind === "markdown" || textKind === "json") return "markdown"
  return "plain"
}

function tryFormatJson(raw: string): string | null {
  try {
    return JSON.stringify(JSON.parse(raw), null, 2)
  } catch {
    return null
  }
}

interface TextContentViewerProps {
  text: string
  /** 后端 text_kind：markdown | json 等 */
  textKind?: string | null
  /** 是否显示 Markdown 切换（运行日志可开） */
  allowMarkdown?: boolean
  allowJsonFormat?: boolean
  maxHeightClass?: string
  emptyLabel?: string
}

export function TextContentViewer({
  text,
  textKind,
  allowMarkdown = true,
  allowJsonFormat = true,
  maxHeightClass = "max-h-64",
  emptyLabel = "（无内容）",
}: TextContentViewerProps) {
  const [mode, setMode] = useState<TextViewMode>(() => defaultMode(textKind))

  useEffect(() => {
    setMode(defaultMode(textKind))
  }, [text, textKind])

  const formattedJson = useMemo(
    () => (textKind === "json" || allowJsonFormat ? tryFormatJson(text) : null),
    [text, textKind, allowJsonFormat],
  )

  const readableMarkdown = useMemo(() => {
    if (textKind === "json") {
      return jsonToReadableMarkdown(text) ?? text
    }
    return text
  }, [text, textKind])

  const docTabLabel = textKind === "json" ? "文档" : "Markdown"
  const showMarkdownTab = allowMarkdown
  const showJsonTab = allowJsonFormat && formattedJson != null

  if (!text.trim()) {
    return <p className="text-xs text-muted-foreground">{emptyLabel}</p>
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5">
        {showMarkdownTab && (
          <ViewTab active={mode === "markdown"} onClick={() => setMode("markdown")}>
            {docTabLabel}
          </ViewTab>
        )}
        {showJsonTab && (
          <ViewTab active={mode === "json"} onClick={() => setMode("json")}>
            JSON 格式化
          </ViewTab>
        )}
        <ViewTab active={mode === "plain"} onClick={() => setMode("plain")}>
          原文
        </ViewTab>
      </div>

      {mode === "markdown" && showMarkdownTab ? (
        <div
          className={`markdown-body overflow-auto rounded-md border border-line-soft bg-background/70 px-3 py-2 text-sm ${maxHeightClass}`}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{readableMarkdown}</ReactMarkdown>
        </div>
      ) : mode === "json" && showJsonTab && formattedJson ? (
        <pre
          className={`overflow-auto rounded-md bg-background/70 p-2 font-mono text-xs whitespace-pre-wrap ${maxHeightClass}`}
        >
          {formattedJson}
        </pre>
      ) : (
        <pre
          className={`overflow-auto rounded-md bg-background/70 p-2 text-xs whitespace-pre-wrap ${maxHeightClass}`}
        >
          {text}
        </pre>
      )}
    </div>
  )
}

function ViewTab({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        active
          ? "rounded-md bg-background px-2.5 py-1 text-xs font-medium text-foreground shadow-sm ring-1 ring-line-soft"
          : "rounded-md px-2.5 py-1 text-xs text-muted-foreground hover:bg-background/60 hover:text-foreground"
      }
    >
      {children}
    </button>
  )
}
