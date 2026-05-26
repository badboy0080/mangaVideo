# handoff-log

## 当前接手摘要

- **项目**：漫剧流水线（manga-pipeline），含 `web` 控制台与 Python 流水线。
- **近期主题**：流水线产物**文档内分段编辑**（Step 1/2/3/4/6）；保存写回磁盘；「运行此步骤」按钮。
- **导航**：侧栏「我的项目」→ `homeView=projects`；「项目」在首页滚到 `#home-projects`，在「我的项目」页则回到首页并定位预览区。
- **文档**：[`docs/designRules`](docs/designRules)；[`docs/prompt-alignment-feasibility.md`](docs/prompt-alignment-feasibility.md)。

## 最近工作记录

### 2026-05-20 — 新增本地启动说明文档

- **用户目标**：写一份本地启动说明，方便每次启动项目。
- **产出**：根目录 [`启动说明.md`](启动说明.md)（环境、首次安装、双终端启动、自检、常见问题）。
- **验证**：内容与 README、`.env.example` 一致。

### 2026-05-20 — 最近项目卡片：上图下文 + 最后编辑时间

- **用户目标**：项目卡片采用参考样式——圆角封面图 + 暗色底框标题 +「最后编辑于」时间。
- **改动**：[`FlovaRecentProjects.tsx`](web/src/components/FlovaRecentProjects.tsx)、[`index.css`](web/src/index.css) `.project-run-card`；后端 `list_runs` 增加 `updated_at`。
- **验证**：`pnpm run build` 通过。

### 2026-05-20 — 最近项目卡片标题两行截断

- **用户目标**：「最近项目」卡片项目名最多两行，超出用 `...`。
- **改动**：[`index.css`](web/src/index.css) 新增 `.project-card-title`；[`FlovaRecentProjects.tsx`](web/src/components/FlovaRecentProjects.tsx) 应用并加 `title` 悬停全文。
- **验证**：`pnpm run build` 通过。

### 2026-05-20 — 顶栏项目名截断/可改 + 步骤中文名 + 运行全部步骤

- **用户目标**：项目名最多显示 5 字+`...`，点击可改；步骤副标题改中文简称；「运行全部步骤」放到「产物预览」行右侧。
- **改动**：[`ProjectRunTitle.tsx`](web/src/components/pipeline/ProjectRunTitle.tsx)、`PATCH /api/runs/{id}` 改 topic；[`step-labels.ts`](web/src/lib/step-labels.ts) + 后端 `STEP_LABELS` 中文化；[`StepArtifactsPanel`](web/src/components/pipeline/StepArtifactsPanel.tsx) 运行全部按钮。
- **验证**：`pnpm run build` 通过。

### 2026-05-20 — 编辑区暗色底框 + 拉高可编辑区域

- **用户目标**：编辑态底框用暗色系；拉高编辑区，一次能看到更多内容便于改稿。
- **改动**：[`editors/shared.tsx`](web/src/components/pipeline/editors/shared.tsx) 暗色 `EditSection`/textarea；[`EditableArtifactPanel`](web/src/components/pipeline/EditableArtifactPanel.tsx) 编辑态整体暗底 + 编辑区 `min-h 65vh`；各步骤编辑器主文本框改用 `editTextareaTallClass`/`MediumClass`。
- **验证**：`pnpm run build` 通过。

### 2026-05-20 — 流水线文档内分段编辑

- **用户目标**：工作台分镜、提示词等文档可在「文档视图」内按章节/分镜块编辑，保存后写回磁盘供下一步读取；不自动跑下一步。
- **后端**：`PUT /api/runs/{id}/steps/{step}/artifacts/text`（[`server/main.py`](server/main.py)、[`pipeline_runner.py`](server/pipeline_runner.py)）；Step 2 同步 `script_data.json` + `shots` 重算。
- **前端**：[`EditableArtifactPanel`](web/src/components/pipeline/EditableArtifactPanel.tsx)、5 个步骤编辑器、[`artifact-parse.ts`](web/src/lib/artifact-parse.ts)、[`script-split.ts`](web/src/lib/script-split.ts)；未保存切换步骤 confirm；「运行此步骤」按钮。
- **验证**：`pnpm run build` 通过；Python 脚本验证 Step 2 保存后 `script.md`/`script_data.json` 一致且 `shots=2`。
- **待办**：Element 标签卡片式富文本编辑（截图样式）留待下期；改内容后需手动点「运行此步骤」重跑下游。

### 2026-05-19 — 项目历程报告（经验沉淀）

- **用户目标**：把做本工具的完整历程写成报告（诞生、实现、痛点、技术、踩坑、经验），供下次同类项目查阅。
- **产出**：[`docs/project-journey-report.md`](docs/project-journey-report.md)（十节：背景、痛点、功能、技术栈、设计决策、踩坑、checklist、待办、目录索引）。
- **验证**：文档与 README、handoff-log、prompt 文档交叉核对。

### 2026-05-19 — 热门预设：TiltCard 3D 倾斜 + 光斑

- **用户目标**：热门预设卡片接入 TiltCard（鼠标跟随倾斜、缩放、光斑）。
- **改动**：新增 [`TiltCard.tsx`](web/src/components/TiltCard.tsx)；[`HotSkillsRow.tsx`](web/src/components/HotSkillsRow.tsx) 每张卡外包 TiltCard。
- **验证**：`pnpm run build` 通过。

### 2026-05-19 — 热门预设：缩小 20% + 文字叠在图上

- **用户目标**：卡片缩小 20%；标题/简介叠在图片底部；底部黑色半透明渐变保证可读；去掉下方独立文本底框。
- **改动**：[`HotSkillsRow.tsx`](web/src/components/HotSkillsRow.tsx) 宽 220/240→176/192px；单块图片卡 + `from-black/80` 底部渐变 overlay。
- **验证**：`pnpm run build` 通过。

### 2026-05-19 — 清理未使用的旧代码与重复目录

- **用户目标**：删除项目中不再使用的代码文件。
- **已删 Web 旧组件（6）**：`RunSidebar`、`StepPipelineCard`、`NewRunForm`、`FinishedClipsGrid`、`PipelineProgress`、`RunHeader`（已被 `RunPipelineView` + 首页 `HomeComposer` 取代）。
- **已删其它**：`web/src/App.css`（Vite 默认，未引用）；`logo_1.png`、`logo_2.png`（未用）；脚本 `finalize_app_tsx.py`、`patch_app_run_detail_ui.py`、`fix_app_encoding.py`（旧 UI 修补，已由 `restore_app_chinese.py` 替代）。
- **已删重复旧工程**：嵌套目录 `manga-pipeline/` 下全部源码与 demo 产物（38 个文件）。
- **CSS**：移除未再使用的 `.bg-home-gradient`。
- **验证**：`pnpm run build` 通过。
- **待手动**：根目录 `output/` 为旧 demo 数据（非代码），空目录 `manga-pipeline/` 若仍存在可手动删文件夹。

### 2026-05-19 — 首页标题：打字机轮播 + 名词主题色

- **用户目标**：「导演，今天」固定；后半句打字机效果，轮播「新想法/新剧本/广告案/新动画」；「有什么」后的名词用主题渐变色。
- **改动**：新增 [`HomeHeroTypewriter.tsx`](web/src/components/HomeHeroTypewriter.tsx)；[`HomePage.tsx`](web/src/components/HomePage.tsx) 接入。
- **验证**：`pnpm run build` 通过。

### 2026-05-19 — Aurora 背景：透明度与饱和度各降 50%

- **用户目标**：首页 Aurora 动效更柔和——透明度减半、颜色饱和度减半。
- **改动**：[`AuroraBackground.tsx`](web/src/components/AuroraBackground.tsx) 各层 `opacity` 与渐变 alpha 减半，外层加 `saturate-50`；[`index.css`](web/src/index.css) `.aurora-wave-1~4` 的 rgba alpha 减半。
- **验证**：`pnpm run build` 通过。

### 2026-05-19 — 首页 Aurora 动效背景

- **用户目标**：首页仅加 Aurora 背景层，不改现有布局与内容。
- **改动**：[`AuroraBackground.tsx`](web/src/components/AuroraBackground.tsx)；[`index.css`](web/src/index.css) 动画；[`App.tsx`](web/src/App.tsx) 首页分支挂载背景。
- **验证**：`pnpm run build` 通过。

### 2026-05-19 — JSON 产物解析为排版 Markdown 文档

- **用户目标**：Step 1 等 JSON 文本默认显示为标题清晰、无字段名的易读文档，而非 raw JSON。
- **改动**：[`web/src/lib/json-to-markdown.ts`](web/src/lib/json-to-markdown.ts)；[`TextContentViewer.tsx`](web/src/components/TextContentViewer.tsx) 默认「文档」Tab；[`StepArtifactsPanel.tsx`](web/src/components/pipeline/StepArtifactsPanel.tsx) 标签改为「文档」。
- **验证**：`pnpm run build` 通过。

### 2026-05-19 — 流水线进度链：主题渐变圆点 + 等距 + 无外框

- **用户目标**：进度条用主题色渐变圆形、节点等距、去掉外边框。
- **改动**：[`PipelineStepChain.tsx`](web/src/components/pipeline/PipelineStepChain.tsx)。
- **验证**：`pnpm run build` 通过。

### 2026-05-19 — 更新 README.md

- **用户目标**：同步项目现状到根目录 README（Web 控制台、8 步流水线、环境配置、目录结构、中文乱码检查等）。
- **改动**：[`README.md`](README.md)。
- **验证**：内容与当前 `server/`、`web/`、`pipeline.py` 一致。

### 2026-05-19 — 修复流水线操作页中文问号 + 防复发规则

- **现象**：流水线操作页（及详情顶栏）大量 `????`。
- **原因**：`App.tsx` 再次被非 UTF-8 方式编辑损坏（与历次相同）。
- **修复**：运行 [`scripts/restore_app_chinese.py`](scripts/restore_app_chinese.py)；新增 [`scripts/check_ui_chinese.py`](scripts/check_ui_chinese.py)、[`.cursor/rules/web-utf8-chinese.mdc`](.cursor/rules/web-utf8-chinese.mdc)。
- **验证**：`check_ui_chinese.py` exit 0；改 App.tsx 后必须先跑 restore + check。

### 2026-05-19 — 首页：悬停展开侧栏（SessionNavBar 风格）

- **用户目标**：按提供的 SessionNavBar 代码改造首页左侧导航。
- **改动**：重写 [`FlovaHomeSidebar.tsx`](web/src/components/FlovaHomeSidebar.tsx)（framer-motion 悬停展开/收起、Logo、首页/我的项目/热门/最近项目/创作提示/设置）；[`HomeSettingsDialog.tsx`](web/src/components/HomeSettingsDialog.tsx) 支持侧栏触发；[`FlovaHomeTopBar.tsx`](web/src/components/FlovaHomeTopBar.tsx) 仅保留 API 警告；新增 `framer-motion`、`ui/separator.tsx`。
- **验证**：`pnpm run build` 通过。

### 2026-05-19 — 修复产物请求风暴（ERR_INSUFFICIENT_RESOURCES / 页面抖动）

- **现象**：控制台大量 `steps/N/artifacts` 失败、页面抖动。
- **原因**：轮询更新 `detail.steps` 时仍对 8 步批量拉产物 + 重复请求无去重。
- **修复**：[`RunPipelineView.tsx`](web/src/components/pipeline/RunPipelineView.tsx) 仅拉当前 `activeStep`；[`App.tsx`](web/src/App.tsx) 产物请求 in-flight/缓存去重、轮询 `refreshDetail` 改为 silent。
- **验证**：`pnpm run build` 通过；刷新详情页后 Network 应只见当前步骤产物请求。

### 2026-05-19 — 流水线操作页：单步展示 + 进度链切换

- **用户目标**：工作流控制台一次只显示一个步骤的产物；点击顶部进度链切换步骤（不再 8 步全部平铺）。
- **改动**：[`StepArtifactsPanel.tsx`](web/src/components/pipeline/StepArtifactsPanel.tsx) 仅渲染 `activeStep`；[`PipelineStepChain.tsx`](web/src/components/pipeline/PipelineStepChain.tsx) 点击只 `onStepChange`；[`RunPipelineView.tsx`](web/src/components/pipeline/RunPipelineView.tsx) 切换步骤时拉取产物。
- **验证**：`pnpm run build` 通过。

### 2026-05-19 — 首页：侧栏 Logo 再放大 20%

- **用户目标**：Logo 在上一版基础上再放大 20%。
- **改动**：[`FlovaHomeSidebar.tsx`](web/src/components/FlovaHomeSidebar.tsx) `h-12→h-[3.6rem]`（约 58px）、`max-w` 同步至 `4.68rem`。
- **验证**：待用户刷新确认；侧栏宽约 76px，logo 已接近满宽。

### 2026-05-19 — 首页：侧栏 Logo 放大 + 去掉侧栏细线

- **用户目标**：Logo 再放大 20%；去掉侧栏右侧与底部「提示」区分割线。
- **改动**：[`FlovaHomeSidebar.tsx`](web/src/components/FlovaHomeSidebar.tsx) `h-10→h-12`、`max-w` 同步 +20%；移除 `border-r`、`border-t`。
- **验证**：`pnpm run build` 通过。

### 2026-05-19 — 首页：侧栏 Logo + 去掉顶栏细线

- **用户目标**：`web/src/assets/logo_3.png` 放到首页左上角；删除首页顶栏底部分割线。
- **改动**：[`FlovaHomeSidebar.tsx`](web/src/components/FlovaHomeSidebar.tsx)；[`FlovaHomeTopBar.tsx`](web/src/components/FlovaHomeTopBar.tsx) 去掉 `border-b`。
- **验证**：`pnpm run build` 通过。

### 2026-05-19 — 流水线操作页：进度链 + 产物平铺 + 底部日志

- **用户目标**：去掉红框内元信息/一键执行/单步卡片/上下步；顶部圆形+虚线进度链；下方每步产物直接展示；日志折叠在页底。
- **新增**：`web/src/components/pipeline/`（`PipelineStepChain`、`StepArtifactsPanel`、`ArtifactTextBlock`、`ArtifactMediaCard`、`PipelineRunLogs`、`RunPipelineView`）。
- **改动**：[`web/src/App.tsx`](web/src/App.tsx) 详情区改用 `RunPipelineView`。
- **验证**：`pnpm run build` 通过。

### 2026-05-19 — 修复 App.tsx 中文乱码（页面显示问号）

- **现象**：控制台多处按钮/提示显示 `????`。
- **原因**：`App.tsx` 在先前编辑时 UTF-8 中文被损坏。
- **修复**：[`scripts/restore_app_chinese.py`](scripts/restore_app_chinese.py) 批量恢复文案；[`web/src/App.tsx`](web/src/App.tsx)。
- **验证**：`pnpm run build` 通过；刷新后应显示「返回」「刷新」「全流程执行」等正常中文。

### 2026-05-19 — 项目详情页：返回 + 项目名顶栏，去掉左侧历史栏

- **用户目标**：删除详情页红框内「漫剧流水线控制台」标题区与左侧「生成历史」；顶栏改为返回按钮 + 项目名称，返回回首页。
- **改动**：[`web/src/App.tsx`](web/src/App.tsx) 详情分支布局；[`RunHeader.tsx`](web/src/components/RunHeader.tsx) 去掉重复大标题（元信息保留）。
- **验证**：`web` 下 `pnpm run build` 通过。

### 2026-05-19 — 首页：我的项目页 + 最近项目单行预览

- **用户目标**：去掉首页「全部运行」列表；侧栏「新建」改「我的项目」并打开完整项目网格页；首页最近项目只保留一行；去掉「查看全部运行」。
- **改动**：[`MyProjectsPage.tsx`](web/src/components/MyProjectsPage.tsx)；[`FlovaRecentProjects.tsx`](web/src/components/FlovaRecentProjects.tsx) `variant=preview|full`；[`HomePage.tsx`](web/src/components/HomePage.tsx) 仅 preview；[`App.tsx`](web/src/App.tsx) `homeView` 切换；[`FlovaHomeSidebar.tsx`](web/src/components/FlovaHomeSidebar.tsx) 修复误写非法 `motion` 标签为 `div`。
- **验证**：`web` 下 `pnpm run build` 通过。

### 2026-05-20 — 首页按 designRules 优化 + 项目卡仅图+标题

- **依据**：[`docs/designRules`](docs/designRules)。
- **项目卡**：[`FlovaRecentProjects.tsx`](web/src/components/FlovaRecentProjects.tsx) 去掉 run_id、时间、「打开流水线」；上图下文；hover 上浮/缩放；回收站改为 hover 图标。
- **封面**：[`pipeline_runner.py`](server/pipeline_runner.py) `list_runs` 增加 `cover_image`（images 下首张图）。
- **全局**：环境光、`.flova-content-card`、区块标题、Composer 输入框样式；[`HomePage`](web/src/components/HomePage.tsx)、[`HotSkillsRow`](web/src/components/HotSkillsRow.tsx) 间距对齐规范。
- **验证**：`pnpm run build` 通过；需重启 API 后 `cover_image` 字段生效。

### 2026-05-19 — 修复 legacy 项目无法移入回收站

- **现象**：无 `pipeline_ui_state.json` 的旧项目点「回收站」失败。
- **原因**：`request_stop()` 强依赖 `load_state()`，legacy 目录无状态文件时直接 500。
- **修复**：[`server/pipeline_runner.py`](server/pipeline_runner.py) `request_stop` 无状态文件时仅设取消事件并返回。
- **清理**：已将 5 个 legacy 目录移入 `outputs/_trash/`（20260516_*）。

### 2026-05-19 — 首页创作框 Flova 式改版 + 设置齿轮

- **用户目标**：单框输入 + 框内底栏（风格/时长胶囊下拉）+ 右侧彩虹发送；去掉 +、「完成后发送」、高级并发；并发迁到右上角齿轮设置。
- **改动**：[`HomeComposer.tsx`](web/src/components/HomeComposer.tsx)；[`HomeSettingsDialog.tsx`](web/src/components/HomeSettingsDialog.tsx) + [`FlovaHomeTopBar.tsx`](web/src/components/FlovaHomeTopBar.tsx)。
- **验证**：`pnpm run build` 通过。

### 2026-05-19 — 首页热门预设：Seedream 4.5 缩略图 7 张

- **用户目标**：7 个热门预设各一张缩略图。
- **已完成**：`python scripts/seedream_batch_presets.py` 生成 7/7，落盘 `web/public/presets/{movie,brand,anime,gamecg,scifi,doc,mv}.png`；[`HotSkillsRow.tsx`](web/src/components/HotSkillsRow.tsx) 改为 `<img src="/presets/...">`。
- **验证**：批量脚本 exit 0；`pnpm run build` 通过；刷新首页「热门预设」应见真实配图。

### 2026-05-19 — Seedream 4.5：助手 / Web 即时生图能力

- **用户目标**：对话里能让助手用 Seedream 4.5 为网页占位图等生成资产。
- **改动**：[`steps/seedream_client.py`](steps/seedream_client.py)（默认 `doubao-seedream-4-5-251128`）；[`server/seedream_service.py`](server/seedream_service.py) + [`server/main.py`](server/main.py) `GET /api/seedream/status`、`POST /api/seedream/generate`、`GET /api/ui-assets/{filename}`；[`scripts/seedream_generate.py`](scripts/seedream_generate.py)；[`docs/seedream-assistant.md`](docs/seedream-assistant.md)；[`web/asset-prompts.json`](web/asset-prompts.json)；Step 5 改为共用 client（不再写死 5.0 模型）。
- **验证**：本机 `is_configured=True`；`web` `pnpm run build` 通过；需重启 uvicorn 后 API 生效。

### 2026-05-19 — 首页：左侧边栏固定、右侧内容区滚动

- **用户目标**：首页左侧导航始终贴在左边；顶栏固定，主内容在右侧区域内滚动。
- **改动**：[`web/src/App.tsx`](web/src/App.tsx) 首页分支 `flex h-dvh overflow-hidden` + `#home-main-scroll`（`overflow-y-auto`）；修复误写的无效 `motion` 标签为 `div`；[`FlovaHomeSidebar.tsx`](web/src/components/FlovaHomeSidebar.tsx) `h-full`；侧栏「提示」按钮改为在 `#home-main-scroll` 内平滑滚动。
- **验证**：`web` 下 `pnpm run build` 通过；浏览器刷新首页后：侧栏不随内容滚动，右侧可上下滚动，点「热门/项目/新建」仍定位到对应区块。

### 2026-05-19 — 修复首页中文显示为问号

- **现象**：首页创作区大量 `????`（`HomeComposer.tsx` 曾被错误编码保存）。
- **修复**：重写 [`web/src/components/HomeComposer.tsx`](web/src/components/HomeComposer.tsx) 为 UTF-8 中文文案。
- **验证**：`web` 下 `pnpm run build` 通过；刷新页面后应显示「创意描述」「风格」「时长」等正常中文。

### 2026-05-19 — Step 1：按风格类型加载独立 systemPrompt

- **用户目标**：7 种「风格类型」各有独立 systemPrompt，选中即加载；取消自定义风格。
- **后端**：[`prompts/step_01/_base.txt`](prompts/step_01/_base.txt) + [`prompts/step_01/styles/*.txt`](prompts/step_01/styles)；[`steps/step_01_research.py`](steps/step_01_research.py) `load_step01_system_prompt` / `validate_style`；[`server/main.py`](server/main.py) 创建 run 时校验；旧别名 `广告片`→`品牌广告` 等。
- **前端**：[`web/src/lib/run-presets.ts`](web/src/lib/run-presets.ts) 7 项；[`HomeComposer`](web/src/components/HomeComposer.tsx) 去掉自定义；[`HotSkillsRow`](web/src/components/HotSkillsRow.tsx) 7 张卡。
- **验证**：`python -m unittest tests.test_step_01_research tests.test_step_02_script`；`web` `pnpm run build` 通过。

### 2026-05-19 — Web：产物/运行日志增加 Markdown 展示

- **用户目标**：产物与日志预览支持 Markdown 渲染。
- **改动**：[`web/src/components/TextContentViewer.tsx`](web/src/components/TextContentViewer.tsx)（`react-markdown` + `remark-gfm`）；[`StepPipelineCard.tsx`](web/src/components/StepPipelineCard.tsx) 接入；[`index.css`](web/src/index.css) `.markdown-body` 样式。
- **交互**：Step2 `script.md` 默认 **Markdown**  tab；JSON 产物可切 **JSON 格式化**；运行日志可切 Markdown/原文。
- **验证**：`web` 下 `pnpm run build` 通过。

### 2026-05-19 — 分析：上次运行只出 1 个分镜（run `20260519_115426_b3a0`）

- **用户问题**：为什么流水线只输出了一个分镜。
- **结论**：`script.md` 里 **模型写了 6 条分镜**（`## 分镜 1｜10 秒｜` … `分镜 6`），但 [`steps/script_split.py`](steps/script_split.py) 解析器只认 **行首直接是 `分镜 N｜`**，不认 `## ` 前缀；后备正则的下一条边界也不匹配 `## 分镜 2`，整篇被当成 **1 块**。故 `script_data.json` 里 `"shots": 1`，Step 6/7 只生成 `shot_01`。
- **日志**：`logs/step_2.log` 有「解析出 1 个有效分镜块，2 幕」；`logs/step_6.log` 仅 `shot_01 [10s]`。
- **已做（方案 2）**：[`prompts/step_02_script_system.txt`](prompts/step_02_script_system.txt) 增加「机器解析硬约束」，禁止 `#`/`##` 包裹分镜标题与 T2V/I2V 小节。
- **待办**：重跑 Step 2 或整条流水线验证 `shots` 是否等于模型写的条数。

### 2026-05-18 — Step 4：DeepSeek 从 Step 1 清单生成人物/场景/道具

- **用户目标**：Step 4 用 DeepSeek 生成资产，主要依据 Step 1「人物与场景清单」，输出人物、道具、场景。
- **改动**：[`prompts/step_04_extract_assets_system.txt`](prompts/step_04_extract_assets_system.txt)；[`steps/step_04_prompts_img.py`](steps/step_04_prompts_img.py) 先调模型出 JSON 清单并写 `assets.json`，再逐条生成定妆 prompt；Step 4 前置改为仅需 Step 2（[`server/pipeline_runner.py`](server/pipeline_runner.py)）。
- **验证**：模块 import 通过；需有 `DEEPSEEK_API_KEY` 跑端到端 Step 4。

### 2026-05-18 — Web：停止步骤 + 首页回收站

- **用户目标**：运行中可点按钮停止；首页项目卡右上角「回收站」移除项目且历史不再显示。
- **后端**：[`server/pipeline_runner.py`](server/pipeline_runner.py) `request_stop` / `delete_run`（协作式取消 + 移至 `outputs/_trash`）；[`server/main.py`](server/main.py) `POST /api/runs/{id}/stop`、`DELETE /api/runs/{id}`，`api_revision` 8。
- **前端**：[`web/src/lib/api.ts`](web/src/lib/api.ts)、[`FlovaRecentProjects.tsx`](web/src/components/FlovaRecentProjects.tsx)、[`App.tsx`](web/src/App.tsx)（停止执行 + 步骤卡「停止」）、[`StepPipelineCard.tsx`](web/src/components/StepPipelineCard.tsx)（`cancelled` 状态）。
- **验证**：`web` 下 `pnpm run build` 通过；需重启 uvicorn 后使用新 API。

### 2026-05-18 — Step 01～06：产出仅采信 LLM，Python 只做整理

- **用户目标**：每一步 step01～06 的输出都是 LLM 直接输出，py 只整理。
- **改动**：[`steps/step_output_policy.py`](steps/step_output_policy.py)；[`step_02_script.py`](steps/step_02_script.py) 去 `_fallback_script`、`script.md` 无本地标题；[`step_04_prompts_img.py`](steps/step_04_prompts_img.py) 去本地三段式兜底；[`step_06_video_prompts.py`](steps/step_06_video_prompts.py) 去 `_build_narrative`/`_infer_style`；[`pipeline_runner.py`](server/pipeline_runner.py)、[`pipeline.py`](pipeline.py) 写 `script.md` 不再加 `# 主题` 前缀；[`tests/test_step_02_script.py`](tests/test_step_02_script.py)。
- **说明**：Step 3 仍为从 Step2 正文解析 `@`（不调用模型）；Step 5 为生图 API，prompt 来自 Step4 模型正文。
- **验证**：`python -m unittest tests.test_step_01_research tests.test_step_02_script` 通过。

### 2026-05-18 — 提示词：Step 01 / 02 系统提示词对齐（方案 A）

- **用户目标**：按可行性说明先改 Step 1 与 Step 2：Step1 剧本+清单，Step2 唯一正式分镜。
- **改动**：[`prompts/step_01_research_system.txt`](prompts/step_01_research_system.txt)（去掉外围 md 围栏、删除逐镜 SCENE/时间码，改为场次纲要 + 必含 `## 【人物与场景清单】`）；[`prompts/step_02_script_system.txt`](prompts/step_02_script_system.txt)（分工说明、I2V 画面/音频两层、时长与包装符、`@` 与 Step 6 收口）。
- **验证**：未跑端到端流水线；建议跑一次 1→2→4 核对清单抽取。

### 2026-05-18 — 提示词：Step 01～06 与 promptGuild 对齐（可行性文档）

- **用户目标**：按 `docs/promptGuild` 审查 step_01/02/04/06 系统提示词，找出可统一字段与可改进描述；**先出方案、不改文件**；职责：Step1 剧本、Step2 分镜、Step4 资产、Step6 图生视频润色。
- **产出**：[`docs/prompt-alignment-feasibility.md`](docs/prompt-alignment-feasibility.md)（Guild 与流水线术语映射、公共契约建议、P0 Step1「双分镜/入库铁律」冲突与方案 A/B、分步 P1/P2、落地顺序）。
- **验证**：仅文档评审，未跑流水线。

- **用户目标**：修复 `localhost:5174` 访问 `127.0.0.1:8765` 时浏览器报 CORS / `ERR_FAILED`。
- **改动**：[`server/main.py`](server/main.py) 增加 `5174/5175` 白名单、`allow_origin_regex` 含 `[::1]`、`allow_credentials=False`（与当前无 Cookie 的 fetch 一致）；`api_revision` → 7。
- **验证**：需在本机 **重启** `uvicorn` 后刷新前端；若仍 404，确认 API 与 `outputs/` 为同一仓库根目录启动。

### 2026-05-18 — 整理 `docs/promptGuild`

- **用户目标**：统一文档格式与层级结构。
- **改动**：[`docs/promptGuild`](docs/promptGuild) 改为标准 Markdown（一级标题、章节编号、列表与分段）；修正媒体生成小节笔误「定。)」；图像小节补一句与「中文环境用中文」的优先级说明（原文中英并存）。

### 2026-05-18 — Step 1：落盘仅用 LLM 正文

- **用户目标**：Step 1 与 Step 6 一致，`research.json` 中正文只采信模型输出。
- **改动**：[`steps/step_01_research.py`](steps/step_01_research.py) 去掉 8000 字截断与本地拼装的 `summary`、去掉 API 失败时的占位纲要；`findings[].content` 与 `creative_brief` 同源；[`prompts/step_01_research_system.txt`](prompts/step_01_research_system.txt) 末增加 **Output Constraint**（禁止套话/Markdown 围栏包裹等）。

### 2026-05-18 — Step 6：`prompt` 仅用模型正文，去掉本地前缀

- **用户目标**：Step 6 入库的 `prompt` 与此前一样只采信 LLM 润色结果，不再拼接本地「风格/场景/分镜+duration-ms」前缀（时长仍用字段 `duration_ms`）。
- **改动**：[`steps/step_06_video_prompts.py`](steps/step_06_video_prompts.py)：`final_prompt` 仅为润色正文或（润色无效时）I2V 原文或无 I2V 时的叙事回退；移除 `_build_location_desc` / `_extract_scene_details` 死代码。

### 2026-05-18 — 首页创意输入框底色与页面背景一致

- **用户目标**：大输入区内层（textarea）不要灰块，改为与整页背景同色。
- **改动**：[`HomeComposer`](web/src/components/HomeComposer.tsx) 文本域由半透明 `bg-background/35` 改为实心 `bg-background`（与 `--background` 令牌一致）。

### 2026-05-18 — 首页主标语改为一句问候

- **用户目标**：首页标题区由长 Slogan 改为「导演，今天有什么新创意？」。
- **改动**：[`web/src/components/HomePage.tsx`](web/src/components/HomePage.tsx) 去掉副标题段落，仅保留该句为 `h1`。

### 2026-05-18 — 首页 Flova 式布局（仅此页；详情页保持原样）

- **用户目标**：仅首页在布局、配色、圆角、侧栏、大输入区、横向卡片、项目网格上尽量接近 Flova。
- **实现**：`App.tsx` 在 `!selected` 时切换为左窄条 [`FlovaHomeSidebar`](web/src/components/FlovaHomeSidebar.tsx) + [`FlovaHomeTopBar`](web/src/components/FlovaHomeTopBar.tsx) + 可滚动主区；[`HomePage`](web/src/components/HomePage.tsx) 增加 Flova 风主标题/副标题、[`HotSkillsRow`](web/src/components/HotSkillsRow.tsx) 横向预设卡、[`FlovaRecentProjects`](web/src/components/FlovaRecentProjects.tsx) 最近项目网格（无成片用渐变占位）+「查看全部运行」锚点列表；[`HomeComposer`](web/src/components/HomeComposer.tsx) 玻璃壳、占位「由一个想法或故事开始…」、`+` 展开高级；[`index.css`](web/src/index.css) 增加 `.glass-flova`、画布略加深。选中运行后仍为顶栏 + 宽 [`RunSidebar`](web/src/components/RunSidebar.tsx) + 步骤控制台。
- **验证**：`web` 下 `pnpm run build` 通过。

### 2026-05-18 — Web：按 Flova 参考规范改造主视觉与首页创作区

- **用户目标**：用 [`docs/design-spec-flova-reference.md`](docs/design-spec-flova-reference.md) 指导项目界面改造。
- **已完成**：暗色画布加近黑、卡片面与字色层级、顶部弱双氛围光（偏暖+偏冷）；[`HomeComposer`](web/src/components/HomeComposer.tsx) 大圆角输入壳、引导型占位、底部工具行胶囊下拉 + 圆形青绿渐变发送；[`native-select`](web/src/components/ui/native-select.tsx) 增加 `nativeSelectPillClass`；[`RunSidebar`](web/src/components/RunSidebar.tsx) 去掉标题下划线、历史选中改为浅表面块高亮。
- **验证**：`web` 下 `pnpm run build` 通过。

### 2026-05-18 — Flova 参考截图 → 设计规范 MD

- **用户目标**：分析提供的 Flova.ai 风格截图，输出可保存的设计规范文档。
- **产出**：[`docs/design-spec-flova-reference.md`](docs/design-spec-flova-reference.md)（布局、色板估算、输入区/卡片/pill、与「无边框+浅灰线」原则对齐及落地清单）。
- **说明**：文档为界面归纳，非官方稿；色号供对照，精确值建议浏览器取色。

### 2026-05-18 — 新主页布局（草稿对齐）

- **用户目标**：左侧生成历史；首页问候 + 大输入框；风格/时长 **下拉框**；「开始」创建运行；**历史成片**置于首页「我的项目」区块。
- **新增/改动**：[`web/src/components/HomePage.tsx`](web/src/components/HomePage.tsx)、[`HomeComposer.tsx`](web/src/components/HomeComposer.tsx)、[`ui/native-select.tsx`](web/src/components/ui/native-select.tsx)、[`lib/run-presets.ts`](web/src/lib/run-presets.ts)；[`App.tsx`](web/src/App.tsx) 取消「成片 / 新建」双面板切换，未选中运行时固定渲染 HomePage；[`FinishedClipsGrid.tsx`](web/src/components/FinishedClipsGrid.tsx) 支持标题覆盖、`headingDescription=null`、`showNewProjectTile`；[`RunSidebar.tsx`](web/src/components/RunSidebar.tsx) 弱化新建入口（ghost「新建一条」+ 滚动至 `#home-composer`）；[`NewRunForm.tsx`](web/src/components/NewRunForm.tsx) 预设来源改为 `run-presets`。
- **验证**：`pnpm run build`（`web`）通过。

### 2026-05-18 — Web：浅灰分割线 + 去掉卡片/按钮线框

- **用户目标**：截图反馈细线改浅灰；卡片与按钮取消明显描边。
- **实现**：[`web/src/index.css`](web/src/index.css) 新增 **`.border-line-soft`** / **`.mp-scrollbar`**；顶栏、[RunSidebar](web/src/components/RunSidebar.tsx)、[RunHeader](web/src/components/RunHeader.tsx)、[StepPipelineCard](web/src/components/StepPipelineCard.tsx)、[FinishedClipsGrid](web/src/components/FinishedClipsGrid.tsx) 分割线改用该类；[**Card**](web/src/components/ui/card.tsx) 默认 **无边框无阴影**；[**Button**](web/src/components/ui/button.tsx) 的 **outline / cta / cool** 去描边；[**Input**](web/src/components/ui/input.tsx) 无底框、[PipelineProgress](web/src/components/PipelineProgress.tsx) 步骤按钮去 **ring**、[dialog](web/src/components/ui/dialog.tsx) 内容区无边框；提示/错误横幅去彩色描边、靠底色区分。
- **验证**：`pnpm run build`（`web`）通过。
- **文档**：[`docs/web-console-design-tokens.md`](docs/web-console-design-tokens.md) 增加「分割线」小段。

### 2026-05-18 — hue 取舍：令牌修复 + Button 变体 + 设计速查文档

- **用户想做什么**：`/hue` 语境下重做前端视觉；选型：先做产物界面改版，附简短令牌说明。
- **已完成**：
  - [`web/tailwind.config.js`](web/tailwind.config.js)：语义色从 `hsl(var(--token))` 改为 `var(--token)`（与 `:root`/`.dark` 中 **oklch** 对齐）；补全 **`accent-warm` / `-foreground` / `accent-cool` / `-foreground`**，消除 `ring-accent-cool`、`text-accent-cool` 等无效类。
  - [`web/src/components/ui/button.tsx`](web/src/components/ui/button.tsx)：补 **`cta` / `cool`**；`link` 改为 **`text-accent-cool`**。
  - [`docs/web-console-design-tokens.md`](docs/web-console-design-tokens.md)：PM 友好的一页设计语言与 Tailwind 注意点。
- **验证**：`web` 下 `pnpm run build` 通过。
- **备注**：完整 hue Phase 7–13（独立 `preview.html`/SKILL 包）未在本次生成；可按同一 `design-model` 思路以后再补。

### 2026-05-18 — Step 6：`sqlite3.connect` 收到 Connection 而非路径

- **原因**：[`server/pipeline_runner.py`](server/pipeline_runner.py) 调用 `steps.step_06_video_prompts.run` 时第三个参数误传 **`conn`**，而 [`steps/step_06_video_prompts.py`](steps/step_06_video_prompts.py) 的签名是 **`db_path: str`**，内部会自己对路径 `sqlite3.connect(db_path)`。
- **修复**：Step 6 改为 `s6(script_data, img_results, db_path, d_out)`，不再在此处 `connect`/`close`（Step 6 内部按分镜建连写库）。
- **验证**：静态核对调用与 `run(...)` docstring；未跑端到端 UI。

### 2026-05-18 — `web`：`pnpm run dev` 找不到 vite / plugin-react

- **原因**：未在 `web` 目录执行完整 `pnpm install`，`node_modules` 里没有开发依赖（含 `vite`、`@vitejs/plugin-react`）。
- **处理**：在 `web` 下执行 `pnpm install`；若遇 `ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY`，先设 `$env:CI='true'` 再安装。
- **验证**：本机 `pnpm install` 退出码 0；`pnpm run dev` 可进入 Vite。
- **改动文件**：无（仅依赖安装）。

### 2026-05-17 — Step 1 User Prompt 仅透传三字段

- `steps/step_01_research.py`：`user_prompt` 只含 **主题、风格类型、时长（秒）**；不写长模版（由系统提示词负责）。

### 2026-05-17 — Step 4 仅以 Step 1「人物场景清单」为权威

- **用户反馈**：多分镜投喂导致多套主角定妆、人设不一致。
- **实现**：`_extract_step1_inventory_block`、`run(..., research=)`，`pipeline_runner`/`pipeline.py` 传入 **`research.json`**；指令层明确 **禁止引用分镜正文**；恢复 **`_dedupe_merge_asset_rows`**。

### 2026-05-16 — Step 04：整部剧本文送进大模型（已废止）

- 已由上条替换为「仅用 Step 1 清单」口径。

### 2026-05-16 — 同名资产合并（已落地于 Step 4）

- **说明**：`_dedupe_merge_asset_rows` 按 **(tag + 规范化名称)** 合并；`prompt_map.assets` 可为 `refs_from_script`。

### 2026-05-16 — Step 03 DeepSeek 资产提取

- **用户目标**：第 3 步与前面步骤一致调用 DeepSeek；**系统提示词**使用 `prompts/step_04_img_single_system.txt`。
- **实现**：`steps/step_03_extract_assets.py` 加载 `STEP03_EXTRACT_ASSETS_SYSTEM_PROMPT_FILE`（未设则默认上述模板），用户模板要求**仅输出 JSON**（角色/场景/道具 + refs + description），与上游「单行文生图」铁律在用户侧明确覆盖解析；调用 `deepseek_chat`（低温、较大 max_tokens）。
- **回退**：无 Key、超时、非 JSON、或三类均为空 → 沿用原正则 + `_classify_tag` **启发式**提取，流水线接口不变。
- **验证**：本机未跑端到端流水线（可选：有 `DEEPSEEK_API_KEY` 时跑一次 Step 3）。

### 2026-05-16（续）— 暗色下正文「看不见」修复

- **原因**：`tailwind.config.js` 里颜色写成 **`hsl(var(--foreground))`**，而 `index.css` 里 `--foreground` 已是完整 **`oklch(...)`**，拼成非法的 `hsl(oklch(...))`，浏览器忽略后字色退回默认黑。
- **修复**：语义色改为 **`var(--background)` / `var(--foreground)`** 等；**`destructive-foreground`** 仍为「H S% L%」分量，保留 **`hsl(var(--destructive-foreground))`**。
- **`index.css`**：去掉全局 `* { outline-ring/50 }`（`ring` 改用 `var()` 后 Tailwind 无法生成该类），焦点环仍由各组件的 `focus-visible:ring-*` 负责。
- **是否需要重启**：一般 **刷新页面**即可；改的是构建配置与 CSS，不需「重启电脑」。

### 2026-05-16（续 4）— 去掉白线框、容器参考图 2/3（surface 块）

- **目标**：去掉高对比「白描边」，用大面积极弱分割 + **略浅表面色**（`--card` / `muted`）区分容器，对齐参考里的深灰底块、无硬边框。
- **index.css**：画布 `--background` 略深；`--card` 略抬；`--border` 改为 **低透明灰线**（只留给必要分割）；`--input` 同步减弱。
- **`Card`**：默认 `border-0 shadow-none`。
- **页面**：`App` 顶栏与流水线横条、侧栏、成片网格、步骤卡、进度条、RunHeader、NewRunForm 等去掉/弱化 `border-*`，改用 `bg-card` / `bg-muted/xx`；侧栏历史行改为 **无底框**、选中仅用浅底；`button` 线框按钮在暗色下 `dark:border-white/10`。

### 2026-05-16（续 3）— 标题/说明仍为黑、统一浅灰字

- **原因**：① `.dark` 未在根上写 `color`，部分子树未用 `text-*` 时走浏览器默认近黑；② **`<button>` 自带系统字色**（不继承父级），侧栏历史等原生按钮内标题呈黑；③ 设计调整为**主字/标题浅灰**（`--foreground`）、**说明字**略淡（`--muted-foreground`）。
- **修复**：`index.css` 中 `.dark` 增加 `color-scheme` + `color: var(--foreground)`；`#root` 与 `h1–h6` 显式浅色；令牌 `--foreground` / `--card-foreground` 调为 `oklch(0.88…)`，`--muted-foreground` 为 `oklch(0.72…)`；`App` 根布局加 `text-foreground`；`RunSidebar` / `FinishedClipsGrid` / `RunHeader` 等按钮补 **`text-card-foreground` / `text-foreground`**。

### 2026-05-16（续 2）— `text-primary` 与深色按钮色冲突

- **原因**：暗色里 **`--primary`** 故意设为**深灰**（给默认实心按钮铺底），但 **`text-primary` 类也读同一个变量**，成片卡片「打开流水线详情」、成片路径、表单 chip 选中态等仍写 `text-primary` 时，会学成**深灰字贴深底**。
- **修复**：链接/类链接改用 **`text-accent-cool`**；正文路径用 **`text-foreground`**；`button` 的 **`link`** variant 改为 `text-accent-cool`；`NewRunForm` 风格 chip 选中态用 **`accent-cool` 边框+浅底+浅字**；`RunSidebar` 选中行改用 **`accent-cool`** 描边。`CardTitle` / `Label` 默认补 **`text-card-foreground` / `text-foreground`**。`--muted-foreground` 改为更**中性灰**（减轻整页说明字发蓝）。涉及文件：`FinishedClipsGrid.tsx`、`RunHeader.tsx`、`NewRunForm.tsx`、`RunSidebar.tsx`、`button.tsx`、`card.tsx`、`label.tsx`、`index.css`、`StepPipelineCard.tsx`。

### 2026-05-16 — Web 暗色 UI 落地

- **用户目标**：在「漫剧流水线控制台」上落地深色画布、浅灰卡片、暖色主 CTA、信息态冷色点缀。
- **已完成**：
  - `web/index.html`：`<html class="dark">` 默认暗色工作台。
  - `web/src/index.css`：`.dark` 调色贴近 canvas/surface/border；**文字**：`--foreground`（主文）、`--card-foreground` 等与规范主字色对齐，`--muted-foreground` 对齐次级说明字色；新增 `--accent-warm` / `--accent-cool`；中性 `--primary` 实心按钮；`.dark .bg-app-gradient` 改为冷色微光。
  - `web/tailwind.config.js`：`accent-warm` / `accent-cool` 颜色键。
  - `web/src/components/ui/button.tsx`：新增 `cta`（暖）、`cool`（蓝）。
  - `App.tsx`：侧栏列宽 `280–320px`；API 地址用 `text-accent-cool`；「一键执行全部步骤」→ `variant="cta"`。
  - `RunSidebar` / `NewRunForm`：主入口「新建动画」「创建运行」→ `cta`。
  - `StepPipelineCard`：「执行」→ `cool`。
  - `PipelineProgress`：当前步骤高亮环 → `ring-accent-cool`。
  - `input.tsx`：暗色下 `dark:bg-muted/80`。
- **验证**：`pnpm run build`（`web`）通过。
- **待办 / 风险**：控制台仍以暗色为默认；若日后要亮色开关，需同步 `:root` 与主题切换逻辑。`lightningcss` 构建时对 `@theme` 等有警告，属依赖链已知现象，不影响当前构建成功。

### 更早（归档摘要）

- API / 成片：`GET /api/runs` 与 `final_mp4`、Step 6 分镜 `script_split`、Seedance `SEEDANCE_PRIVACY_FALLBACK` 等见历史提交与对话；详情可搜代码与 `docs/`。
