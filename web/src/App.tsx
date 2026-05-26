import { RefreshCw, Copy, Check, ChevronLeft } from "lucide-react"
import { useCallback, useEffect, useRef, useState } from "react"
import { AuroraBackground } from "@/components/AuroraBackground"
import { FlovaHomeSidebar, type HomeShellView } from "@/components/FlovaHomeSidebar"
import { FlovaHomeTopBar } from "@/components/FlovaHomeTopBar"
import { HomePage } from "@/components/HomePage"
import { MyProjectsPage } from "@/components/MyProjectsPage"
import { RunPipelineView } from "@/components/pipeline/RunPipelineView"
import { ProjectRunTitle } from "@/components/pipeline/ProjectRunTitle"
import { RunDetailSkeleton } from "@/components/RunDetailSkeleton"
import { Button } from "@/components/ui/button"
import type { RunDetail, RunSummary, StepArtifacts } from "@/lib/api"
import { API_BASE, apiJson, apiText, deleteRun, patchRunTopic, postRunPipelineAll, postRunStep } from "@/lib/api"
import { isStylePreset } from "@/lib/run-presets"
const HEALTH_DISMISS_KEY = "mp_ui_health_banner_dismiss_session"

function homeScrollContainer(): HTMLElement | null {
  return document.getElementById("home-main-scroll")
}
function scrollElementIntoHomeView(el: HTMLElement | null) {
  if (!el) return
  const scroller = homeScrollContainer()
  if (scroller) {
    const scrollerRect = scroller.getBoundingClientRect()
    const elRect = el.getBoundingClientRect()
    const top = scroller.scrollTop + (elRect.top - scrollerRect.top) - 12
    scroller.scrollTo({ top: Math.max(0, top), behavior: "smooth" })
    return
  }
  el.scrollIntoView({ behavior: "smooth", block: "start" })
}
function scrollToComposer() {
  window.requestAnimationFrame(() => scrollElementIntoHomeView(document.getElementById("home-composer")))
}
function scrollToSection(id: string) {
  window.requestAnimationFrame(() => scrollElementIntoHomeView(document.getElementById(id)))
}
function anyRunning(detail: RunDetail | null): boolean {
  if (!detail) return false
  return Object.values(detail.steps).some((s) => s?.status === "running")
}
export default function App() {
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [detail, setDetail] = useState<RunDetail | null>(null)
  const detailRef = useRef<RunDetail | null>(null)
  detailRef.current = detail
  const [loadingList, setLoadingList] = useState(false)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [creatingRun, setCreatingRun] = useState(false)
  const [deletingRunId, setDeletingRunId] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [errCopied, setErrCopied] = useState(false)
  const [apiWarn, setApiWarn] = useState<string | null>(null)
  const [healthDismissed, setHealthDismissed] = useState(
    () => typeof sessionStorage !== "undefined" && sessionStorage.getItem(HEALTH_DISMISS_KEY) === "1",
  )
  const [homeView, setHomeView] = useState<HomeShellView>("home")
  const [topic, setTopic] = useState("")
  const [duration, setDuration] = useState(90)
  const [style, setStyle] = useState("电影短片")
  const [imgConc, setImgConc] = useState(5)
  const [vidConc, setVidConc] = useState(3)
  const [focusedStep, setFocusedStep] = useState(1)
  const stepFocusInitForRun = useRef<string | null>(null)
  const artFetchInflight = useRef<Set<string>>(new Set())
  const artLoadedKeys = useRef<Set<string>>(new Set())
  const artDirtyRef = useRef(false)
  const [runningStepReq, setRunningStepReq] = useState(false)
  const [runningAllReq, setRunningAllReq] = useState(false)
  const [savingTopic, setSavingTopic] = useState(false)
  const [logByStep, setLogByStep] = useState<Record<string, string>>({})
  const [artByStep, setArtByStep] = useState<Record<string, StepArtifacts>>({})
  const fetchStepLog = useCallback(async (step: number) => {
    if (!selected) return
    const path = `/api/runs/${encodeURIComponent(selected)}/steps/${step}/log`
    try {
      const text = await apiText(path)
      setLogByStep((m) => ({ ...m, [String(step)]: text }))
    } catch (e) {
      setLogByStep((m) => ({
        ...m,
        [String(step)]: e instanceof Error ? e.message : "（加载日志失败）",
      }))
    }
  }, [selected])
  const fetchStepArt = useCallback(async (step: number) => {
    if (!selected) return
    const sid = String(step)
    const cacheKey = `${selected}:${sid}`
    if (artFetchInflight.current.has(cacheKey)) return

    const status = detailRef.current?.steps[sid]?.status ?? "pending"
    if (artLoadedKeys.current.has(cacheKey) && status !== "running") return

    artFetchInflight.current.add(cacheKey)
    const statusAtStart = status
    try {
      const a = await apiJson<StepArtifacts>(
        `/api/runs/${encodeURIComponent(selected)}/steps/${step}/artifacts`,
      )
      if (statusAtStart !== "running") {
        artLoadedKeys.current.add(cacheKey)
      }
      setArtByStep((m) => ({ ...m, [sid]: a }))
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      setArtByStep((m) => ({
        ...m,
        [sid]: {
          step,
          text: `加载产物失败：\n${msg}`,
          text_kind: "markdown",
          images: [],
          videos: [],
        },
      }))
    } finally {
      artFetchInflight.current.delete(cacheKey)
    }
  }, [selected])
  const refreshStepArt = useCallback(
    async (step: number) => {
      if (!selected) return
      artLoadedKeys.current.delete(`${selected}:${String(step)}`)
      await fetchStepArt(step)
    },
    [selected, fetchStepArt],
  )
  const handleArtifactSaved = useCallback(
    (step: number) => {
      artDirtyRef.current = false
      void refreshStepArt(step)
    },
    [refreshStepArt],
  )
  const handleArtDirtyChange = useCallback((dirty: boolean) => {
    artDirtyRef.current = dirty
  }, [])
  const handleStepChange = useCallback((step: number) => {
    if (artDirtyRef.current) {
      if (!window.confirm("有未保存的文档修改，确定切换步骤吗？")) return
      artDirtyRef.current = false
    }
    setFocusedStep(step)
  }, [])
  const refreshRuns = useCallback(async () => {
    setLoadingList(true)
    setErr(null)
    try {
      const data = await apiJson<RunSummary[]>("/api/runs")
      setRuns(data)
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    } finally {
      setLoadingList(false)
    }
  }, [])
  const refreshDetail = useCallback(async (runId: string, opts?: { silent?: boolean }) => {
    const silent = opts?.silent === true
    if (!silent) setLoadingDetail(true)
    if (!silent) setErr(null)
    try {
      const d = await apiJson<RunDetail>(`/api/runs/${encodeURIComponent(runId)}`)
      setDetail(d)
    } catch (e) {
      if (!silent) {
        setErr(e instanceof Error ? e.message : String(e))
        setDetail(null)
      }
    } finally {
      if (!silent) setLoadingDetail(false)
    }
  }, [])
  const handleRunStep = useCallback(
    async (step: number) => {
      if (!selected) return
      setRunningStepReq(true)
      setErr(null)
      try {
        const force = detailRef.current?.steps[String(step)]?.status === "success"
        await postRunStep(selected, step, force)
        await refreshDetail(selected, { silent: true })
        artLoadedKeys.current.delete(`${selected}:${String(step)}`)
        void fetchStepArt(step)
        void fetchStepLog(step)
      } catch (e) {
        setErr(e instanceof Error ? e.message : String(e))
      } finally {
        setRunningStepReq(false)
      }
    },
    [selected, fetchStepArt, fetchStepLog, refreshDetail],
  )
  const handleRunAll = useCallback(async () => {
    if (!selected) return
    setRunningAllReq(true)
    setErr(null)
    try {
      await postRunPipelineAll(selected, false)
      await refreshDetail(selected, { silent: true })
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    } finally {
      setRunningAllReq(false)
    }
  }, [selected, refreshDetail])
  const handleRenameTopic = useCallback(
    async (nextTopic: string) => {
      if (!selected) return
      setSavingTopic(true)
      setErr(null)
      try {
        await patchRunTopic(selected, nextTopic)
        setDetail((d) => (d ? { ...d, topic: nextTopic } : d))
        void refreshRuns()
      } catch (e) {
        setErr(e instanceof Error ? e.message : String(e))
      } finally {
        setSavingTopic(false)
      }
    },
    [selected, refreshRuns],
  )
  useEffect(() => {
    void refreshRuns()
  }, [refreshRuns])
  useEffect(() => {
    let cancelled = false
    void (async () => {
      try {
        const h = await apiJson<{
          ok: boolean
          api_revision?: number
          routes?: string[]
        }>("/api/health")
        if (cancelled || healthDismissed) return
        if (!Array.isArray(h.routes) || !h.routes.includes("step_log")) {
          setApiWarn(
            "后端 /api/health 未列出 step_log（多半是旧进程）。请在**本仓库根目录**重启：python -m uvicorn server.main:app --host 127.0.0.1 --port 8765",
          )
        } else {
          setApiWarn(null)
        }
      } catch {
        if (!cancelled && !healthDismissed) {
          setApiWarn(`无法连接 API（${API_BASE}）。请先启动后端。`)
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [healthDismissed])
  useEffect(() => {
    if (!selected) {
      setDetail(null)
      setLoadingDetail(false)
      return
    }
    void refreshDetail(selected)
  }, [selected, refreshDetail])
  useEffect(() => {
    setLogByStep({})
    setArtByStep({})
    artLoadedKeys.current.clear()
    artFetchInflight.current.clear()
  }, [selected])
  useEffect(() => {
    stepFocusInitForRun.current = null
  }, [selected])
  useEffect(() => {
    if (!detail || detail.run_id !== selected || !selected) return
    if (stepFocusInitForRun.current === selected) return
    stepFocusInitForRun.current = selected
    const order = [1, 2, 3, 4, 5] as const
    const running = order.find((x) => detail.steps[String(x)]?.status === "running")
    const initial =
      running ?? order.find((x) => detail.steps[String(x)]?.status !== "success") ?? 1
    setFocusedStep(initial)
  }, [detail, selected])
  useEffect(() => {
    if (!detail || !selected || !anyRunning(detail)) return
    const t = window.setInterval(() => {
      void refreshDetail(selected, { silent: true })
    }, 2500)
    return () => window.clearInterval(t)
  }, [detail, selected, refreshDetail])
  useEffect(() => {
    if (!detail || !selected || !anyRunning(detail)) return
    const pollLogs = () => {
      const d = detailRef.current
      if (!d) return
      Object.entries(d.steps).forEach(([k, r]) => {
        if (r?.status === "running") void fetchStepLog(Number(k))
      })
    }
    pollLogs()
    const t = window.setInterval(pollLogs, 2500)
    return () => window.clearInterval(t)
  }, [detail, selected, fetchStepLog])
  async function onCreateRun() {
    setErr(null)
    if (!isStylePreset(style.trim())) {
      setErr("请选择有效的风格类型（7 种预设之一）")
      return
    }
    setCreatingRun(true)
    try {
      const body = await apiJson<RunDetail>("/api/runs", {
        method: "POST",
        body: JSON.stringify({
          topic: topic.trim(),
          duration,
          style: style.trim(),
          img_concurrency: imgConc,
          video_concurrency: vidConc,
        }),
      })
      await refreshRuns()
      setSelected(body.run_id)
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    } finally {
      setCreatingRun(false)
    }
  }
  async function onDeleteRun(runId: string) {
    const topic = runs.find((r) => r.run_id === runId)?.topic || runId
    if (!window.confirm(`确定将「${topic}」移入回收站？\n列表与历史中将不再显示（文件在 outputs/_trash）。`)) {
      return
    }
    setDeletingRunId(runId)
    setErr(null)
    try {
      await deleteRun(runId)
      if (selected === runId) {
        setSelected(null)
        setDetail(null)
      }
      await refreshRuns()
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    } finally {
      setDeletingRunId(null)
    }
  }
  async function copyErr() {
    if (!err) return
    try {
      await navigator.clipboard.writeText(err)
      setErrCopied(true)
      window.setTimeout(() => setErrCopied(false), 2000)
    } catch {
      /* ignore */
    }
  }
  function dismissHealthBanner() {
    sessionStorage.setItem(HEALTH_DISMISS_KEY, "1")
    setHealthDismissed(true)
    setApiWarn(null)
  }
  const displayStep = Math.min(5, Math.max(1, focusedStep))
  const isHome = !selected
  const pipelineBusy = anyRunning(detail) || runningStepReq || runningAllReq

  function goHome() {
    setSelected(null)
    void refreshRuns()
  }

  return (
    <div
      className={
        isHome ? "min-h-screen text-foreground" : "min-h-screen bg-app-gradient text-foreground"
      }
    >
      {isHome ? (
        <div className="relative flex h-dvh overflow-hidden">
          <AuroraBackground />
          <div className="relative z-10 flex min-h-0 min-w-0 flex-1 overflow-hidden">
          <FlovaHomeSidebar
            homeView={homeView}
            imgConc={imgConc}
            onImgConcChange={setImgConc}
            vidConc={vidConc}
            onVidConcChange={setVidConc}
            onHome={() => {
              setSelected(null)
              setHomeView("home")
              homeScrollContainer()?.scrollTo({ top: 0, behavior: "smooth" })
            }}
            onMyProjects={() => {
              setSelected(null)
              setHomeView("projects")
              homeScrollContainer()?.scrollTo({ top: 0, behavior: "smooth" })
            }}
            onScrollHotSkills={() => {
              setSelected(null)
              setHomeView("home")
              scrollToSection("home-hot-skills")
            }}
            onScrollProjects={() => {
              setSelected(null)
              if (homeView === "projects") {
                setHomeView("home")
                window.requestAnimationFrame(() => scrollToSection("home-projects"))
                return
              }
              scrollToSection("home-projects")
            }}
          />
          <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
            <FlovaHomeTopBar
              apiWarn={apiWarn}
              healthDismissed={healthDismissed}
              onDismissHealth={dismissHealthBanner}
            />
            <main
              id="home-main-scroll"
              className="min-h-0 flex-1 overflow-y-auto overscroll-y-contain mp-scrollbar"
            >
              <div className="mx-auto max-w-6xl px-4 py-6 sm:px-8">
                {err && (
                  <div className="mb-6 flex gap-3 rounded-xl bg-destructive/12 px-4 py-3 text-sm text-destructive">
                    <pre className="min-w-0 flex-1 whitespace-pre-wrap break-words">{err}</pre>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      className="shrink-0"
                      onClick={() => void copyErr()}
                    >
                      {errCopied ? <Check className="size-4" /> : <Copy className="size-4" />}
                      {errCopied ? "已复制" : "复制"}
                    </Button>
                  </div>
                )}
                {homeView === "home" ? (
                  <HomePage
                    runs={runs}
                    loadingList={loadingList}
                    topic={topic}
                    onTopicChange={setTopic}
                    style={style}
                    onStyleChange={setStyle}
                    duration={duration}
                    onDurationChange={setDuration}
                    createBusy={creatingRun}
                    onCreateRun={() => void onCreateRun()}
                    onPickRun={(runId) => setSelected(runId)}
                    onDeleteRun={(runId) => void onDeleteRun(runId)}
                    deletingRunId={deletingRunId}
                  />
                ) : (
                  <MyProjectsPage
                    runs={runs}
                    loadingList={loadingList}
                    onPickRun={(runId) => setSelected(runId)}
                    onNewProject={() => {
                      setHomeView("home")
                      scrollToComposer()
                    }}
                    onDeleteRun={(runId) => void onDeleteRun(runId)}
                    deletingRunId={deletingRunId}
                  />
                )}
              </div>
            </main>
          </div>
          </div>
        </div>
      ) : (
        <>
          <header className="sticky top-0 z-40 border-b border-line-soft bg-card/85 backdrop-blur-md supports-[backdrop-filter]:bg-card/75">
            <div className="mx-auto max-w-7xl space-y-3 px-4 py-4 sm:px-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex min-w-0 flex-1 items-center gap-2 sm:gap-3">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="shrink-0 gap-1 px-2 text-muted-foreground hover:text-foreground"
                    onClick={goHome}
                  >
                    <ChevronLeft className="size-4" aria-hidden />
                    返回
                  </Button>
                  <ProjectRunTitle
                    topic={detail?.topic ?? runs.find((r) => r.run_id === selected)?.topic}
                    saving={savingTopic}
                    onSave={handleRenameTopic}
                  />
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="shrink-0 transition-colors"
                  onClick={() => void refreshRuns()}
                  aria-busy={loadingList}
                >
                  <RefreshCw className={`size-4 ${loadingList ? "animate-spin" : ""}`} aria-hidden />
                  刷新
                </Button>
              </div>
              {apiWarn && !healthDismissed && (
                <div className="flex flex-wrap items-start gap-2 rounded-xl bg-amber-500/[0.09] px-3 py-2.5 text-sm text-amber-950 dark:text-amber-50">
                  <p className="min-w-0 flex-1 leading-snug">{apiWarn}</p>
                  <button
                    type="button"
                    className="shrink-0 rounded-lg bg-background/90 px-2.5 py-1.5 text-xs font-medium transition-colors hover:bg-muted/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    onClick={dismissHealthBanner}
                  >
                    本次会话关闭提示
                  </button>
                </div>
              )}
            </div>
          </header>
          <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
            <section className="space-y-5 pb-16">
              {err && (
                <div className="flex gap-3 rounded-xl bg-destructive/12 px-4 py-3 text-sm text-destructive">
                  <pre className="min-w-0 flex-1 whitespace-pre-wrap break-words">{err}</pre>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    className="shrink-0"
                    onClick={() => void copyErr()}
                  >
                    {errCopied ? <Check className="size-4" /> : <Copy className="size-4" />}
                    {errCopied ? "已复制" : "复制"}
                  </Button>
                </div>
              )}
              {selected && loadingDetail && !detail && <RunDetailSkeleton />}
              {detail && (
                <RunPipelineView
                  detail={detail}
                  activeStep={displayStep}
                  onStepChange={handleStepChange}
                  artByStep={artByStep}
                  logByStep={logByStep}
                  onFetchArt={(step) => void fetchStepArt(step)}
                  onFetchLog={(step) => void fetchStepLog(step)}
                  onArtifactSaved={handleArtifactSaved}
                  onArtDirtyChange={handleArtDirtyChange}
                  onRunStep={(step) => void handleRunStep(step)}
                  onRunAll={() => void handleRunAll()}
                  runningStepReq={runningStepReq}
                  runningAllReq={runningAllReq}
                  pipelineBusy={pipelineBusy}
                />
              )}
            </section>
          </main>
        </>
      )}
    </div>
  )
}
