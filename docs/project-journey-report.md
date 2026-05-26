# 漫剧流水线（manga-pipeline）项目历程报告

> **文档目的**：记录本项目从想法到可用的完整历程，沉淀「做 AI 视频流水线工具」的经验，供下次同类项目查阅。  
> **读者**：产品经理、应用工程师、提示词工程师  
> **最后更新**：2026-05-19  
> **关联文档**：[`README.md`](../README.md)、[`handoff-log.md`](../handoff-log.md)、[`docs/designRules`](designRules)、[`docs/prompt-alignment-feasibility.md`](prompt-alignment-feasibility.md)

---

## 一、项目是怎么诞生的

### 1.1 背景

传统「从创意到成片」的路径大致是：

```
写剧本 → 分镜 → 定妆/场景图 → 逐镜拍/生成 → 剪辑拼接
```

每一步都要换工具、换格式、人工搬运中间结果。AI 生图（Seedream）、图生视频（Seedance 2.0）、大模型写剧本（DeepSeek）成熟后，**技术上已经能串成一条链**，但缺少一个：

- **可重复跑**的流水线（Pipeline：按步骤自动执行的程序）
- **可断点续跑**的状态管理（某步失败不用从头来）
- **非工程师也能用**的控制台（Web 界面）

**manga-pipeline（漫剧流水线）** 就是为这个缺口而生的：用户输入一句创意 + 风格 + 时长，系统自动走完 8 步，最终在 `outputs/<run_id>/videos/final.mp4` 产出成片。

### 1.2 产品定位（一句话）

> **「导演工作台」**：一句话创意 → 8 步 AI 流水线 → MP4，全程可在浏览器里看进度、看产物、看日志。

参考了 Flova.ai 等创作工具的交互气质（暗色、大输入框、预设卡片），但核心能力是**自研 Python 流水线 + 火山引擎 API**，不是纯 UI 壳。

### 1.3 演进阶段（时间线摘要）

| 阶段 | 时间（约） | 重点 |
|------|-----------|------|
| **MVP 流水线** | 2026-05-16 前后 | CLI `pipeline.py`、8 步 steps、DeepSeek + Seedream + Seedance + ffmpeg |
| **Web 控制台 v1** | 2026-05-16～17 | FastAPI 后端、React 控制台、步骤卡 + 侧栏历史 |
| **提示词工程化** | 2026-05-18 | promptGuild 对齐、Step1/2 职责拆分、LLM 产出「只采信模型正文」 |
| **Flova 风 UI** | 2026-05-18～20 | 首页大输入框、暗色令牌、designRules、侧栏/项目卡改版 |
| **控制台重构** | 2026-05-19 | 进度链 + 单步产物、请求风暴修复、JSON→可读文档、Aurora 背景、打字机标题 |
| **体验抛光** | 2026-05-19 | 热门预设 TiltCard、代码清理、7 风格独立 Prompt |

---

## 二、解决了什么痛点

### 2.1 创作链路痛点

| 痛点 | 以前 | 本项目做法 |
|------|------|-----------|
| 步骤多、易丢上下文 | 手动复制粘贴各步结果 | 8 步统一落在 `outputs/<run_id>/`，JSON/Markdown/图片/视频结构化存储 |
| 角色脸在不同镜头不一致 | 每镜重新描述人物 | 分镜 `@图片N` 引用 Step5 同一张定妆图；Step4 以 Step1「人物与场景清单」为权威 |
| 提示词各写各的、格式漂移 | 无统一规范 | `prompts/` 分步 system prompt + `docs/promptGuild` + 可行性对齐文档 |
| 跑一半失败要重来 | 无状态 | `pipeline_ui_state.json` + SQLite `assets.db` + 每步 `logs/step_N.log` |
| 只有工程师能跑 | 命令行门槛高 | Web：创建项目、看进度链、预览产物、折叠日志 |

### 2.2 工程协作痛点

| 痛点 | 做法 |
|------|------|
| AI 改代码后中文变 `????` | `scripts/restore_app_chinese.py` + `check_ui_chinese.py` + Cursor 规则 |
| 多次 UI 改版留下死代码 | 删除 6 个旧组件 + 嵌套重复目录 `manga-pipeline/` |
| 新会话接手不知道做到哪 | `handoff-log.md` 交接摘要 + 本报告 |

---

## 三、实现了什么（功能清单）

### 3.1 后端流水线（Python）

**8 步流水线**（[`steps/`](../steps/) + [`pipeline.py`](../pipeline.py)）：

| Step | 名称 | 技术 | 产出 |
|------|------|------|------|
| 01 | 剧本纲要 | DeepSeek，按 7 种风格加载不同 system prompt | `research.json` |
| 02 | 分镜脚本 | DeepSeek，含 T2V/I2V 块、`@` 引用 | `script.md` |
| 03 | 资产提取 | 正则解析 Step2 的 `@`（不调模型） | `assets.json` |
| 04 | 生图提示词 | DeepSeek，依据 Step1 人物场景清单 | `prompt_map.json` |
| 05 | 文生图 | Seedream 4.5，可并发 | `images/`、`img_results.json` |
| 06 | 图生视频提示词 | DeepSeek I2V 润色 | `video_prompts.json` |
| 07 | 图生视频 | Seedance 2.0，可并发 | `videos/shot_*.mp4` |
| 08 | 拼接 | ffmpeg | `final.mp4` |

**控制面**（[`server/`](../server/)）：

- FastAPI：`/api/runs` 创建/列表/详情/停止/删除
- `pipeline_runner.py`：步骤调度、协作式取消、stdout 捕获写日志、状态 JSON
- Seedream 辅助 API：首页缩略图等 UI 资产即时生图

### 3.2 Web 控制台（React + Vite）

**首页**

- 问候标题 + **打字机轮播**（「有什么新想法/新剧本/广告案/新动画？」）
- **Aurora 动效背景**（低饱和、低透明度）
- **HomeComposer**：单框创意输入 + 风格/时长胶囊 + 渐变发送按钮
- **热门预设**：7 张 Seedream 缩略图 + 文字叠图 + **TiltCard 3D 倾斜**
- **最近项目**：封面图 + 标题，hover 回收站
- **悬停展开侧栏**（framer-motion）：首页 / 我的项目 / 设置（并发）

**项目详情页**

- 顶栏：返回 + 项目名
- **8 步进度链**（主题渐变圆点 + 虚线，点击切换步骤）
- **单步产物区**：只展示当前步骤的文本/图片/视频
- **JSON 默认转可读「文档」Tab**（非工程师友好）
- 底部 **运行日志** 默认折叠

### 3.3 提示词与规范资产

- `prompts/step_01/_base.txt` + `prompts/step_01/styles/*.txt`（7 风格）
- `docs/promptGuild`：产品级阶段与术语总则
- `docs/prompt-alignment-feasibility.md`：Step 职责边界与方案 A/B
- `docs/designRules` / `docs/design-spec-flova-reference.md`：UI 规范

---

## 四、技术栈一览

### 4.1 后端

| 类别 | 选型 | 说明 |
|------|------|------|
| 语言 | Python 3.10+ | 步骤脚本、API、CLI 统一 |
| Web 框架 | FastAPI + uvicorn | 本地 `8765` 端口 |
| 大模型 | DeepSeek API | 剧本、分镜、提示词 |
| 生图 | 火山 Seedream 4.5 | `doubao-seedream-4-5-251128` |
| 生视频 | 火山 Seedance 2.0 | 图生视频 |
| 存储 | 文件系统 + SQLite | 产物落盘；`assets.db` 记资产状态 |
| 视频处理 | ffmpeg | Step 8 concat |
| 配置 | `.env` + python-dotenv | API Key 不入库 |

### 4.2 前端

| 类别 | 选型 | 说明 |
|------|------|------|
| 框架 | React 19 + TypeScript | |
| 构建 | Vite 8 | `pnpm dev` / `pnpm build` |
| 样式 | Tailwind CSS 4 + oklch 设计令牌 | 暗色默认 |
| 组件 | shadcn 风格 ui/ | Button、Dialog、Card 等 |
| 动效 | framer-motion、CSS Aurora、TiltCard | 侧栏、背景、预设卡 |
| Markdown | react-markdown + remark-gfm | 产物/日志预览 |
| 字体 | Geist | 通过 @fontsource |

### 4.3 工程化

- `pytest` / `unittest`：Step1、Step2 等单测
- `handoff-log.md`：多轮 AI 协作交接
- `scripts/`：中文修复、Seedream 批量预设、生图 CLI

---

## 五、关键设计决策（为什么这样设计）

### 5.1 「LLM 产出只采信模型正文」

**问题**：Python 在模型输出外再拼标题、摘要、风格前缀，会导致：

- 入库内容与模型实际写的不一致
- Step6 视频 prompt 被本地前缀污染
- 调试时不知道问题在模型还是在代码

**决策**（[`steps/step_output_policy.py`](../steps/step_output_policy.py)）：Step 1～6 落盘内容以 LLM 返回为准，Python 只做解析、校验、格式化，**不做内容兜底拼接**（失败则明确报错，不用占位脚本糊弄）。

### 5.2 Step1 与 Step2 职责拆分（方案 A）

**问题**：Step1 曾要求输出「逐镜分镜」，与 Step2 重复；且格式与 Step2 的 `分镜 N｜X 秒｜` 不一致，下游解析混乱。

**决策**：

- **Step1**：场次纲要 + `## 【人物与场景清单】`（给 Step4 抽资产）
- **Step2**：**唯一正式分镜**，固定表格 + T2V/I2V
- **Step6**：收口 Seedance 负面约束（no music、no subtitles 等）

详见 [`docs/prompt-alignment-feasibility.md`](prompt-alignment-feasibility.md)。

### 5.3 Step4 只信 Step1 清单，不信整篇分镜

**问题**：把多分镜全文喂给 Step4，模型会为不同镜头生成多套主角定妆，**人设不一致**。

**决策**：Step4 以 Step1「人物与场景清单」为权威，指令层禁止引用分镜正文；同名资产合并 `_dedupe_merge_asset_rows`。

### 5.4 Web：单步展示 + 按需拉产物

**问题**：详情页一次渲染 8 步产物 + 轮询时批量请求 → 浏览器 `ERR_INSUFFICIENT_RESOURCES`、页面抖动。

**决策**：

- UI 只展示 `activeStep` 的产物
- 切换步骤时才请求该步 artifacts
- App 层 in-flight 去重 + silent 轮询

### 5.5 UI：面差分层，少描边

参考 Flova / Linear 系：**用背景明度差区分卡片**，不用高对比白线框。令牌见 `docs/designRules`、`web/src/index.css`。

---

## 六、踩过的坑（血泪经验）

### 6.1 提示词 vs 解析器：模型写了 6 镜，系统只认 1 镜

**现象**：`script.md` 里模型写了 `## 分镜 1｜10 秒｜` … `分镜 6`，但 `script_split.py` 只认**行首** `分镜 N｜`，不认 `## ` 前缀。

**结果**：`shots: 1`，Step6/7 只生成 `shot_01`。

**教训**：

1. **提示词里要写「机器解析硬约束」**（禁止 `#` 包裹分镜标题）
2. **解析器要宽容**或 **golden sample 单测**（一条真实 model 输出测解析条数）
3. 改 prompt 后必须 **重跑 Step2 看 shots 数量**

### 6.2 UTF-8 中文在 Windows 上反复变 `????`

**现象**：`App.tsx`、`HomeComposer.tsx` 多次出现问号。

**原因**：PowerShell / 部分编辑路径用非 UTF-8 写文件，中文损坏。

**对策**：

- 改完 `App.tsx` 跑 `python scripts/restore_app_chinese.py`
- CI 或提交前跑 `python scripts/check_ui_chinese.py`
- Cursor 规则：`.cursor/rules/web-utf8-chinese.mdc`

### 6.3 Tailwind 颜色 `hsl(var(--token))` + oklch 令牌

**现象**：暗色主题下文字「看不见」（实际是很深灰字在深底上）。

**原因**：`--foreground` 已是完整 `oklch(...)`，再包 `hsl()` 成非法 CSS，浏览器忽略。

**对策**：语义色改为 `var(--foreground)`；仅仍用 HSL 分量的保留 `hsl(var(...))`。

### 6.4 `--primary` 深色用于按钮底，却拿 `text-primary` 当链接色

**现象**：「打开流水线」等链接深灰不可读。

**对策**：链接/强调改用 `text-accent-cool`；按钮 variant 单独定义。

### 6.5 CORS：Vite 端口变化

**现象**：`localhost:5174` 访问 API 失败。

**对策**：`server/main.py` 白名单 + `allow_origin_regex` 含 `[::1]`；改端口后记得重启 uvicorn。

### 6.6 嵌套重复工程目录

**现象**：仓库里曾有一份 `manga-pipeline/manga-pipeline/` 旧代码副本，易误导编辑和 import。

**对策**：清理删除；`.gitignore` 管好 `outputs/`。

### 6.7 Legacy 项目无 `pipeline_ui_state.json`

**现象**：旧 run 点「回收站」500。

**对策**：`request_stop` / `delete_run` 对无状态文件做兼容；旧目录移入 `outputs/_trash/`。

### 6.8 AI 协作写 JSX 时误用 `<motion>` 标签

**现象**：构建失败或运行异常。

**对策**：framer-motion 必须用 `motion.div` 等，不能写裸 `<motion>`。

---

## 七、经验沉淀：下次做同类工具怎么做

### 7.1 开工前 checklist

- [ ] **画一张 8～N 步数据流图**：每步输入文件、输出文件、是否调 LLM、是否调外部 API
- [ ] **写清「谁负责分镜/谁负责资产/谁负责 I2V 润色」**，避免两步都写分镜
- [ ] **定一种机器可解析的分镜格式**，并写 3 条样例 + 单测
- [ ] **`.env.example` 列全 Key** + README 快速开始
- [ ] **outputs 目录结构** 第一天就定好，不要后期改路径

### 7.2 提示词工程

- [ ] 系统 prompt 放 `prompts/`，**一步一文件**，风格用 `_base + styles/` 组合
- [ ] 每步加 **Output Constraint**（禁止围栏、禁止开场白）
- [ ] 大改前先写 **可行性文档**（本项目即 `prompt-alignment-feasibility.md`）
- [ ] 模型输出与 Python 解析 **契约测试**：解析条数 = 模型声称条数

### 7.3 流水线运行时

- [ ] 每步写 `logs/step_N.log`，Web 可折叠展示
- [ ] 状态 JSON + 协作式 cancel（线程 Event）
- [ ] 生图/生视频 **并发可配置**（Web 设置 + CLI 参数）
- [ ] 删除 = 移入 `_trash`，防误删

### 7.4 Web 控制台

- [ ] **产品经理要能看懂产物**：JSON → 可读 Markdown（`json-to-markdown.ts`）
- [ ] **详情页不要一次拉全步骤产物**；轮询要 dedupe
- [ ] 暗色 UI：**oklch 令牌 + var()**，链接色与按钮底分离
- [ ] Windows 中文：**UTF-8 检查脚本** 进仓库
- [ ] 首页与详情页 **布局分支清晰**（`!selected` vs 选中 run）

### 7.5 与 AI 协作开发

- [ ] 维护 `handoff-log.md`（最近 5 条详细记录即可）
- [ ] 大改 UI 后 **删旧组件**，避免双轨并存
- [ ] 每次声称「完成」前 **`pnpm run build` / pytest**
- [ ] 给 AI **参考文档路径**（如 `@docs/designRules`）比口头描述省回合

### 7.6 推荐提问方式（给产品经理）

| 较差 | 较好 |
|------|------|
| 「优化一下首页」 | 「首页热门预设卡片缩小 20%，文字叠在图上，底部黑色渐变，去掉底框」 |
| 「修复 bug」 | 「详情页 Network 里 artifacts 请求刷屏，Console 报 ERR_INSUFFICIENT_RESOURCES」 |
| 「改提示词」 | 「Step2 是唯一正式分镜，Step1 不要逐镜；先出可行性文档再改文件」 |

---

## 八、当前状态与已知待办

### 8.1 已稳定可用

- CLI 全链路 + Web 创建/查看/停止/删除项目
- 7 风格预设 + 热门缩略图 + TiltCard
- 进度链单步产物 + JSON 文档视图
- 中文乱码修复脚本与规则

### 8.2 待验证 / 待增强

| 项 | 说明 |
|----|------|
| 分镜解析硬约束 | 改 Step2 prompt 后需重跑验证 `shots` 数量 |
| Step4/6 与 Guild 完全对齐 | 可行性文档中 04/06 仍标记待后续 |
| `output/` 旧 demo 目录 | 可手动删除，与 `outputs/` 无关 |
| 详情页执行按钮 | 部分 UI 改版后执行/停止入口需产品确认是否加回 |
| 像素级 Flova 一致 | 色值为估算，需浏览器取色微调 |

---

## 九、目录与文档索引（接手用）

```
manga-pipeline/
├── README.md                 # 安装、8 步说明、CLI
├── handoff-log.md            # 最近改动摘要（AI 交接）
├── docs/
│   ├── project-journey-report.md   # 本报告
│   ├── designRules                 # UI 规范
│   ├── promptGuild                 # 提示词总则
│   └── prompt-alignment-feasibility.md
├── pipeline.py               # CLI 入口
├── steps/                    # 8 步实现
├── prompts/                  # 各步 system prompt
├── server/                   # FastAPI + pipeline_runner
├── web/                      # React 控制台
├── scripts/                  # 工具脚本
├── outputs/                  # 运行产物（gitignore）
└── tests/                    # 单测
```

---

## 十、总结

**manga-pipeline** 不是单一脚本，而是 **「提示词体系 + 可断点流水线 + 导演向 Web 控制台」** 的组合。最大价值在于：

1. 把 AI 视频生产拆成 **可观测的 8 步**，每步产物可审可改；
2. 用 **Step 职责边界 + 清单式资产** 缓解一致性问题；
3. 用 **Flova 风 UI + 可读文档视图** 降低非工程师使用门槛。

最大成本在于：**提示词与解析器的契约**、**Windows UTF-8**、**Web 轮询与产物加载**——这三类问题在下一个同类项目里几乎必然再现，宜在第一天就按第七章 checklist 预埋。

---

*本报告根据 README、handoff-log、workUp、设计/提示词文档及 2026-05-16～05-19 开发记录整理。若架构有重大变更，请同步更新本章「演进阶段」与「待办」两节。*
