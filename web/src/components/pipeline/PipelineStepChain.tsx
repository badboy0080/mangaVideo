import { Fragment } from "react"

import { stepTitleZh } from "@/lib/step-labels"
import { cn } from "@/lib/utils"
import type { RunDetail, StepStatus } from "@/lib/api"

const STEP_COUNT = 5

/** 与首页发送按钮、accent-cool 一致的主题渐变 */
const THEME_GRADIENT =
  "bg-gradient-to-br from-violet-500 via-fuchsia-500 to-teal-500 text-white shadow-[0_0_18px_rgba(168,85,247,0.22)]"

interface PipelineStepChainProps {
  detail: RunDetail
  activeStep: number
  onStepChange: (step: number) => void
}

function circleClass(status: StepStatus, isActive: boolean): string {
  const base =
    "relative z-[1] flex size-10 shrink-0 items-center justify-center rounded-full text-xs font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background motion-safe:hover:scale-105"

  switch (status) {
    case "success":
      return cn(base, THEME_GRADIENT, isActive && "ring-2 ring-fuchsia-300/70 ring-offset-1 ring-offset-background")
    case "running":
      return cn(
        base,
        THEME_GRADIENT,
        "motion-safe:animate-pulse",
        isActive && "ring-2 ring-amber-200/80 ring-offset-1 ring-offset-background",
      )
    case "failed":
      return cn(
        base,
        "bg-gradient-to-br from-destructive to-red-600 text-destructive-foreground",
        isActive && "ring-2 ring-destructive/45 ring-offset-1 ring-offset-background",
      )
    case "cancelled":
      return cn(
        base,
        "bg-muted-foreground/50 text-background",
        isActive && "ring-2 ring-muted-foreground/35 ring-offset-1 ring-offset-background",
      )
    default:
      return cn(
        base,
        "border-2 border-dashed border-muted-foreground/40 bg-muted/25 text-muted-foreground",
        isActive && "border-accent-cool/60 bg-accent-cool/10 text-foreground ring-2 ring-accent-cool/25 ring-offset-1 ring-offset-background",
      )
  }
}

function connectorClass(leftStatus: StepStatus): string {
  const done = leftStatus === "success" || leftStatus === "running"
  return cn(
    "mx-1 flex h-4 min-w-0 flex-1 items-center [&>span]:block [&>span]:h-0 [&>span]:w-full [&>span]:border-t-2 [&>span]:border-dashed",
    done ? "[&>span]:border-fuchsia-400/55" : "[&>span]:border-muted-foreground/28",
  )
}

/** 页顶进度链：主题渐变圆点 + 等距虚线连接 */
export function PipelineStepChain({ detail, activeStep, onStepChange }: PipelineStepChainProps) {
  const steps = Array.from({ length: STEP_COUNT }, (_, i) => i + 1)

  return (
    <section className="px-1 py-4">
      <p className="mb-4 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">进度</p>
      <div className="flex w-full min-w-0 items-center">
        {steps.map((n, idx) => {
          const sid = String(n)
          const row = detail.steps[sid]
          const status: StepStatus = row?.status ?? "pending"
          const isActive = activeStep === n
          const prevStatus: StepStatus =
            idx > 0 ? (detail.steps[String(steps[idx - 1])]?.status ?? "pending") : "pending"

          return (
            <Fragment key={sid}>
              {idx > 0 ? (
                <div className={connectorClass(prevStatus)} aria-hidden>
                  <span />
                </div>
              ) : null}
              <button
                type="button"
                title={`步骤 ${n} · ${stepTitleZh(n)}`}
                aria-label={`步骤 ${n} ${stepTitleZh(n)}，${status}${isActive ? "（当前）" : ""}`}
                aria-current={isActive ? "step" : undefined}
                className={circleClass(status, isActive)}
                onClick={() => onStepChange(n)}
              >
                {n}
              </button>
            </Fragment>
          )
        })}
      </div>
    </section>
  )
}
