import { Loader2, Play, PlayCircle } from "lucide-react"

import { EditableArtifactPanel } from "@/components/pipeline/EditableArtifactPanel"
import { ArtifactMediaCard } from "@/components/pipeline/ArtifactMediaCard"
import { ReviewBadge, ScoreBar } from "@/components/pipeline/ReviewBadge"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { isEditableStep } from "@/lib/artifact-parse"
import { fileUrl, postRegenerateStep3Image } from "@/lib/api"
import type { ReviewResult, RunDetail, RunReviews, StepArtifacts, StepRow, StepStatus } from "@/lib/api"
import { stepTitleZh } from "@/lib/step-labels"
import { cn } from "@/lib/utils"

function statusVariant(
  s: StepStatus,
): "outline" | "secondary" | "success" | "destructive" | "warning" | "muted" {
  switch (s) {
    case "success":
      return "success"
    case "failed":
      return "destructive"
    case "running":
      return "warning"
    case "cancelled":
      return "outline"
    default:
      return "muted"
  }
}

export interface StepArtifactsPanelProps {
  detail: RunDetail
  artByStep: Record<string, StepArtifacts>
  activeStep: number
  runReviews?: RunReviews | null
  onArtifactSaved?: (step: number) => void
  onDirtyChange?: (dirty: boolean) => void
  onRunStep?: (step: number) => void
  onRewriteStep1FromReview?: () => void
  onRunAll?: () => void
  runningStep?: boolean
  rewritingStep1?: boolean
  runningAll?: boolean
  pipelineBusy?: boolean
}

function StepBlock({
  stepNum,
  row,
  detail,
  arts,
  isActive,
  review,
  onArtifactSaved,
  onDirtyChange,
  onRunStep,
  onRewriteStep1FromReview,
  runningStep,
  rewritingStep1,
  pipelineBusy,
}: {
  stepNum: number
  row: StepRow
  detail: RunDetail
  arts: StepArtifacts | undefined
  isActive: boolean
  review?: ReviewResult | null
  onArtifactSaved?: (step: number) => void
  onDirtyChange?: (dirty: boolean) => void
  onRunStep?: (step: number) => void
  onRewriteStep1FromReview?: () => void
  runningStep?: boolean
  rewritingStep1?: boolean
  pipelineBusy?: boolean
}) {
  const hasArts =
    arts && (Boolean(arts.text?.trim()) || arts.images.length > 0 || arts.videos.length > 0)
  const showEmpty =
    row.status === "pending" || row.status === "cancelled" || (!hasArts && row.status !== "running")

  const imageSrc = (path: string, updatedAt?: string) => {
    const base = fileUrl(detail.run_id, path)
    return updatedAt ? `${base}&v=${encodeURIComponent(updatedAt)}` : base
  }

  return (
    <section
      id={`pipeline-step-artifacts-${stepNum}`}
      className={cn(
        "scroll-mt-28 rounded-2xl border border-line-soft bg-card/40 p-4 sm:p-5",
        isActive && "border-accent-cool/35 bg-card/65 ring-1 ring-accent-cool/20",
      )}
    >
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-semibold text-foreground">
          步骤 {stepNum}
          <span className="font-normal text-muted-foreground"> · {stepTitleZh(stepNum)}</span>
        </h3>
        <Badge variant={statusVariant(row.status)}>{row.status}</Badge>
        {row.status === "running" && (
          <span className="inline-flex items-center gap-1 text-xs text-amber-600">
            <Loader2 className="size-3 animate-spin" aria-hidden />
            运行中
          </span>
        )}
        {onRunStep && row.status !== "running" && (
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="ml-auto h-7 gap-1 text-xs"
            disabled={runningStep || pipelineBusy}
            onClick={() => onRunStep(stepNum)}
          >
            <Play className="size-3" aria-hidden />
            运行此步骤
          </Button>
        )}
      </div>

      {row.error && (
        <pre className="mb-4 max-h-32 overflow-auto rounded-lg bg-destructive/10 p-3 text-xs whitespace-pre-wrap text-destructive">
          {row.error}
        </pre>
      )}

      {review && row.status === "success" && (
        <div className="mb-4">
          <ReviewBadge review={review} step={stepNum} />
          {typeof review.score === "number" && (
            <ScoreBar score={review.score} className="mt-2" />
          )}
        </div>
      )}

      {row.status === "running" && !hasArts && (
        <p className="text-sm text-muted-foreground">步骤执行中，产物生成后将显示在此处。</p>
      )}

      {showEmpty && row.status !== "running" && (
        <p className="text-sm text-muted-foreground">暂无产物（步骤未完成或未生成文件）。</p>
      )}

      {hasArts && (
        <div className="space-y-4">
          {arts?.text?.trim() ? (
            <EditableArtifactPanel
              runId={detail.run_id}
              step={stepNum}
              label={arts.text_kind === "json" ? "文档" : `文本（${arts.text_kind ?? "plain"}）`}
              text={arts.text}
              textKind={arts.text_kind}
              onSaved={isEditableStep(stepNum) ? onArtifactSaved : undefined}
              onDirtyChange={isActive && isEditableStep(stepNum) ? onDirtyChange : undefined}
              onRewriteFromReview={stepNum === 1 ? onRewriteStep1FromReview : undefined}
              rewritingFromReview={rewritingStep1}
              rewriteDisabled={pipelineBusy}
            />
          ) : null}

          {arts && arts.images.length > 0 ? (
            <div>
              <p className="mb-2 text-xs font-medium text-muted-foreground">图片</p>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {arts.images.map((im) => (
                  <ArtifactMediaCard
                    key={im.path}
                    kind="image"
                    src={imageSrc(im.path, im.updated_at)}
                    label={im.label}
                    prompt={im.prompt}
                    regenerateDisabled={pipelineBusy}
                    onRegenerate={
                      stepNum === 3
                        ? async (prompt) => {
                            await postRegenerateStep3Image(detail.run_id, { path: im.path, prompt })
                            onArtifactSaved?.(stepNum)
                          }
                        : undefined
                    }
                  />
                ))}
              </div>
            </div>
          ) : null}

          {arts && arts.videos.length > 0 ? (
            <div>
              <p className="mb-2 text-xs font-medium text-muted-foreground">视频</p>
              <div className="grid gap-3 lg:grid-cols-2">
                {arts.videos.map((v) => (
                  <ArtifactMediaCard
                    key={v.path}
                    kind="video"
                    src={fileUrl(detail.run_id, v.path)}
                    label={v.label}
                  />
                ))}
              </div>
            </div>
          ) : null}
        </div>
      )}
    </section>
  )
}

/** 当前步骤产物：仅展示 activeStep 对应内容 */
export function StepArtifactsPanel({
  detail,
  artByStep,
  activeStep,
  runReviews,
  onArtifactSaved,
  onDirtyChange,
  onRunStep,
  onRewriteStep1FromReview,
  onRunAll,
  runningStep,
  rewritingStep1,
  runningAll,
  pipelineBusy,
}: StepArtifactsPanelProps) {
  const sid = String(activeStep)
  const row = detail.steps[sid] ?? {
    title: stepTitleZh(activeStep),
    status: "pending" as StepStatus,
    error: null,
    updated_at: null,
  }

  const review = runReviews?.reviews?.[sid] ?? null
  const busy = pipelineBusy || runningStep || runningAll

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-foreground">产物预览</h2>
        {onRunAll ? (
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="h-8 gap-1.5 text-xs"
            disabled={busy}
            onClick={onRunAll}
          >
            {runningAll ? (
              <Loader2 className="size-3.5 animate-spin" aria-hidden />
            ) : (
              <PlayCircle className="size-3.5" aria-hidden />
            )}
            运行全部步骤
          </Button>
        ) : null}
      </div>
      <StepBlock
        key={sid}
        stepNum={activeStep}
        row={row}
        detail={detail}
        arts={artByStep[sid]}
        isActive
        review={review}
        onArtifactSaved={onArtifactSaved}
        onDirtyChange={onDirtyChange}
        onRunStep={onRunStep}
        onRewriteStep1FromReview={onRewriteStep1FromReview}
        runningStep={runningStep}
        rewritingStep1={rewritingStep1}
        pipelineBusy={pipelineBusy}
      />
    </div>
  )
}
