import { Loader2, RefreshCw } from "lucide-react"

import { TextContentViewer } from "@/components/TextContentViewer"
import { Button } from "@/components/ui/button"
import type { RunDetail, StepStatus } from "@/lib/api"

const STEP_COUNT = 5

export interface PipelineRunLogsProps {
  detail: RunDetail
  logByStep: Record<string, string>
  onFetchLog: (step: number) => void
}

/** 页面底部：默认折叠的运行日志 */
export function PipelineRunLogs({ detail, logByStep, onFetchLog }: PipelineRunLogsProps) {
  const anyRunning = Object.values(detail.steps).some((s) => s?.status === "running")

  return (
    <details className="rounded-2xl border border-line-soft bg-muted/25 text-sm">
      <summary className="cursor-pointer select-none px-4 py-3 font-medium text-foreground">
        运行日志
        {anyRunning && (
          <span className="ml-2 inline-flex items-center gap-1 text-xs font-normal text-amber-600">
            <Loader2 className="size-3 animate-spin" aria-hidden />
            有步骤进行中…
          </span>
        )}
      </summary>
      <div className="space-y-3 border-t border-line-soft px-4 py-4">
        {Array.from({ length: STEP_COUNT }, (_, i) => i + 1).map((n) => {
          const sid = String(n)
          const row = detail.steps[sid]
          const status: StepStatus = row?.status ?? "pending"
          const logText = logByStep[sid]
          const title = row?.title ?? `Step ${n}`

          return (
            <details
              key={sid}
              className="rounded-lg border border-line-soft bg-background/40"
              onToggle={(e) => {
                if (e.currentTarget.open) onFetchLog(n)
              }}
            >
              <summary className="cursor-pointer select-none px-3 py-2.5 text-xs font-medium text-foreground/90">
                步骤 {n} · {title}
                <span className="ml-2 font-normal text-muted-foreground">({status})</span>
              </summary>
              <div className="space-y-2 border-t border-line-soft px-3 py-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={(e) => {
                    e.preventDefault()
                    onFetchLog(n)
                  }}
                >
                  <RefreshCw className="size-3" aria-hidden />
                  刷新本步日志
                </Button>
                {logText != null && logText.length > 0 ? (
                  <TextContentViewer text={logText} allowJsonFormat={false} maxHeightClass="max-h-64" />
                ) : (
                  <p className="text-xs text-muted-foreground">（展开后自动加载，或点击刷新）</p>
                )}
              </div>
            </details>
          )
        })}
      </div>
    </details>
  )
}
