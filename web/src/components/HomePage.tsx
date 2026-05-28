import { FlovaRecentProjects } from "@/components/FlovaRecentProjects"
import { HomeComposer } from "@/components/HomeComposer"
import { HomeHeroTypewriter } from "@/components/HomeHeroTypewriter"
import { HotSkillsRow } from "@/components/HotSkillsRow"

interface HomePageProps {
  topic: string
  onTopicChange: (v: string) => void
  style: string
  onStyleChange: (v: string) => void
  duration: number
  onDurationChange: (v: number) => void
  createBusy?: boolean
  onCreateRun: () => void
  runs: import("@/lib/api").RunSummary[]
  loadingList: boolean
  onPickRun: (runId: string) => void
  onDeleteRun: (runId: string) => void
  deletingRunId?: string | null
}

export function HomePage({
  topic,
  onTopicChange,
  style,
  onStyleChange,
  duration,
  onDurationChange,
  createBusy,
  onCreateRun,
  runs,
  loadingList,
  onPickRun,
  onDeleteRun,
  deletingRunId = null,
}: HomePageProps) {
  return (
    <div className="mt-[200px] space-y-8 pb-20 sm:space-y-12">
      <header className="mx-auto max-w-4xl pt-2 text-center">
        <HomeHeroTypewriter />
      </header>

      <HomeComposer
        topic={topic}
        onTopicChange={onTopicChange}
        style={style}
        onStyleChange={onStyleChange}
        duration={duration}
        onDurationChange={onDurationChange}
        busy={createBusy}
        onStart={onCreateRun}
      />

      <HotSkillsRow
        onPickPreset={(preset) => {
          onStyleChange(preset)
          window.requestAnimationFrame(() =>
            document.getElementById("home-composer")?.scrollIntoView({ behavior: "smooth", block: "start" }),
          )
        }}
      />

      <section id="home-projects" className="scroll-mt-24">
        <FlovaRecentProjects
          variant="preview"
          runs={runs}
          loadingList={loadingList}
          onPickRun={onPickRun}
          onNewProject={() => {
            document.getElementById("home-composer")?.scrollIntoView({ behavior: "smooth", block: "start" })
          }}
          onDeleteRun={onDeleteRun}
          deletingRunId={deletingRunId}
        />
      </section>
    </div>
  )
}
