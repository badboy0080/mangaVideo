---
name: seedream-manga-pipeline
description: Generate UI or pipeline images with Volcengine Seedream 4.5 in manga-pipeline. Use when the user asks to generate images, thumbnails, preset cards, placeholders, or "用 seedream 生图" for this project's web or outputs.
---

# manga-pipeline Seedream 生图

## 前置

- 项目根 `.env` 含 `ARK_API_KEY` 或 `VOLCENGINE_API_KEY`
- 默认模型：`doubao-seedream-4-5-251128`（`SEEDREAM_MODEL` 可覆盖）

## 优先方式

1. **单张 / 首页资产**：`python scripts/seedream_generate.py --prompt "..." [--save-as name] [--copy-to web/public/presets/x.png]`
2. **批量首页预设**：读 `web/asset-prompts.json`，对每条 `presets[]` 执行脚本并 `--copy-to web/public/presets/{id}.png`
3. **API 已运行时**：`POST http://127.0.0.1:8765/api/seedream/generate`（body 见 `docs/seedream-assistant.md`）

## 禁止

- 不要把 API Key 写入代码或提交到 Git
- 不要用批量删除命令清理 `outputs/_ui_assets`

## 代码入口

- 客户端：`steps/seedream_client.py`
- 服务：`server/seedream_service.py`
- 流水线 Step 5：`steps/step_05_generate_imgs.py`
