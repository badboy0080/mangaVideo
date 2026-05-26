import { useState } from "react"
import { motion } from "framer-motion"
import { BookOpen, Flame, FolderKanban, Home, LayoutGrid, type LucideIcon } from "lucide-react"

import logoImg from "@/assets/logo_3.png"
import { HomeSettingsDialog } from "@/components/HomeSettingsDialog"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"

export type HomeShellView = "home" | "projects"

export interface FlovaHomeSidebarProps {
  homeView: HomeShellView
  onHome: () => void
  onMyProjects: () => void
  onScrollHotSkills: () => void
  onScrollProjects: () => void
  imgConc: number
  onImgConcChange: (v: number) => void
  vidConc: number
  onVidConcChange: (v: number) => void
}

const sidebarVariants = {
  open: { width: "15rem" },
  closed: { width: "3.05rem" },
}

const labelVariants = {
  open: { x: 0, opacity: 1, transition: { x: { stiffness: 1000, velocity: -100 } } },
  closed: { x: -12, opacity: 0, transition: { x: { stiffness: 100 } } },
}

const transitionProps = {
  type: "tween" as const,
  ease: "easeOut" as const,
  duration: 0.2,
}

function scrollToComposer() {
  const el = document.getElementById("home-composer")
  const scroller = document.getElementById("home-main-scroll")
  if (!el) return
  if (scroller) {
    const scrollerRect = scroller.getBoundingClientRect()
    const elRect = el.getBoundingClientRect()
    const top = scroller.scrollTop + (elRect.top - scrollerRect.top) - 12
    scroller.scrollTo({ top: Math.max(0, top), behavior: "smooth" })
    return
  }
  el.scrollIntoView({ behavior: "smooth", block: "start" })
}

function SidebarNavItem({
  icon: Icon,
  label,
  active,
  isCollapsed,
  onClick,
}: {
  icon: LucideIcon
  label: string
  active?: boolean
  isCollapsed: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={isCollapsed ? label : undefined}
      className={cn(
        "flex h-8 w-full flex-row items-center rounded-md px-2 py-1.5 transition",
        "text-muted-foreground hover:bg-muted hover:text-foreground",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/45",
        active && "bg-muted text-accent-cool",
      )}
    >
      <Icon className="size-4 shrink-0" aria-hidden />
      {!isCollapsed ? (
        <motion.span
          variants={labelVariants}
          initial={false}
          animate="open"
          className="ml-2 truncate text-sm font-medium"
        >
          {label}
        </motion.span>
      ) : null}
    </button>
  )
}

/**
 * 首页侧栏：悬停展开 / 收起，适配漫剧流水线导航。
 */
export function FlovaHomeSidebar({
  homeView,
  onHome,
  onMyProjects,
  onScrollHotSkills,
  onScrollProjects,
  imgConc,
  onImgConcChange,
  vidConc,
  onVidConcChange,
}: FlovaHomeSidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(true)

  return (
    <motion.aside
      className="relative z-40 flex h-full shrink-0 overflow-hidden border-r border-line-soft/60 bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60"
      initial={isCollapsed ? "closed" : "open"}
      animate={isCollapsed ? "closed" : "open"}
      variants={sidebarVariants}
      transition={transitionProps}
      onMouseEnter={() => setIsCollapsed(false)}
      onMouseLeave={() => setIsCollapsed(true)}
    >
      <motion.div className="flex h-full w-full flex-col text-muted-foreground">
        <motion.div className="flex h-[54px] w-full shrink-0 items-center border-b border-line-soft/60 px-2">
          <button
            type="button"
            onClick={onHome}
            className="flex w-full items-center gap-2 rounded-md px-1 py-1 transition hover:bg-muted/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/45"
            aria-label="回到首页"
          >
            <img
              src={logoImg}
              alt="漫剧"
              className={cn(
                "object-contain object-left transition-all duration-200",
                isCollapsed ? "h-8 w-8" : "h-9 w-auto max-w-[10rem]",
              )}
            />
          </button>
        </motion.div>

        <nav className="flex min-h-0 flex-1 flex-col p-2" aria-label="主导航">
          <motion.div className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto mp-scrollbar">
            <SidebarNavItem
              icon={Home}
              label="首页"
              active={homeView === "home"}
              isCollapsed={isCollapsed}
              onClick={onHome}
            />
            <SidebarNavItem
              icon={FolderKanban}
              label="我的项目"
              active={homeView === "projects"}
              isCollapsed={isCollapsed}
              onClick={onMyProjects}
            />
            <Separator className="my-1" />
            <SidebarNavItem
              icon={Flame}
              label="热门预设"
              isCollapsed={isCollapsed}
              onClick={onScrollHotSkills}
            />
            <SidebarNavItem
              icon={LayoutGrid}
              label="最近项目"
              isCollapsed={isCollapsed}
              onClick={onScrollProjects}
            />
          </motion.div>

          <div className="mt-2 flex shrink-0 flex-col gap-1 border-t border-line-soft/60 pt-2">
            <SidebarNavItem
              icon={BookOpen}
              label="创作提示"
              isCollapsed={isCollapsed}
              onClick={scrollToComposer}
            />
            <HomeSettingsDialog
              imgConc={imgConc}
              onImgConcChange={onImgConcChange}
              vidConc={vidConc}
              onVidConcChange={onVidConcChange}
              triggerVariant="sidebar"
              sidebarCollapsed={isCollapsed}
            />
          </div>
        </nav>
      </motion.div>
    </motion.aside>
  )
}
