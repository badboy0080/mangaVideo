# prompts 文件引用清单

本清单用于说明 `prompts/` 目录下每个文件目前被哪里读取、影响流水线哪一步，以及是否属于旧文件。

## 加载规则

- 当前主流程优先通过 `prompts/pipeline_prompts.json` 注册提示词。
- 代码统一从 `steps/prompt_config.py` 读取注册表。
- 可用 `MANGA_PIPELINE_PROMPTS_CONFIG` 替换整份注册表。
- 可用 `MANGA_PROMPTS_DIR` 替换默认 `prompts/` 目录。
- 每个注册项还可以用对应的环境变量单独指定文件路径，例如 `STEP01_SCRIPT_SYSTEM_PROMPT_FILE`。

## 当前主流程引用

| 文件 | 注册 key / 读取位置 | 影响步骤 | 说明 |
|---|---|---|---|
| `pipeline_prompts.json` | `steps/prompt_config.py` 的 `load_pipeline_prompt_config()` | 全部 prompt 注册 | 中央注册表，决定各 Agent 默认读取哪个 prompt 文件。 |
| `step_01/_base.txt` | `step_01_script.system`；`steps/step_01_research.py` 的 `load_step01_system_prompt()` | Step01 剧本生成 | Step01 通用底座提示词，会和具体风格文件拼接。 |
| `step_01/styles/电影短片.txt` | `steps/step_01_research.py` 按风格名读取 | Step01 剧本生成 | 用户选择「电影短片」时拼接到 `_base.txt` 后。 |
| `step_01/styles/品牌广告.txt` | `steps/step_01_research.py` 按风格名读取 | Step01 剧本生成 | 用户选择「品牌广告」时拼接；旧别名「广告片」也会映射到它。 |
| `step_01/styles/动画叙事.txt` | `steps/step_01_research.py` 按风格名读取 | Step01 剧本生成 | 用户选择「动画叙事」时拼接；旧别名「动画」「动画短片」也会映射到它。 |
| `step_01/styles/游戏CG.txt` | `steps/step_01_research.py` 按风格名读取 | Step01 剧本生成 | 用户选择「游戏CG」时拼接。 |
| `step_01/styles/MV.txt` | `steps/step_01_research.py` 按风格名读取 | Step01 剧本生成 | 用户选择「MV」时拼接。 |
| `step_01/styles/科幻短片.txt` | `steps/step_01_research.py` 按风格名读取 | Step01 剧本生成 | 用户选择「科幻短片」时拼接。 |
| `step_01/styles/纪录片风格.txt` | `steps/step_01_research.py` 按风格名读取 | Step01 剧本生成 | 用户选择「纪录片风格」时拼接。 |
| `step_01_review/_base.txt` | `step_01_review.system`；`steps/step_01_review.py` 的 `load_review_system_prompt()` | Step01 剧本审核 | 审核 Agent 的系统提示词，只审剧本质量，不审固定字段。 |
| `step_01_review/rules.json` | `step_01_review.system`；`steps/step_01_review.py` 的 `load_review_rules()` | Step01 剧本审核 | 审核规则配置，和 `_base.txt` 一起送给审核 Agent。 |
| `step_02_script_system.txt` | `step_02_storyboard.system`；`steps/step_02_script.py` | Step02 分镜脚本 | 控制 DeepSeek 生成分镜脚本、T2V/I2V 段落、时长规则。 |
| `step_04_extract_assets_system.txt` | `step_02_asset_catalog.system`；`steps/step_04_prompts_img.py` | Step02 资产清单 | 当前主流程里仍由 Step02 门面调用，用于从 Step01 清单提取角色/场景/道具 JSON。文件名带 `step_04` 是历史命名。 |
| `step_04_img_single_system.txt` | `step_02_asset_image.system`；`steps/step_04_prompts_img.py` | Step02 资产生图 prompt | 当前主流程里仍由 Step02 门面调用，用于把单个角色/场景/道具写成定妆级文生图 prompt。文件名带 `step_04` 是历史命名。 |
| `step_06_i2v_polish_system.txt` | `step_04_video.system`；`steps/step_06_video_prompts.py` | Step04 视频 prompt 润色 | 当前主流程里由 Step04 视频生成前调用，用于润色每个分镜的 Seedance I2V prompt。文件名带 `step_06` 是历史命名。 |

## 旧脚本引用

这些文件不在当前 Web 控制台主流程里使用，主要被旧脚本 `scripts/demo_pipeline.py` 和 `scripts/run_pipeline.py` 读取。

| 文件 | 引用位置 | 当前状态 |
|---|---|---|
| `deepseek_script_system.txt` | `scripts/demo_pipeline.py`、`scripts/run_pipeline.py` 的 `load_prompt("deepseek_script_system")` | 旧版剧本生成 system prompt。当前主流程已改用 `step_01/_base.txt` + `step_01/styles/*.txt`。 |
| `deepseek_script_user.txt` | `scripts/demo_pipeline.py`、`scripts/run_pipeline.py` 的 `load_prompt("deepseek_script_user")` | 旧版剧本生成 user prompt 模板。当前主流程在 `steps/step_01_research.py` 内动态拼 user prompt。 |
| `asset_prompt_system.txt` | `scripts/demo_pipeline.py`、`scripts/run_pipeline.py` 的 `load_prompt("asset_prompt_system")` | 旧版资产提示词 system prompt。当前主流程已改用 `step_04_extract_assets_system.txt` 和 `step_04_img_single_system.txt`。 |
| `asset_prompt_user.txt` | `scripts/demo_pipeline.py`、`scripts/run_pipeline.py` 的 `load_prompt("asset_prompt_user")` | 旧版资产提示词 user prompt 模板。当前主流程由 `steps/step_04_prompts_img.py` 动态拼用户输入。 |

## 暂未发现代码引用

以下文件目前未被 `rg` 搜到实际代码读取。可以先视为候选规则、历史遗留或待接入文件，修改它们通常不会影响当前主流程。

| 文件 | 说明 |
|---|---|
| `camera_grammar.json` | 未发现当前代码引用。看命名像运镜语法配置，后续若要做独立运镜 Agent 或校验器，可以接入。 |
| `step_04_refine_shots_system.txt` | 未发现当前代码引用。看命名像分镜二次润色 prompt，当前主流程没有接入。 |
| `step_01_research_system.txt` | 文件内容已标注“已迁移，请勿直接编辑”。当前 Step01 已改用 `step_01/_base.txt` + `step_01/styles/*.txt`。 |

## 主流程调用关系速记

```text
Step01 剧本生成
  server/pipeline_runner.py
  -> steps/step_01_research.py
  -> prompts/step_01/_base.txt
  -> prompts/step_01/styles/{风格}.txt

Step01 剧本审核
  server/pipeline_runner.py
  -> steps/step_01_review.py
  -> prompts/step_01_review/_base.txt
  -> prompts/step_01_review/rules.json

Step02 分镜 + 资产 prompt
  server/pipeline_runner.py
  -> steps/step_02_storyboard.py
  -> steps/step_02_script.py
  -> prompts/step_02_script_system.txt
  -> steps/step_04_prompts_img.py
  -> prompts/step_04_extract_assets_system.txt
  -> prompts/step_04_img_single_system.txt

Step03 图片生成
  server/pipeline_runner.py
  -> steps/step_03_generate_assets.py
  -> 使用 Step02 产出的 prompt_map，不直接读取 prompts/*.txt

Step04 视频生成
  server/pipeline_runner.py
  -> steps/step_04_generate_videos.py
  -> steps/step_06_video_prompts.py
  -> prompts/step_06_i2v_polish_system.txt

Step05 合成
  server/pipeline_runner.py
  -> 目前不直接读取 prompts/*.txt
```

## 改 prompt 时的建议

- 改 Step01 剧本能力：优先改 `step_01/_base.txt`；只影响某个风格时改 `step_01/styles/{风格}.txt`。
- 改 Step01 审核标准：改 `step_01_review/_base.txt` 和 `step_01_review/rules.json`。
- 改分镜格式：改 `step_02_script_system.txt`。
- 改角色/场景/道具提取：改 `step_04_extract_assets_system.txt`。
- 改资产定妆图 prompt：改 `step_04_img_single_system.txt`。
- 改 Seedance 视频 prompt 润色：改 `step_06_i2v_polish_system.txt`。
- 改 `asset_prompt_*`、`deepseek_script_*`、`camera_grammar.json`、`step_04_refine_shots_system.txt` 前，先确认是否要重新接入旧流程或新 Agent。
