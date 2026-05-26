import { TiltCard } from "@/components/TiltCard"
import type { StylePreset } from "@/lib/run-presets"

const HOT_COPY: {
  title: string
  blurb: string
  preset: StylePreset
  /** web/public/presets/{thumb}.png，由 Seedream 4.5 生成 */
  thumb: string
}[] = [
  {
    title: "电影短片",
    blurb: "剧情节奏与人物弧光，适合叙事向短片。",
    preset: "电影短片",
    thumb: "movie",
  },
  {
    title: "品牌广告",
    blurb: "干净镜头与强记忆点，适合品牌向短内容。",
    preset: "品牌广告",
    thumb: "brand",
  },
  {
    title: "动画叙事",
    blurb: "夸张表演与风格化画面，适合番剧气质。",
    preset: "动画叙事",
    thumb: "anime",
  },
  {
    title: "游戏 CG",
    blurb: "预告片式高光与能力展示，适合版本 PV。",
    preset: "游戏CG",
    thumb: "gamecg",
  },
  {
    title: "科幻短片",
    blurb: "未来设定与视觉奇观，适合概念短片。",
    preset: "科幻短片",
    thumb: "scifi",
  },
  {
    title: "纪录片风格",
    blurb: "克制真实、旁白与观察镜头并重。",
    preset: "纪录片风格",
    thumb: "doc",
  },
  {
    title: "MV 节奏",
    blurb: "强节拍剪辑，画面跟音乐走。",
    preset: "MV",
    thumb: "mv",
  },
]

export interface HotSkillsRowProps {
  onPickPreset: (preset: string) => void
}

/**
 * Flova 「热门预设」：横向卡片 + Seedream 缩略图 + 标题/简介。
 */
export function HotSkillsRow({ onPickPreset }: HotSkillsRowProps) {
  return (
    <section id="home-hot-skills" className="scroll-mt-24 space-y-6">
      <h2 className="flova-section-title text-foreground">热门预设</h2>
      <div className="-mx-4 flex gap-3 overflow-x-auto px-4 pb-1 pt-0.5 mp-scrollbar sm:mx-0 sm:px-0">
        {HOT_COPY.map((item) => (
          <button
            key={item.preset}
            type="button"
            onClick={() => onPickPreset(item.preset)}
            className="shrink-0 border-0 bg-transparent p-0 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            <TiltCard
              tiltLimit={12}
              scale={1.04}
              effect="evade"
              className="flova-content-card aspect-[16/10] min-w-[176px] max-w-[192px] bg-transparent dark:hover:bg-transparent sm:min-w-[192px]"
            >
              <img
                src={`/presets/${item.thumb}.png`}
                alt=""
                className="absolute inset-0 size-full object-cover"
                loading="lazy"
                decoding="async"
              />
              <div className="absolute inset-x-0 bottom-0 z-[1] bg-gradient-to-t from-black/80 via-black/50 to-transparent px-3 pb-2.5 pt-8">
                <p className="text-[0.7rem] font-semibold leading-snug text-[#e8e8ee] sm:text-xs">{item.title}</p>
                <p className="mt-0.5 line-clamp-2 text-[0.625rem] leading-relaxed text-white/75 sm:text-[0.6875rem]">
                  {item.blurb}
                </p>
              </div>
            </TiltCard>
          </button>
        ))}
      </div>
    </section>
  )
}
