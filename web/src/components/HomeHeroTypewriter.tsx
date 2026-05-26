import { useEffect, useState } from "react"

import { cn } from "@/lib/utils"

const ROTATING_PHRASES = [
  { prefix: "有什么", highlight: "新想法？" },
  { prefix: "有什么", highlight: "新剧本？" },
  { prefix: "有什么", highlight: "广告案？" },
  { prefix: "有什么", highlight: "新动画？" },
] as const

const TYPE_MS = 85
const DELETE_MS = 45
const PAUSE_FULL_MS = 2200
const PAUSE_EMPTY_MS = 280

/** 与进度链、发送按钮一致的主题渐变，用于名词高亮 */
const HIGHLIGHT_GRADIENT =
  "bg-gradient-to-r from-violet-400 via-fuchsia-400 to-teal-400 bg-clip-text text-transparent"

interface HomeHeroTypewriterProps {
  className?: string
}

export function HomeHeroTypewriter({ className }: HomeHeroTypewriterProps) {
  const [phraseIndex, setPhraseIndex] = useState(0)
  const [charCount, setCharCount] = useState(0)
  const [deleting, setDeleting] = useState(false)

  const phrase = ROTATING_PHRASES[phraseIndex]
  const full = phrase.prefix + phrase.highlight

  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>

    if (!deleting && charCount < full.length) {
      timeout = setTimeout(() => setCharCount((c) => c + 1), TYPE_MS)
    } else if (!deleting && charCount === full.length) {
      timeout = setTimeout(() => setDeleting(true), PAUSE_FULL_MS)
    } else if (deleting && charCount > 0) {
      timeout = setTimeout(() => setCharCount((c) => c - 1), DELETE_MS)
    } else if (deleting && charCount === 0) {
      timeout = setTimeout(() => {
        setDeleting(false)
        setPhraseIndex((i) => (i + 1) % ROTATING_PHRASES.length)
      }, PAUSE_EMPTY_MS)
    }

    return () => clearTimeout(timeout)
  }, [charCount, deleting, full.length])

  const displayed = full.slice(0, charCount)
  const prefixLen = phrase.prefix.length
  const shownPrefix = displayed.slice(0, Math.min(displayed.length, prefixLen))
  const shownHighlight = displayed.slice(prefixLen)

  return (
    <h1
      className={cn(
        "text-balance text-[clamp(1.6rem,3vw,2.4rem)] font-bold leading-tight tracking-tight text-[#e8e8ee]",
        className,
      )}
    >
      <span>导演，今天</span>
      <span aria-live="polite" className="inline-block whitespace-nowrap text-left">
        {shownPrefix}
        {shownHighlight ? <span className={HIGHLIGHT_GRADIENT}>{shownHighlight}</span> : null}
        <span
          className="ml-0.5 inline-block h-[0.85em] w-[3px] animate-pulse rounded-sm bg-gradient-to-b from-violet-400 to-fuchsia-400 align-[-0.08em]"
          aria-hidden
        />
      </span>
    </h1>
  )
}
