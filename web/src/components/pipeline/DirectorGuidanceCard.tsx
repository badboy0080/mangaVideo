import { Lightbulb, Palette, Clock, Camera, Music } from "lucide-react"
import type { DirectorGuidance } from "@/lib/api"
import { cn } from "@/lib/utils"

export interface DirectorGuidanceCardProps {
  guidance: DirectorGuidance | null | undefined
  className?: string
}

const EMPTY = "—"

export function DirectorGuidanceCard({ guidance, className }: DirectorGuidanceCardProps) {
  if (!guidance || guidance.error) return null

  const hasContent =
    guidance.tone ||
    guidance.visual_style ||
    guidance.color_palette ||
    guidance.pacing ||
    guidance.shot_advice ||
    guidance.audio_direction ||
    (guidance.key_themes && guidance.key_themes.length > 0)

  if (!hasContent) return null

  return (
    <div className={cn(
      "rounded-2xl border border-accent-cool/25 bg-card/40 p-4 sm:p-5",
      className,
    )}>
      <div className="mb-3 flex items-center gap-2">
        <div className="flex size-6 items-center justify-center rounded-md bg-accent-cool/15">
          <Lightbulb className="size-3.5 text-accent-cool" />
        </div>
        <h3 className="text-sm font-semibold text-foreground">创意总监指导</h3>
      </div>

      <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
        {guidance.tone && (
          <InfoChip icon={<Lightbulb className="size-3" />} label="基调" value={guidance.tone} />
        )}
        {guidance.visual_style && (
          <InfoChip icon={<Palette className="size-3" />} label="视觉风格" value={guidance.visual_style} />
        )}
        {guidance.color_palette && (
          <InfoChip icon={<Palette className="size-3" />} label="色调" value={guidance.color_palette} />
        )}
        {guidance.pacing && (
          <InfoChip icon={<Clock className="size-3" />} label="节奏" value={guidance.pacing} />
        )}
        {guidance.shot_advice && (
          <InfoChip icon={<Camera className="size-3" />} label="分镜建议" value={guidance.shot_advice} />
        )}
        {guidance.audio_direction && (
          <InfoChip icon={<Music className="size-3" />} label="音频方向" value={guidance.audio_direction} />
        )}
      </div>

      {guidance.key_themes && guidance.key_themes.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {guidance.key_themes.map((t) => (
            <span
              key={t}
              className="inline-flex items-center rounded-full border border-accent-cool/20 bg-accent-cool/5 px-2.5 py-0.5 text-[11px] text-accent-cool/80"
            >
              {t}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function InfoChip({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2 rounded-lg border border-line-soft bg-background/40 px-3 py-2">
      <span className="mt-0.5 shrink-0 text-muted-foreground">{icon}</span>
      <div className="min-w-0">
        <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
        <p className="text-xs leading-relaxed text-foreground">{value || EMPTY}</p>
      </div>
    </div>
  )
}
