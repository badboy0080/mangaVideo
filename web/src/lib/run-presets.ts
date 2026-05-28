/** Step 1 / Step 2 沿用的风格预设（与新建表单共用；须与后端 STYLE_PRESETS 一致） */
export const STYLE_PRESETS = [
  "电影短片",
  "品牌广告",
  "动画叙事",
  "游戏CG",
  "MV",
  "科幻短片",
  "纪录片风格",
] as const

export type StylePreset = (typeof STYLE_PRESETS)[number]

export function isStylePreset(s: string): s is StylePreset {
  return (STYLE_PRESETS as readonly string[]).includes(s)
}

/** 成片目标时长（秒）下拉选项 */
export const DURATION_OPTIONS_SEC = [30, 45, 60, 90, 120, 180, 300] as const
