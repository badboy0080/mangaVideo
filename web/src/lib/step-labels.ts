const STEP_TITLES_ZH: Record<number, string> = {
  1: "剧本",
  2: "分镜",
  3: "资产",
  4: "视频",
  5: "成片",
}

export function stepTitleZh(step: number): string {
  return STEP_TITLES_ZH[step] ?? `步骤 ${step}`
}
