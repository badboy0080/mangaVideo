# Seedream 4.5 助手生图说明

本项目已接入火山引擎 **Seedream 4.5**（模型 ID：`doubao-seedream-4-5-251128`），用于：

1. **流水线 Step 5**：按 Step 4 的英文提示词批量生成角色/场景/道具图  
2. **网页/UI 资产**：首页卡片、占位图等，可由 Cursor 助手或 API 即时生成  
3. **对话中让我生图**：你在 Cursor 里说「用 Seedream 给热门预设生成缩略图」，我会跑脚本或调 API

## 1. 配置 API Key

在项目根目录 `.env` 中填写（二选一即可）：

```env
ARK_API_KEY=你的火山引擎密钥
# 或
VOLCENGINE_API_KEY=你的火山引擎密钥

# 可选：默认已是 4.5，一般不用改
SEEDREAM_MODEL=doubao-seedream-4-5-251128
```

改完后 **重启** `uvicorn`（后端 API）。

## 2. 命令行（推荐给 Cursor 助手用）

```bash
# 生成一张图，落在 outputs/_ui_assets/
python scripts/seedream_generate.py --prompt "cinematic film still, moody lighting, 16:9 thumbnail, no text"

# 生成并复制到网页静态目录（首页热门预设缩略图）
python scripts/seedream_generate.py \
  --prompt "..." \
  --purpose hot_preset_电影短片 \
  --save-as preset_movie \
  --copy-to web/public/presets/movie.png
```

生成记录会追加到 `outputs/_ui_assets/manifest.jsonl`（含 prompt、用途、文件名）。

## 3. HTTP API（网页或 Postman）

**检查是否已配置密钥**

`GET /api/seedream/status`

**生成一张图**

`POST /api/seedream/generate`

```json
{
  "prompt": "brand ad style product hero shot, clean studio light",
  "purpose": "hot_preset_品牌广告",
  "save_as": "preset_brand",
  "size": "2K"
}
```

返回示例：

```json
{
  "ok": true,
  "filename": "preset_brand.png",
  "url": "/api/ui-assets/preset_brand.png",
  "path": "D:/.../outputs/_ui_assets/preset_brand.png"
}
```

浏览器预览（API 默认 `http://127.0.0.1:8765`）：

`http://127.0.0.1:8765/api/ui-assets/preset_brand.png`

## 4. 首页热门预设缩略图（建议流程）

1. 打开 [`web/asset-prompts.json`](../web/asset-prompts.json)，里面有 7 种风格的英文提示词  
2. 对每一项执行 `seedream_generate.py --copy-to web/public/presets/<id>.png`  
3. 在 `HotSkillsRow` 里把渐变块换成 `<img src="/presets/movie.png" />`（需要时再改前端）

## 5. 在对话里怎么跟我说

你可以直接说：

- 「用 Seedream 4.5 给首页 7 个热门预设各生成一张缩略图」  
- 「根据这段描述生成一张 2K 场景图，保存到 web/public/presets」  
- 「检查一下 Seedream API 是否配置好了」

我会用本项目的脚本或 API 完成，不会把密钥写进代码仓库。
