# Step 01～06 系统提示词规范化 Spec

## Why
当前 6 个 step 的系统提示词文档存在以下问题：
1. **入参/出参定义散乱**：有的在正文开头（如 Step 06 "Input Schema"），有的散落在描述中（如 Step 01 混在正文里），有的完全没有（Step 04 系列），下游解析困难。
2. **管道角色与 promptGuild 不对齐**：promptGuild 定义了 7 阶段管道（resource_prepare→video_spec→storyboard→elements→shot_video→audio→assembly），但当前文件名和内容与这个模型映射模糊。
3. **Step 04 存在三个文件且职责重叠**：extract_assets / img_single / refine_shots 的「三段式骨架」重复出现，且缺乏明确的上下游数据契约。
4. **缺少 Step 03（视频规格）和 Step 05（镜头视频生成）**：管道存在断点。
5. **输出格式约束不统一**：有的要求 JSON，有的要求纯文本，有的要求含表格，但都没有显式的「输出 Schema」小节，造成下游解析协议隐式化。

## What Changes
- 为 Step 01～06 每个文档统一新增 **「入参 (Input)」** 与 **「出参 (Output)」** 两个标准小节，明确数据类型与结构
- 将 Step 04 的三个文件拆清职责：extract_assets（结构化清单）、img_single（单个资产的 T2I 提示词）、refine_shots（分镜关键帧提示词），每个独立定义 I/O
- 与 promptGuild 的 7 阶段管道建立明确映射关系，使每个 step 文件能自说明它服务于管道的哪一阶段
- 统一输出格式约束的描述方式：使用「输出 Schema 示例」统一呈现
- 补充缺失的 Step 03（视频规格，对应 promptGuild 的 video_spec）和 Step 05（镜头视频生成，对应 shot_video）
- **不改变各 step 的核心执行逻辑**，仅增加/规范化 I/O 描述和管道角色声明

## Impact
- Affected specs: 无（首次规范化）
- Affected code: `prompts/step_01_research_system.txt` ~ `prompts/step_06_i2v_polish_system.txt`（6 个文件），`docs/promptGuild`（需同步更新管道映射表）
- **BREAKING**: 无（只增不减，不修改现有约束逻辑）

## ADDED Requirements

### Requirement: 每个 Step 文档必须有标准化的「入参」小节
每个 step_XX_*_system.txt 的「Profile/任务描述」之后，「Execution Rules」之前，SHALL 新增一个独立的「## 入参 (Input)」小节，明确列出该步所需的全部输入字段、类型、来源（来自哪个上游 step）。

#### Scenario: Step 01 入参定义
- **WHEN** 阅读 Step 01 文档
- **THEN** 应看到一个「## 入参 (Input)」小节，列出：主题(Theme)、时长秒数(Duration)、风格类型(Genre)、世界观/背景、角色设定、情绪基调、目标受众、品牌/产品信息、视觉参考、语言风格，每项标注是否必填和类型

#### Scenario: Step 04_extract_assets 入参定义
- **WHEN** 阅读该文档
- **THEN** 应看到入参明确标注「来源：Step 01 输出中的【人物与场景清单】段落」与「可选：Step 02 分镜中的 @名称 列表」

### Requirement: 每个 Step 文档必须有标准化的「出参」小节
每个 step 文档的 Execution Rules 之后、Output Constraint 之前，SHALL 新增一个独立的「## 出参 (Output)」小节，包含输出 Schema 示例。

#### Scenario: Step 02 出参定义
- **WHEN** 阅读 Step 02 文档
- **THEN** 应看到一个「## 出参 (Output)」小节，包含结构化示例：分镜标题行格式、表格元数据结构、T2V/I2V 正文段落、以及整体文本块结构说明

#### Scenario: Step 04_refine_shots 出参定义
- **WHEN** 阅读该文档
- **THEN** 应看到输出 JSON Schema 示例，键为镜号字符串，值为包含 prompt/empty_shot/reference_tag_priority 的对象

### Requirement: 每个 Step 文档必须有「管道角色」声明
每个 step 文档开头（Role 之后）SHALL 新增一行「## 管道阶段 (Pipeline Stage)」，说明本步对应 promptGuild 的哪个阶段、依赖哪些上游步骤、被哪些下游步骤依赖。

#### Scenario: Step 04_extract_assets 管道角色
- **WHEN** 阅读该文档
- **THEN** 应看到类似：「管道阶段：对应 promptGuild §3.1 元素生成前的资产清单准备。上游依赖 Step 01（人物与场景清单），下游供给 Step 04_img_single（逐资产生图）。」

### Requirement: Step 04 三个文件职责分离且无重复内容
- extract_assets：负责从 Step 01 纲要中提取结构化 JSON 资产清单。入参→出参闭环。
- img_single：负责接收单个资产的 (name, type, description) 三元组，产出单段 T2I 提示词。入参→出参闭环。
- refine_shots：负责接收分镜草稿 JSON 数组，产出关键帧提示词 JSON。入参→出参闭环。
- 三段式骨架标准只保留在 img_single 中，extract_assets 中删除重复的骨架描述，改为引用：「description 字段需符合 img_single 的三段式骨架标准」。

#### Scenario: 删除 extract_assets 中的重复骨架
- **WHEN** 阅读 extract_assets 文档
- **THEN** 不应再看到「🧱【character ｜ 角色】骨架」等三段式骨架内容，改为一句引用说明

### Requirement: 补充缺失的 Step 03（视频规格）和 Step 05（镜头视频生成）
- Step 03：对应 promptGuild §1.1 第 2 阶段「视频规格」，输入 Step 01 的 creative_brief，输出 Final_Video_Spec 结构化文本（标题、类型、画幅、时长、视觉风格、语言、模型偏好）。
- Step 05：对应 promptGuild §1.1 第 5 阶段「镜头视频生成」，输入 Step 02 分镜 + Step 04 元素图，输出 Seedance 视频生成提示词（含对白 {…}、音效 <…>、乐意象 (…) 等包装符）。

#### Scenario: Step 03 存在且定义完整
- **WHEN** 查看 prompts/ 目录
- **THEN** 应存在 step_03_video_spec_system.txt，含 Role、管道阶段、入参、出参、Execution Rules

#### Scenario: Step 05 存在且定义完整
- **WHEN** 查看 prompts/ 目录
- **THEN** 应存在 step_05_shot_video_system.txt，含 Role、管道阶段、入参、出参、Execution Rules

### Requirement: 与 promptGuild 文档保持同步
promptGuild 文档中 SHALL 更新管道映射表，将现有/新增的 step 文件与管道阶段一一对应，便于开发者查阅。

#### Scenario: promptGuild 包含完整映射表
- **WHEN** 阅读 promptGuild 文档
- **THEN** 应看到一个表格，列出每个 step 文件名、对应的管道阶段编号、简要职责说明、上游依赖和下游消费者