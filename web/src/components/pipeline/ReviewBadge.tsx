import { CheckCircle, XCircle, SkipForward } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ReviewResult } from "@/lib/api"

export interface ReviewBadgeProps {
  review: ReviewResult | null | undefined
  step: number
  className?: string
}

export function ReviewBadge({ review, step, className }: ReviewBadgeProps) {
  if (!review) return null

  const skipped = review.skipped === true
  const passed = review.passed === true
  const score = typeof review.score === "number" ? review.score : null

  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-2 rounded-lg border px-3 py-2 text-xs",
        skipped
          ? "border-zinc-700/50 bg-zinc-800/30 text-zinc-400"
          : passed
            ? "border-emerald-700/40 bg-emerald-900/20 text-emerald-400"
            : "border-amber-700/40 bg-amber-900/20 text-amber-400",
        className,
      )}
    >
      {skipped ? (
        <SkipForward className="size-3.5 shrink-0" />
      ) : passed ? (
        <CheckCircle className="size-3.5 shrink-0" />
      ) : (
        <XCircle className="size-3.5 shrink-0" />
      )}

      <span className="font-medium">
        Step{step} 审核
        {skipped ? " 跳过" : passed ? " 通过" : " 未通过"}
      </span>

      {score != null && (
        <span className={cn(
          "ml-auto font-mono tabular-nums",
          score >= 80 ? "text-emerald-400" : score >= 60 ? "text-amber-400" : "text-red-400",
        )}>
          {score}分
        </span>
      )}

      {review.issues && review.issues.length > 0 && (
        <div className="mt-1 w-full text-[11px] leading-relaxed opacity-80">
          {review.issues.map((issue, i) => (
            <span key={i} className="block before:mr-1 before:content-['•']">
              {issue}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export function ScoreBar({ score, maxScore = 100, className }: { score: number; maxScore?: number; className?: string }) {
  const pct = Math.max(0, Math.min(100, (score / maxScore) * 100))
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-zinc-700">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500",
            pct >= 80 ? "bg-emerald-500" : pct >= 60 ? "bg-amber-500" : "bg-red-500",
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-[11px] font-mono text-muted-foreground tabular-nums">{score}/{maxScore}</span>
    </div>
  )
}
