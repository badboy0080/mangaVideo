# MangaVideo

![MangaVideo 项目大图](docs/assets/manga-video-hero.png)

一个面向短片创作的 AI 流水线工具：输入一个创意主题，系统会一步步生成剧本纲要、分镜、角色/场景资产图、视频片段、最终成片和封面图。

它适合用来做：

- 漫画感短片 / 动画叙事
- 电影短片概念片
- 品牌广告短片
- 游戏 CG 风格短片
- MV、科幻短片、纪录片风格内容

## 项目能做什么

你只需要在网页里输入一个主题，例如：

> 一个关于少年与飞鱼的奇幻冒险故事，发生在云上的古老小镇。

然后系统会按步骤推进：

1. **剧本**：用 DeepSeek 生成故事大纲、人物与场景方向。
2. **分镜**：把故事拆成镜头，生成每个镜头的画面说明和视频提示词。
3. **资产**：提取主要角色和场景，整理成可复用的视觉资产。
4. **视频**：用 Seedream / Seedance 生成图片和视频片段。
5. **成片**：用 ffmpeg 把视频片段拼接成 `final.mp4`。
6. **封面**：根据故事生成短片封面图，方便项目展示。

项目还带有一个 Web 控制台，可以查看每一步产物、编辑文本、重跑单步、查看运行日志。

## 项目结构

```text
manga-pipeline/
├─ web/                 # 前端页面，React + Vite
├─ server/              # 后端 API，FastAPI
├─ steps/               # 每一步流水线逻辑
├─ agents/              # Agent 封装：导演、审核员、生成员等
├─ prompts/             # 各步骤使用的提示词模板
├─ tests/               # 自动化测试
├─ docs/                # 项目文档和 README 图片
├─ outputs/             # 本地生成结果，已被 Git 忽略
├─ db/                  # 本地数据库，已被 Git 忽略
└─ .env                 # 本地密钥配置，已被 Git 忽略
```

## 技术栈

| 模块 | 技术 |
| --- | --- |
| 前端 | React、TypeScript、Vite、Tailwind CSS |
| 后端 | Python、FastAPI |
| 文本生成 | DeepSeek |
| 图片生成 | Seedream |
| 视频生成 | Seedance |
| 视频拼接 | ffmpeg |
| 数据存储 | 本地 SQLite / 输出文件 |

## 第一次使用

### 1. 安装 Python 依赖

在项目根目录执行：

```powershell
pip install -r requirements.txt
```

### 2. 配置密钥

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

然后打开 `.env`，填入你的密钥：

```env
DEEPSEEK_API_KEY=你的 DeepSeek 密钥
ARK_API_KEY=你的火山引擎 Ark 密钥
```

说明：

- `DEEPSEEK_API_KEY`：用于生成剧本、分镜、提示词、审核意见。
- `ARK_API_KEY`：用于 Seedream 生图和 Seedance 生视频。

### 3. 安装前端依赖

```powershell
cd web
pnpm install
cd ..
```

## 日常启动

需要开两个终端。

### 终端 1：启动后端

```powershell
python -m uvicorn server.main:app --host 127.0.0.1 --port 8765
```

健康检查地址：

```text
http://127.0.0.1:8765/api/health
```

### 终端 2：启动前端

```powershell
cd web
pnpm dev
```

浏览器打开：

```text
http://localhost:5173
```

## 常用命令

### 前端构建

```powershell
cd web
pnpm run build
```

### 运行后端测试

```powershell
python -m unittest discover tests
```

### 命令行运行流水线

```powershell
python pipeline.py "你的短片主题" --duration 90 --style 电影短片
```

## 产物保存在哪里

生成结果默认保存在：

```text
outputs/<项目ID>/
```

常见文件包括：

- `script_brief.json`：剧本纲要
- `storyboard.json`：分镜内容
- `assets.json`：角色和场景资产
- `images/`：生成图片
- `videos/`：生成视频片段
- `final.mp4`：最终成片
- `cover.png`：封面图

这些都是本地生成物，已经加入 `.gitignore`，不会上传到 GitHub。

## Git 忽略规则

项目已经忽略这些本地文件：

- `.env`：本地密钥
- `node_modules/`、`web/node_modules/`：依赖目录
- `outputs/`、`output/`、`manga-pipeline/output/`：生成产物
- `db/*.db`：本地数据库
- `logs/`：运行日志
- `web/dist/`：前端构建结果
- `.cursor/`、`.trae/`、`.idea/`、`.vscode/`：本地编辑器配置

这样可以避免把密钥、视频、图片、数据库和缓存文件上传到仓库。

## 当前注意事项

- 跑真实 AI 生成时，需要有效的 DeepSeek 和 Ark 密钥。
- 生成视频和拼接成片前，请确认已经安装 `ffmpeg`。
- 如果网页显示连接不上 API，优先检查后端是否还在运行。
- 如果 GitHub 推送失败，多半是网络连不上 GitHub，不是项目代码问题。

## 相关文档

- [启动说明.md](启动说明.md)：更详细的本地启动说明
- [handoff-log.md](handoff-log.md)：近期开发交接记录
- [prompts/README.md](prompts/README.md)：提示词文件说明
- [docs/ai-short-film-workflow-analysis.md](docs/ai-short-film-workflow-analysis.md)：AI 短片流程分析
