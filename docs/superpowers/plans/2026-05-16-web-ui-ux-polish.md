# Web Console UX / Visual Polish Implementation Plan

> **For agentic workers:** RECOMMENDED: Use superpowers `subagent-driven-development` or `executing-plans` to implement task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 提升「漫剧流水线控制台」的**可读性、操作反馈与视觉一致性**，在不大改后端契约的前提下优化前端交互与设计风格。

**Architecture:** 保持 **Vite + React + TS + Tailwind + 现有 shadcn 风格组件**；将 **`App.tsx` 拆成若干专职组件与 hooks**，把 API、格式化与运行详情视图分离；用 **CSS 变量主题层**统一色相与圆角，必要时补充 **轻量 Sonner/自建 toast** 做反馈。**不搞**大规模换框架。

**Tech Stack:** React 18、TypeScript、Tailwind CSS、lucide-react、Radix/shadcn 组件（`web/src/components/ui/*`）。

---

## File map（将要创建 / 修改）

| 区域 | 文件 | 职责 |
|------|------|------|
| 入口 | `web/index.html` | `<title>`、`lang`、可选字体 preload |
| 全局样式 | `web/src/index.css` | `:root` / `.dark` 设计令牌（主色、surface、阴影） |
| 布局 | `web/src/App.tsx` | 组合布局与路由级状态（变薄） |
| 新建 | `web/src/lib/api.ts` | `apiJson` / `apiText` / `fileUrl` / 类型 |
| 新建 | `web/src/hooks/useRuns.ts`（或拆分多个 hook） | 列表、详情轮询、step log/artifacts 加载 |
| 新建 | `web/src/components/NewRunForm.tsx` | 新建运行表单 |
| 新建 | `web/src/components/RunSidebar.tsx` | 历史运行列表 |
| 新建 | `web/src/components/RunHeader.tsx` | 当前 run 元数据 + 成片链接 |
| 新建 | `web/src/components/StepPipelineCard.tsx` | 单步卡片（执行 / 日志 / 产物） |
| 新建 | `web/src/components/PipelineProgress.tsx`（可选） | 顶部 8 步横向进度条 |
| UI（按需） | `web/src/components/ui/*` | 仅当缺组件时加 `toast`、`skeleton`、`separator`、`scroll-area` |

---

### Task 1: 设计令牌与页面基调（低成本高收益）

**Files:**
- Modify: `web/src/index.css`
- Modify: `web/index.html`

- [ ] **Step 1:** 将 `index.html` 的 `lang` 改为 `zh-CN`，`title` 改为「漫剧流水线控制台」或产品名。
- [ ] **Step 2:** 在 `:root` 定义一层**偏创作工具**的配色（例如深蓝主色 + 中性 surface），保留明暗可读对比；**可选**增加 `.dark` 与同结构的暗色变量（若只做亮色也可）。
- [ ] **Step 3:** 给 `body` 增加极淡的背景渐变或 noise（纯 CSS，避免大图资产）。
- [ ] **验证：** `npm run dev`，明暗对比与表单可读性正常。

---

### Task 2: 拆分 `App.tsx`（可维护性 + 交互地基）

**Files:**
- Modify: `web/src/App.tsx`（缩减至布局 + state 注入）
- Create: `web/src/lib/api.ts`
- Create: `web/src/components/NewRunForm.tsx`
- Create: `web/src/components/RunSidebar.tsx`
- Create: `web/src/components/RunHeader.tsx`
- Create: `web/src/components/StepPipelineCard.tsx`

- [ ] **Step 1:** 抽出 `apiJson` / `apiText` / `fileUrl` / 共享类型到 `lib/api.ts`，`App.tsx` 只做 import。
- [ ] **Step 2:** `NewRunForm`：主题、时长、风格、并发字段；底部主按钮；保留现有校验行为。
- [ ] **Step 3:** `RunSidebar`：列表项 hover/active、空状态文案、加载中 skeleton（可用简单 `animate-pulse` 块）。
- [ ] **Step 4:** `RunHeader`：`run_id`、out_dir 可复制、`final_mp4` 外链样式突出。
- [ ] **Step 5:** `StepPipelineCard`：封装单卡逻辑（状态 Badge、执行/重做、折叠日志与产物）。
- [ ] **验证：** `npm run build` 无 TS 错误；手动点选运行、展开日志仍可用。

---

### Task 3: 交互优化（用户「知道系统在干什么」）

**Files:**
- Modify: `web/src/App.tsx` 或新建 `hooks/useRuns.ts`
- Modify: `web/src/components/StepPipelineCard.tsx`

- [ ] **Step 1:** 「执行步骤」点击后：**立刻禁用按钮**并显示 loading（已有部分）；避免重复 POST（`busy` 逻辑复核）。
- [ ] **Step 2:** 详情加载中：右侧主体显示 **Skeleton** 而非空白。
- [ ] **Step 3:** 错误区（红色 alert）：支持 **一键复制**错误全文（小图标按钮）。
- [ ] **Step 4:** `/api/health` 告警条：改为 **可关闭**（localStorage 记住「本次会话忽略」可选）。
- [ ] **验证：** 网络失败 / 409 / 400 时文案仍可读。

---

### Task 4: 步骤视图信息架构（减少噪音）

**Files:**
- Modify: `web/src/components/StepPipelineCard.tsx`

- [ ] **Step 1:** 默认 **折叠**「运行日志」「产物预览」；成功步骤仅显示一行摘要（更新时间）。
- [ ] **Step 2:** `running` 步骤自动展开日志（可选），结束后折叠。
- [ ] **Step 3:** 产物预览：图片 grid **固定高度 + 点击放大**（简易 dialog 或 `target=_blank` 保留）。
- [ ] **验证：** 8 步列表首屏可扫完。

---

### Task 5: 表单与设计细节（风格预设 + 可达性）

**Files:**
- Modify: `web/src/components/NewRunForm.tsx`

- [ ] **Step 1:** 「风格类型」增加 **快捷 chips**（电影短片 / 广告片 / 动画短片），点击填入输入框，仍可自定义。
- [ ] **Step 2:** `Label` 与 `Input` 增加 `htmlFor` / `id` 已全部对齐（复核）。
- [ ] **Step 3:** 主要按钮与 destructive 状态使用足够对比色（依赖 Task 1 令牌）。
- [ ] **验证：** 键盘 Tab 可走完表单。

---

### Task 6（可选）: 横向流水线进度条

**Files:**
- Create: `web/src/components/PipelineProgress.tsx`

- [ ] **Step 1:** 在 `RunHeader` 下方渲染 8 段进度（pending / running / success / failed 颜色映射）。
- [ ] **Step 2:** 点击某段可滚动到对应卡片（`scrollIntoView` + `id={`step-${n}`}`）。
- [ ] **验证：** 与轮询刷新同步。

---

## Testing checklist（手动）

- [ ] 新建运行 → 选中 → 逐步执行 1–3 步，日志与 artifacts 正常。
- [ ] 后端故意关掉 → 顶部告警与错误卡片可读。
- [ ] `npm run build` 通过。

---

## Out of scope（本轮不做）

- 替换组件库 / 引入重型图表库。
- 后端 API 改动（除非发现前端刚需）。
- 国际化完整 i18n（仅先把页面语言和标题本地化）。

---

## 给你的说明（产品经理可读）

- **`/write-plan` 命令将来会删掉**，以后可以说：**「用 writing-plans 技能写实施计划」**，我会按技能把计划落到 `docs/superpowers/plans/` 并拆成可勾选任务。
- 上面这份计划**不要求你先懂代码**：优先级是 **看得懂进度、少点错、界面更像 production 控制台**。
