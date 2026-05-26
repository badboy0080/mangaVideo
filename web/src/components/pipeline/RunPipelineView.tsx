import { useEffect } from "react"

import { PipelineRunLogs } from "@/components/pipeline/PipelineRunLogs"
import { PipelineStepChain } from "@/components/pipeline/PipelineStepChain"
import { StepArtifactsPanel } from "@/components/pipeline/StepArtifactsPanel"
import type { RunDetail, StepArtifacts } from "@/lib/api"

export interface RunPipelineViewProps {
  detail: RunDetail
  activeStep: number
  onStepChange: (step: number) => void
  artByStep: Record<string, StepArtifacts>
  logByStep: Record<string, string>
  onFetchArt: (step: number) => void
  onFetchLog: (step: number) => void
  onArtifactSaved?: (step: number) => void
  onArtDirtyChange?: (dirty: boolean) => void
  onRunStep?: (step: number) => void
  onRunAll?: () => void
  runningStepReq?: boolean
  runningAllReq?: boolean
  pipelineBusy?: boolean
}

/** 流水线操作页：顶栏进度链 → 当前步骤产物 → 底部折叠日志 */
export function RunPipelineView({
  detail,
  activeStep,
  onStepChange,
  artByStep,
  logByStep,
  onFetchArt,
  onFetchLog,
  onArtifactSaved,
  onArtDirtyChange,
  onRunStep,
  runningStepReq,
  onRunAll,
  runningAllReq,
  pipelineBusy,
}: RunPipelineViewProps) {
  const activeSid = String(activeStep)
  const activeRow = detail.steps[activeSid]
  const activeStatus = activeRow?.status ?? "pending"
  const activeUpdated = activeRow?.updated_at

  // 仅加载当前步骤产物；运行中步骤随 updated_at 刷新，避免 8 路并发请求
  useEffect(() => {
    onFetchArt(activeStep)
  }, [
    activeStep,
    detail.run_id,
    activeStatus,
    activeStatus === "running" ? activeUpdated : null,
    onFetchArt,
  ])

  return (
    <div className="space-y-6">
      <PipelineStepChain detail={detail} activeStep={activeStep} onStepChange={onStepChange} />
      <StepArtifactsPanel
        detail={detail}
        artByStep={artByStep}
        activeStep={activeStep}
        onArtifactSaved={onArtifactSaved}
        onDirtyChange={onArtDirtyChange}
        onRunStep={onRunStep}
        runningStep={runningStepReq}
        onRunAll={onRunAll}
        runningAll={runningAllReq}
        pipelineBusy={pipelineBusy}
      />
      <PipelineRunLogs detail={detail} logByStep={logByStep} onFetchLog={onFetchLog} />
    </div>
  )
}
