/** 首页 Aurora 动效背景（仅装饰层，pointer-events: none） */
export function AuroraBackground() {
  return (
    <div className="aurora-bg pointer-events-none absolute inset-0 overflow-hidden bg-black" aria-hidden>
      <div className="absolute inset-0 saturate-50">
        <div className="absolute inset-0 opacity-[0.35]">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 via-purple-900/15 to-indigo-900/20" />
        </div>

        <div className="absolute inset-0">
          <div className="aurora-wave aurora-wave-1 absolute inset-0 opacity-30" />
          <div className="aurora-wave aurora-wave-2 absolute inset-0 opacity-[0.25]" />
          <div className="aurora-wave aurora-wave-3 absolute inset-0 opacity-20" />
          <div className="aurora-wave aurora-wave-4 absolute inset-0 opacity-[0.15]" />
        </div>

        <div className="absolute inset-0 bg-gradient-to-t from-black/10 via-transparent to-black/5" />
      </div>
    </div>
  )
}
