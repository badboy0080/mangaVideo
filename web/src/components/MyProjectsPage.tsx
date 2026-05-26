import { FlovaRecentProjects } from "@/components/FlovaRecentProjects"
import type { RunSummary } from "@/lib/api"

export interface MyProjectsPageProps {
  runs: RunSummary[]
  loadingList: boolean
  onPickRun: (runId: string) => void
  onNewProject: () => void
  onDeleteRun: (runId: string) => void
  deletingRunId?: string | null
}

/** 侧栏「我的项目」：完整项目卡片网格 */
export function MyProjectsPage({
  runs,
  loadingList,
  onPickRun,
  onNewProject,
  onDeleteRun,
  deletingRunId = null,
}: MyProjectsPageProps) {
  return (
    <div className="space-y-8 pb-20">
      <header>
        <h1 className="flova-section-title text-foreground">我的项目</h1>
        <p className="mt-2 text-sm text-[#8888aa]">管理全部漫剧流水线项目，点击卡片进入详情。</p>
      </header>

      <FlovaRecentProjects
        variant="full"
        showTitle={false}
        runs={runs}
        loadingList={loadingList}
        onPickRun={onPickRun}
        onNewProject={onNewProject}
        onDeleteRun={onDeleteRun}
        deletingRunId={deletingRunId}
      />
    </div>
  )
}
