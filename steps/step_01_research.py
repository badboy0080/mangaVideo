"""
Step 1: 剧本纲要（DeepSeek）

产出约定：`creative_brief` / `findings[].content` **仅**为模型正文；`summary` 仅为正文首行截取（整理用，非模板生成）。
无 API 或空返回时不写占位纲要。见 `steps.step_output_policy`。

System 提示词 = `prompts/step_01/_base.txt` + `prompts/step_01/styles/{风格}.txt`（按用户选择的风格类型加载）。
"""
from __future__ import annotations

from pathlib import Path

from steps.deepseek_chat import chat
from steps.prompt_config import prompt_registry_entry, prompts_search_dir

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts" / "step_01"

STYLE_PRESETS: tuple[str, ...] = (
    "电影短片",
    "品牌广告",
    "动画叙事",
    "游戏CG",
    "MV",
    "科幻短片",
    "纪录片风格",
)

_STYLE_ALIASES: dict[str, str] = {
    "电影": "电影短片",
    "广告片": "品牌广告",
    "动画短片": "动画叙事",
    "动画": "动画叙事",
}


def resolve_style_key(style: str) -> str:
    s = (style or "").strip()
    return _STYLE_ALIASES.get(s, s)


def validate_style(style: str) -> str:
    """返回规范风格名；非法时抛 ValueError。"""
    key = resolve_style_key(style)
    if key not in STYLE_PRESETS:
        allowed = "、".join(STYLE_PRESETS)
        raise ValueError(f"不支持的风格类型: {style!r}，请使用: {allowed}")
    return key


def load_step01_system_prompt(style: str) -> str:
    key = validate_style(style)
    entry = prompt_registry_entry("step_01_script.system")
    base_rel = str(entry.get("relative_filename") or "step_01/_base.txt")
    style_dir = str(entry.get("style_dir") or "step_01/styles")
    base_path = prompts_search_dir() / base_rel
    if not base_path.is_file():
        base_path = _PROMPT_DIR / "_base.txt"
    style_path = prompts_search_dir() / style_dir / f"{key}.txt"
    if not style_path.is_file():
        style_path = _PROMPT_DIR / "styles" / f"{key}.txt"
    if not base_path.is_file():
        raise FileNotFoundError(f"缺少 Step 1 底座提示词: {base_path}")
    if not style_path.is_file():
        raise FileNotFoundError(f"缺少 Step 1 风格提示词: {style_path}")
    base = base_path.read_text(encoding="utf-8").strip()
    style_part = style_path.read_text(encoding="utf-8").strip()
    return f"{base}\n\n---\n\n# 风格专章\n\n{style_part}"


def run(topic: str, duration_seconds: int = 90, style: str = "电影短片") -> dict:
    """
    返回 dict（写入 research.json），包含:
      - topic, duration_seconds, style（规范名）
      - creative_brief: DeepSeek 返回的正文（仅此；无 API 时不写占位）
      - findings[].content: 与 creative_brief 相同（全量，不截断）
      - summary: 取正文首条非空行的前 240 字（字符来自模型，无本地模板句）
    """
    topic_s = str(topic).strip()
    style_key = validate_style(style)
    duration_s = int(duration_seconds)

    user_prompt = (
        f"主题：{topic_s}\n"
        f"风格类型：{style_key}\n"
        f"时长（秒）：{duration_s}"
    )

    system_prompt = load_step01_system_prompt(style_key)

    print(f"  [DeepSeek] 根据创建动画页面参数生成 Step 1 剧本纲要（{duration_s}s · {style_key}）...")
    creative_brief = chat(
        system_prompt,
        user_prompt,
        temperature=0.75,
        max_tokens=6000,
        timeout=180,
    ).strip()

    if not creative_brief:
        print(
            "  [警告] DeepSeek 未返回正文（检查 DEEPSEEK_API_KEY / 网络）；"
            "creative_brief 保持为空，不写本地占位文案。"
        )

    summary_line = ""
    if creative_brief:
        for line in creative_brief.splitlines():
            s = line.strip()
            if s:
                summary_line = s[:240]
                break

    return {
        "theme": topic_s,
        "body": creative_brief,
        "topic": topic_s,
        "duration_seconds": duration_s,
        "style": style_key,
        "creative_brief": creative_brief,
        "findings": [
            {
                "title": "Step 1 剧本纲要",
                "content": creative_brief,
                "url": "",
                "query": f"deepseek|{style_key}",
            }
        ],
        "summary": summary_line,
    }
