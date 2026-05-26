import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react"
import { Loader2 } from "lucide-react"

import { TextContentViewer } from "@/components/TextContentViewer"
import { PromptMapEditor } from "@/components/pipeline/editors/PromptMapEditor"
import { ResearchEditor } from "@/components/pipeline/editors/ResearchEditor"
import { VideoPromptsEditor } from "@/components/pipeline/editors/VideoPromptsEditor"
import { Button } from "@/components/ui/button"
import {
  type PromptMapEditState,
  type ResearchEditState,
  type VideoPromptEdit,
  isEditableStep,
  mergePromptMapJson,
  mergeResearchJson,
  mergeVideoPromptsJson,
  parsePromptMapJson,
  parseResearchJson,
  parseVideoPromptsJson,
} from "@/lib/artifact-parse"
import { putStepArtifactText } from "@/lib/api"
import { cn } from "@/lib/utils"

type PanelMode = "view" | "edit"

export interface EditableArtifactPanelProps {
  runId: string
  step: number
  label?: string
  text: string
  textKind?: string | null
  maxHeightClass?: string
  onSaved?: (step: number) => void
  onDirtyChange?: (dirty: boolean) => void
}

export function EditableArtifactPanel({
  runId,
  step,
  label = "文档",
  text,
  textKind,
  maxHeightClass = "max-h-[28rem]",
  onSaved,
  onDirtyChange,
}: EditableArtifactPanelProps) {
  const editable = isEditableStep(step)
  const [mode, setMode] = useState<PanelMode>("view")
  const [saving, setSaving] = useState(false)
  const [saveHint, setSaveHint] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [research, setResearch] = useState<ResearchEditState | null>(null)
  const [promptMap, setPromptMap] = useState<PromptMapEditState | null>(null)
  const [videoPrompts, setVideoPrompts] = useState<VideoPromptEdit[]>([])

  const baseline = useMemo(() => text.trim(), [text])

  const currentSerialized = useMemo(() => {
    try {
      if (step === 1 && research) return mergeResearchJson(text, research)
      if (step === 2 && promptMap) return mergePromptMapJson(text, promptMap)
      if (step === 4) return mergeVideoPromptsJson(text, videoPrompts)
    } catch {
      return baseline
    }
    return baseline
  }, [step, research, promptMap, videoPrompts, text, baseline])

  const dirty = mode === "edit" && currentSerialized.trim() !== baseline

  useEffect(() => {
    onDirtyChange?.(dirty)
  }, [dirty, onDirtyChange])

  useEffect(() => {
    if (mode !== "view") return
    setSaveHint(null)
    setError(null)
  }, [text, step, mode])

  const loadEditState = useCallback(() => {
    try {
      if (step === 1) setResearch(parseResearchJson(text))
      else if (step === 2) setPromptMap(parsePromptMapJson(text))
      else if (step === 4) setVideoPrompts(parseVideoPromptsJson(text))
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : "解析产物失败，无法进入编辑")
    }
  }, [step, text])

  const switchToView = () => {
    if (dirty) {
      if (!window.confirm("有未保存的修改，确定放弃吗？")) return
      cancelEdit()
      return
    }
    setMode("view")
  }

  const enterEdit = () => {
    loadEditState()
    setMode("edit")
    setSaveHint(null)
  }

  const cancelEdit = () => {
    setMode("view")
    setError(null)
    setSaveHint(null)
    loadEditState()
  }

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      let payload: string
      let kind: "json" | "markdown"
      if (step === 1 && research) {
        payload = mergeResearchJson(text, research)
        kind = "json"
      } else if (step === 2 && promptMap) {
        payload = mergePromptMapJson(text, promptMap)
        kind = "json"
      } else if (step === 4) {
        payload = mergeVideoPromptsJson(text, videoPrompts)
        kind = "json"
      } else {
        throw new Error("当前步骤不支持保存")
      }

      const res = await putStepArtifactText(runId, step, { text: payload, text_kind: kind })
      setMode("view")
      setSaveHint("已保存。若修改了内容，建议手动重新运行后续步骤。")
      if (res.downstream_steps?.length) {
        setSaveHint(
          `已保存。建议检查并重跑步骤 ${res.downstream_steps.join("、")}（若内容已变更）。`,
        )
      }
      onSaved?.(step)
    } catch (e) {
      setError(e instanceof Error ? e.message : "保存失败")
    } finally {
      setSaving(false)
    }
  }

  const renderEditor = () => {
    if (error) {
      return <p className="text-sm text-destructive">{error}</p>
    }
    if (step === 1 && research) {
      return <ResearchEditor state={research} onChange={setResearch} />
    }
    if (step === 2 && promptMap) {
      return <PromptMapEditor state={promptMap} onChange={setPromptMap} />
    }
    if (step === 4) {
      return <VideoPromptsEditor items={videoPrompts} onChange={setVideoPrompts} />
    }
    return <p className="text-sm text-muted-foreground">加载编辑区…</p>
  }

  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border shadow-inner",
        mode === "edit" && editable
          ? "border-zinc-800 bg-zinc-950/90"
          : "border-line-soft bg-background/60",
      )}
    >
      <div
        className={cn(
          "flex flex-wrap items-center justify-between gap-2 border-b px-3 py-2",
          mode === "edit" && editable ? "border-zinc-800 bg-zinc-900/50" : "border-line-soft",
        )}
      >
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        {editable && (
          <div className="flex flex-wrap items-center gap-1.5">
            <ModeTab active={mode === "view"} onClick={switchToView}>
              查看
            </ModeTab>
            <ModeTab active={mode === "edit"} onClick={enterEdit}>
              编辑
            </ModeTab>
          </div>
        )}
      </div>

      <div className="p-3">
        {saveHint && mode === "view" && (
          <p className="mb-3 rounded-md bg-accent-cool/10 px-3 py-2 text-xs text-accent-cool">{saveHint}</p>
        )}

        {mode === "view" || !editable ? (
          <TextContentViewer text={text} textKind={textKind} maxHeightClass={maxHeightClass} />
        ) : (
          <div className="min-h-[min(65vh,36rem)] max-h-[75vh] space-y-4 overflow-y-auto pr-1">
            {renderEditor()}
          </div>
        )}

        {mode === "edit" && editable && (
          <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-zinc-800 pt-3">
            <Button type="button" size="sm" disabled={saving || !dirty} onClick={() => void handleSave()}>
              {saving ? (
                <>
                  <Loader2 className="mr-1 size-3.5 animate-spin" aria-hidden />
                  保存中…
                </>
              ) : (
                "保存"
              )}
            </Button>
            <Button type="button" size="sm" variant="outline" disabled={saving} onClick={cancelEdit}>
              取消
            </Button>
            {dirty && !saving && (
              <span className="text-xs text-amber-600">有未保存的修改</span>
            )}
            {error && mode === "edit" && (
              <span className="text-xs text-destructive">{error}</span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function ModeTab({
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
