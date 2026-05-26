import { useEffect, useState } from "react"
import { X } from "lucide-react"

import { cn } from "@/lib/utils"

export interface ArtifactMediaCardProps {
  kind: "image" | "video"
  src: string
  label: string
  className?: string
}

/** 图片 / 视频产物卡片 */
export function ArtifactMediaCard({ kind, src, label, className }: ArtifactMediaCardProps) {
  const [previewOpen, setPreviewOpen] = useState(false)

  useEffect(() => {
    if (!previewOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setPreviewOpen(false)
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [previewOpen])

  return (
    <>
      <div
        className={cn(
          "overflow-hidden rounded-xl border border-line-soft bg-background/50 shadow-none transition-shadow hover:shadow-sm",
          className,
        )}
      >
        {kind === "image" ? (
          <button type="button" className="block w-full text-left" onClick={() => setPreviewOpen(true)}>
            <img src={src} alt={label} className="aspect-[4/3] w-full object-cover" loading="lazy" />
          </button>
        ) : (
          <video src={src} controls className="aspect-video w-full bg-black/40" preload="metadata" />
        )}
        <p className="truncate border-t border-line-soft px-3 py-2 text-[11px] text-muted-foreground">{label}</p>
      </div>

      {previewOpen && kind === "image" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true">
          <button
            type="button"
            className="absolute inset-0 bg-black/85 backdrop-blur-sm"
            aria-label="关闭预览"
            onClick={() => setPreviewOpen(false)}
          />
          <button
            type="button"
            className="absolute right-5 top-5 z-[2] rounded-full bg-background p-2 shadow-lg hover:bg-muted"
            aria-label="关闭"
            onClick={() => setPreviewOpen(false)}
          >
            <X className="size-5" />
          </button>
          <img
            src={src}
            alt={label}
            className="relative z-[1] max-h-[90vh] max-w-full rounded-lg object-contain shadow-2xl"
          />
        </div>
      )}
    </>
  )
}
