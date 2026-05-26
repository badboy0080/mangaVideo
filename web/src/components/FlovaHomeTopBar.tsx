export interface FlovaHomeTopBarProps {
  apiWarn: string | null
  healthDismissed: boolean
  onDismissHealth: () => void
}

/**
 * 首页顶栏：仅在有 API 提示时显示横幅。
 */
export function FlovaHomeTopBar({ apiWarn, healthDismissed, onDismissHealth }: FlovaHomeTopBarProps) {
  if (!apiWarn || healthDismissed) return null

  return (
    <header className="sticky top-0 z-40 shrink-0 bg-background/55 backdrop-blur-xl supports-[backdrop-filter]:bg-background/40">
      <div className="border-t border-line-soft px-4 py-2 sm:px-6">
        <div className="flex flex-wrap items-start gap-2 rounded-2xl bg-amber-500/[0.09] px-3 py-2.5 text-sm text-amber-950 dark:text-amber-50">
          <p className="min-w-0 flex-1 leading-snug">{apiWarn}</p>
          <button
            type="button"
            className="shrink-0 rounded-lg bg-background/90 px-2.5 py-1.5 text-xs font-medium transition-colors hover:bg-muted/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            onClick={onDismissHealth}
          >
            关闭
          </button>
        </div>
      </div>
    </header>
  )
}
