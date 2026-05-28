import { ChevronDown } from "lucide-react"
import * as React from "react"

import { cn } from "@/lib/utils"

export const nativeSelectTriggerClass =
  "flex h-9 w-full cursor-pointer appearance-none rounded-md bg-muted/35 px-3 py-2 pe-9 text-sm text-foreground shadow-none outline-none transition-colors hover:bg-muted/50 focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 dark:bg-muted/45"

/** Flova 风格工具条：全圆角胶囊 + 无明显线框 */
export const nativeSelectPillClass =
  "h-10 rounded-full border-0 bg-muted/40 pe-9 ps-4 text-[13px] font-medium dark:bg-muted/50 dark:hover:bg-muted/65"

interface NativeSelectProps extends React.ComponentPropsWithoutRef<"select"> {
  /** 右侧留白给箭头图标 */
  iconClassName?: string
  leadingIcon?: React.ReactNode
}

/**
 * 原生 &lt;select&gt; + 统一样式（无外框线，与 Input 家族一致）。
 */
const NativeSelect = React.forwardRef<HTMLSelectElement, NativeSelectProps>(
  ({ className, iconClassName, leadingIcon, children, disabled, ...props }, ref) => {
    return (
      <div className={cn("relative min-w-[7rem]", iconClassName)}>
        {leadingIcon ? (
          <span className="pointer-events-none absolute start-3 top-1/2 flex size-4 -translate-y-1/2 items-center justify-center text-muted-foreground">
            {leadingIcon}
          </span>
        ) : null}
        <select
          ref={ref}
          disabled={disabled}
          className={cn(nativeSelectTriggerClass, className, leadingIcon ? "ps-9" : "")}
          {...props}
        >
          {children}
        </select>
        <ChevronDown
          className="pointer-events-none absolute end-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground opacity-70"
          aria-hidden
        />
      </div>
    )
  },
)
NativeSelect.displayName = "NativeSelect"

export { NativeSelect }
