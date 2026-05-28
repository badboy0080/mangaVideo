import { useEffect, useState } from "react"
import { Check, Edit3, Loader2, RefreshCw, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export interface ArtifactMediaCardProps {
  kind: "image" | "video"
  src: string
  label: string
  prompt?: string
  regenerateDisabled?: boolean
  onRegenerate?: (prompt: string) => Promise<void>
  className?: string
}

/** 图片 / 视频产物卡片 */
export function ArtifactMediaCard({
  kind,
  src,
  label,
  prompt = "",
  regenerateDisabled,
  onRegenerate,
  className,
}: ArtifactMediaCardProps) {
  const [previewOpen, setPreviewOpen] = useState(false)
  const [editingPrompt, setEditingPrompt] = useState(false)
  const [draftPrompt, setDraftPrompt] = useState(prompt)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setDraftPrompt(prompt)
    setEditingPrompt(false)
    setError(null)
  }, [prompt, src])

  useEffect(() => {
    if (!previewOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setPreviewOpen(false)
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [previewOpen])

  const canRegenerate = kind === "image" && Boolean(onRegenerate)

  const handleRegenerate = async () => {
    if (!onRegenerate) return
    const nextPrompt = draftPrompt.trim()
    if (!nextPrompt) {
      setError("提示词不能为空")
      return
    }
    setBusy(true)
    setError(null)
    try {
      await onRegenerate(nextPrompt)
      setEditingPrompt(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : "重新生成失败")
    } finally {
      setBusy(false)
    }
  }

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

        {kind === "image" && prompt.trim() ? (
          <div className="space-y-2 border-t border-line-soft px-3 py-3">
            <div className="flex items-center justify-between gap-2">
              <p className="text-[11px] font-medium text-muted-foreground">生成提示词</p>
              {canRegenerate ? (
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className="h-7 gap-1 px-2 text-xs"
                  disabled={busy || regenerateDisabled}
                  onClick={() => {
                    setEditingPrompt((v) => !v)
                    setError(null)
                  }}
                >
                  {editingPrompt ? <Check className="size-3" aria-hidden /> : <Edit3 className="size-3" aria-hidden />}
                  {editingPrompt ? "完成" : "修改"}
                </Button>
              ) : null}
            </div>

            {editingPrompt ? (
              <textarea
                value={draftPrompt}
                onChange={(e) => setDraftPrompt(e.target.value)}
                className="min-h-28 w-full resize-y rounded-md border border-line-soft bg-background/80 px-2 py-2 text-xs leading-relaxed text-foreground outline-none focus:border-accent-cool focus:ring-2 focus:ring-accent-cool/20"
              />
            ) : (
              <p className="line-clamp-4 whitespace-pre-wrap text-xs leading-relaxed text-muted-foreground">{prompt}</p>
            )}

            {canRegenerate ? (
              <div className="flex items-center justify-end gap-2">
                {error && <span className="min-w-0 flex-1 text-xs text-destructive">{error}</span>}
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="h-7 gap-1 text-xs"
                  disabled={busy || regenerateDisabled || !draftPrompt.trim()}
                  onClick={() => void handleRegenerate()}
                >
                  {busy ? (
                    <Loader2 className="size-3 animate-spin" aria-hidden />
                  ) : (
                    <RefreshCw className="size-3" aria-hidden />
                  )}
                  重新生成
                </Button>
              </div>
            ) : null}
          </div>
        ) : null}
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
