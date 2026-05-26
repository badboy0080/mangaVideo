import { Loader2, Plus, Trash2 } from "lucide-react"

import { Skeleton } from "@/components/ui/skeleton"
import type { RunSummary } from "@/lib/api"
import { fileUrl } from "@/lib/api"
import { cn } from "@/lib/utils"

const HOME_PREVIEW_COUNT = 4

function sortRunsNewest(runs: RunSummary[]): RunSummary[] {
  return [...runs].sort((a, b) => {
    const ta = Date.parse(a.updated_at ?? a.created_at ?? "") || 0
    const tb = Date.parse(b.updated_at ?? b.created_at ?? "") || 0
    return tb - ta
  })
}

function displayTopic(topic: string | undefined): string {
  const t = (topic || "").trim()
  if (!t || t.includes("legacy")) return "未命名项目"
  return t
}

function formatLastEdited(iso: string | null | undefined): string {
  if (!iso) return "—"
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return "—"
  const y = d.getFullYear()
  const m = d.getMonth() + 1
  const day = d.getDate()
  const h = String(d.getHours()).padStart(2, "0")
  const min = String(d.getMinutes()).padStart(2, "0")
  return `${y}年${m}月${day}日 ${h}:${min}`
}

function NewProjectCard({ onClick, className }: { onClick: () => void; className?: string }) {
  return (
    <li className={cn("min-w-0", className)}>
      <button
        type="button"
        onClick={onClick}
        className="project-run-card group flex h-full w-full flex-col overflow-hidden text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        <div className="flex aspect-[4/3] w-full items-center justify-center rounded-xl bg-zinc-900/80">
          <span className="flex size-12 items-center justify-center rounded-full bg-white/[0.06] text-zinc-400 transition-colors group-hover:text-zinc-200">
            <Plus className="size-6 stroke-[1.5]" aria-hidden />
          </span>
        </div>
        <div className="project-run-card-footer">
          <p className="project-card-title text-[0.9375rem] font-semibold text-[#f0f0f5]">创建新项目</p>
          <p className="mt-1 text-xs text-zinc-500">开始一个新的漫剧项目</p>
        </div>
      </button>
    </li>
  )
}

export interface FlovaRecentProjectsProps {
  runs: RunSummary[]
  loadingList: boolean
  onPickRun: (runId: string) => void
  onNewProject: () => void
  onDeleteRun: (runId: string) => void
  deletingRunId?: string | null
  /** 首页单行预览 vs 我的项目页完整网格 */
  variant?: "preview" | "full"
  showTitle?: boolean
}

export function FlovaRecentProjects(props: FlovaRecentProjectsProps) {
  const {
    runs,
    loadingList,
    onPickRun,
    onNewProject,
    onDeleteRun,
    deletingRunId = null,
    variant = "full",
    showTitle = true,
  } = props

  const sorted = sortRunsNewest(runs)
  const isPreview = variant === "preview"
  const visibleRuns = isPreview ? sorted.slice(0, HOME_PREVIEW_COUNT) : sorted

  return (
    <div className="space-y-6">
      {showTitle ? <h2 className="flova-section-title text-foreground">最近项目</h2> : null}

      {loadingList && runs.length === 0 ? (
        isPreview ? (
          <ul className="-mx-4 flex list-none gap-4 overflow-x-auto px-4 pb-1 mp-scrollbar sm:mx-0 sm:px-0">
            {Array.from({ length: 3 }).map((_, i) => (
              <li key={i} className="w-[min(100%,14rem)] shrink-0 sm:w-[15rem]">
                <Skeleton className="aspect-[4/3] w-full rounded-2xl" />
              </li>
            ))}
          </ul>
        ) : (
          <ul className="grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <li key={i}>
                <Skeleton className="aspect-[4/3] w-full rounded-2xl" />
              </li>
            ))}
          </ul>
        )
      ) : isPreview ? (
        <ul className="-mx-4 flex list-none gap-4 overflow-x-auto px-4 pb-1 pt-0.5 mp-scrollbar sm:mx-0 sm:px-0">
          {visibleRuns.map((r) => (
            <ProjectRunCard
              key={r.run_id}
              run={r}
              deleting={deletingRunId === r.run_id}
              className="w-[min(100%,14rem)] shrink-0 sm:w-[15rem]"
              onPick={() => onPickRun(r.run_id)}
              onDelete={() => onDeleteRun(r.run_id)}
            />
          ))}
        </ul>
      ) : (
        <ul className="grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          <NewProjectCard onClick={onNewProject} />
          {visibleRuns.map((r) => (
            <ProjectRunCard
              key={r.run_id}
              run={r}
              deleting={deletingRunId === r.run_id}
              onPick={() => onPickRun(r.run_id)}
              onDelete={() => onDeleteRun(r.run_id)}
            />
          ))}
        </ul>
      )}

      {loadingList && runs.length > 0 ? (
        <p className="flex items-center gap-2 text-xs text-[#8888aa]">
          <Loader2 className="size-3.5 shrink-0 animate-spin" aria-hidden />
          列表刷新中…
        </p>
      ) : null}
    </div>
  )
}

function ProjectRunCard({
  run,
  deleting,
  onPick,
  onDelete,
  className,
}: {
  run: RunSummary
  deleting: boolean
  onPick: () => void
  onDelete: () => void
  className?: string
}) {
  const title = displayTopic(run.topic)
  const lastEdited = formatLastEdited(run.updated_at ?? run.created_at)
  const hasVideo = Boolean(run.final_mp4?.trim())
  const vid = hasVideo ? String(run.final_mp4).replace(/^\/+/, "") : ""
  const videoSrc = hasVideo ? fileUrl(run.run_id, vid) : ""
  const cover = run.cover_image?.trim()
  const coverSrc = cover ? fileUrl(run.run_id, cover.replace(/^\/+/, "")) : ""
  const hasCover = Boolean(coverSrc)

  return (
    <li className={cn("group relative min-w-0", className)}>
      <button
        type="button"
        title="移入回收站"
        disabled={deleting}
        aria-busy={deleting}
        aria-label="移入回收站"
        className={cn(
          "absolute right-4 top-4 z-10 flex size-8 items-center justify-center rounded-full bg-black/55 text-white backdrop-blur-sm transition-opacity",
          "opacity-0 focus-visible:opacity-100 group-hover:opacity-100",
          "hover:bg-destructive/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          deleting && "opacity-100",
        )}
        onClick={(e) => {
          e.stopPropagation()
          onDelete()
        }}
      >
        {deleting ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <Trash2 className="size-4" aria-hidden />}
      </button>

      <button
        type="button"
        onClick={onPick}
        className="project-run-card group/card flex h-full w-full flex-col text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        <div className="relative aspect-[4/3] w-full shrink-0 overflow-hidden rounded-xl bg-zinc-900">
          {hasVideo ? (
            <video
              className="absolute inset-0 size-full object-cover transition-transform duration-300 ease-out group-hover/card:scale-[1.02]"
              src={videoSrc}
              muted
              playsInline
              preload="metadata"
            />
          ) : hasCover ? (
            <img
              src={coverSrc}
              alt=""
              className="absolute inset-0 size-full object-cover transition-transform duration-300 ease-out group-hover/card:scale-[1.02]"
              loading="lazy"
              decoding="async"
            />
          ) : (
            <div className="absolute inset-0 bg-gradient-to-br from-zinc-800/40 via-zinc-900/60 to-black/80" aria-hidden />
          )}
        </div>

        <div className="project-run-card-footer">
          <p className="project-card-title text-[0.9375rem] font-semibold text-[#f0f0f5]" title={title}>
            {title}
          </p>
          <p className="mt-1.5 text-xs leading-snug text-zinc-500">最后编辑于 {lastEdited}</p>
        </div>
      </button>
    </li>
  )
}
