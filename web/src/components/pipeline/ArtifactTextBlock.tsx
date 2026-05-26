import { TextContentViewer } from "@/components/TextContentViewer"

export interface ArtifactTextBlockProps {
  label?: string
  text: string
  textKind?: string | null
  maxHeightClass?: string
}

/** 产物文本：固定边框的展示框，默认展开 Markdown/原文切换 */
export function ArtifactTextBlock({
  label = "文本",
  text,
  textKind,
  maxHeightClass = "max-h-[28rem]",
}: ArtifactTextBlockProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-line-soft bg-background/60">
      <p className="border-b border-line-soft px-3 py-2 text-xs font-medium text-muted-foreground">{label}</p>
      <div className="p-3">
        <TextContentViewer text={text} textKind={textKind} maxHeightClass={maxHeightClass} />
      </div>
    </div>
  )
}
