import { ArrowUp, Clapperboard, Timer } from "lucide-react"
import { useId } from "react"

import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { NativeSelect, nativeSelectPillClass } from "@/components/ui/native-select"
import { DURATION_OPTIONS_SEC, STYLE_PRESETS } from "@/lib/run-presets"

interface HomeComposerProps {
  topic: string
  onTopicChange: (v: string) => void
  style: string
  onStyleChange: (v: string) => void
  duration: number
  onDurationChange: (v: number) => void
  busy?: boolean
  onStart: () => void
}

export function HomeComposer({
  topic,
  onTopicChange,
  style,
  onStyleChange,
  duration,
  onDurationChange,
  busy,
  onStart,
}: HomeComposerProps) {
  const ideaId = useId()
  const canStart = Boolean(topic.trim() && style.trim())

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && canStart && !busy) {
      e.preventDefault()
      void onStart()
    }
  }

  return (
    <section id="home-composer" className="mx-auto w-full max-w-4xl scroll-mt-28">
      <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-[oklch(0.18_0.01_270)] shadow-none sm:rounded-[20px]">
        <Label htmlFor={ideaId} className="sr-only">
          创意描述
        </Label>
        <textarea
          id={ideaId}
          rows={5}
          value={topic}
          onChange={(e) => onTopicChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="由一个想法或故事开始…"
          className="block min-h-[148px] w-full resize-none border-0 bg-transparent px-5 pb-2 pt-5 text-[15px] leading-relaxed text-foreground placeholder:text-[#4a4a66] focus-visible:outline-none sm:min-h-[160px] sm:px-6 sm:pt-6"
        />

        <div className="flex items-center justify-between gap-2 px-3 pb-3 pt-1 sm:px-4 sm:pb-4">
          <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
            <div className="flex items-center gap-1.5">
              <Clapperboard className="size-4 shrink-0 text-muted-foreground" aria-hidden />
              <Label htmlFor="home-style-select" className="sr-only">
                风格
              </Label>
              <NativeSelect
                id="home-style-select"
                value={style}
                aria-label="风格"
                iconClassName="min-w-0"
                className={nativeSelectPillClass}
                onChange={(e) => onStyleChange(e.target.value)}
              >
                {STYLE_PRESETS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </NativeSelect>
            </div>

            <div className="flex items-center gap-1.5">
              <Timer className="size-4 shrink-0 text-muted-foreground" aria-hidden />
              <Label htmlFor="home-duration-select" className="sr-only">
                时长
              </Label>
              <NativeSelect
                id="home-duration-select"
                value={String(duration)}
                aria-label="成片时长"
                iconClassName="min-w-0"
                className={nativeSelectPillClass}
                onChange={(e) => onDurationChange(Number(e.target.value))}
              >
                {DURATION_OPTIONS_SEC.map((sec) => (
                  <option key={sec} value={String(sec)}>
                    {sec} 秒
                  </option>
                ))}
              </NativeSelect>
            </div>
          </div>

          <Button
            type="button"
            size="icon"
            title={canStart ? "开始创建" : "请先填写创意与风格"}
            aria-label="开始创建流水线"
            disabled={busy || !canStart}
            aria-busy={busy}
            className="size-11 shrink-0 rounded-full border-0 bg-gradient-to-br from-violet-500 via-fuchsia-500 to-amber-400 text-white shadow-none hover:from-violet-500/95 hover:via-fuchsia-500/95 hover:to-amber-400/95 focus-visible:ring-fuchsia-400/45 disabled:opacity-40 sm:size-12"
            onClick={() => void onStart()}
          >
            <ArrowUp className="size-5 stroke-[2.5]" aria-hidden />
          </Button>
        </div>
      </div>
    </section>
  )
}
