import { Settings } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export type HomeSettingsTriggerVariant = "icon" | "sidebar"

export interface HomeSettingsDialogProps {
  imgConc: number
  onImgConcChange: (v: number) => void
  vidConc: number
  onVidConcChange: (v: number) => void
  /** 顶栏圆形按钮（默认）或侧栏导航行 */
  triggerVariant?: HomeSettingsTriggerVariant
  sidebarCollapsed?: boolean
}

/**
 * 首页右上角齿轮：并发等高级选项（从创作框迁出）。
 */
export function HomeSettingsDialog({
  imgConc,
  onImgConcChange,
  vidConc,
  onVidConcChange,
  triggerVariant = "icon",
  sidebarCollapsed = false,
}: HomeSettingsDialogProps) {
  const isSidebar = triggerVariant === "sidebar"

  return (
    <Dialog>
      <DialogTrigger asChild>
        {isSidebar ? (
          <button
            type="button"
            title={sidebarCollapsed ? "设置" : undefined}
            className={cn(
              "flex h-8 w-full flex-row items-center rounded-md px-2 py-1.5 transition",
              "text-muted-foreground hover:bg-muted hover:text-foreground",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/45",
            )}
          >
            <Settings className="size-4 shrink-0" aria-hidden />
            {!sidebarCollapsed ? (
              <span className="ml-2 truncate text-sm font-medium">设置</span>
            ) : null}
          </button>
        ) : (
          <Button
            type="button"
            variant="outline"
            size="icon-sm"
            className="size-9 shrink-0 rounded-full border-line-soft/80 bg-background/50 hover:bg-muted/50"
            aria-label="设置"
            title="设置"
          >
            <Settings className="size-[1.05rem]" aria-hidden />
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>设置</DialogTitle>
          <DialogDescription>创建流水线时的并发参数，一般保持默认即可。</DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 pt-2 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="settings-img-conc">生图并发</Label>
            <Input
              id="settings-img-conc"
              type="number"
              min={1}
              max={16}
              value={imgConc}
              onChange={(e) => onImgConcChange(Number(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">Step 5 同时生成几张图，范围 1–16。</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="settings-vid-conc">视频并发</Label>
            <Input
              id="settings-vid-conc"
              type="number"
              min={1}
              max={8}
              value={vidConc}
              onChange={(e) => onVidConcChange(Number(e.target.value))}
            />
            <p className="text-xs text-muted-foreground">Step 4 同时生成几段视频，范围 1–8。</p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
