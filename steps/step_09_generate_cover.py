"""Step 6: generate a short-film cover poster from Step 1."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from steps.deepseek_chat import chat as deepseek_chat
from steps.prompt_config import load_registered_system_prompt
from steps.seedream_client import api_key, generate_image

_COVER_SYSTEM = load_registered_system_prompt("step_06_cover.system")


def _resolve_out_dir(out_dir: str) -> Path:
    p = Path(out_dir)
    if not p.is_absolute():
        p = Path(__file__).resolve().parent.parent / out_dir
    return p


def _step1_body(research: dict[str, Any]) -> str:
    body = research.get("body") or research.get("creative_brief") or ""
    if isinstance(body, str) and body.strip():
        return body.strip()
    for item in research.get("findings") or []:
        if isinstance(item, dict) and isinstance(item.get("content"), str):
            content = item["content"].strip()
            if content:
                return content
    return ""


def build_cover_prompt(research: dict[str, Any]) -> str:
    """Ask the LLM for the final image prompt. Empty LLM output stays empty."""
    body = _step1_body(research)
    if not body:
        raise RuntimeError("Step06 需要先完成 Step01，并确保 research.json 中有创意正文")

    user_body = (
        "### Step01 创意正文\n"
        f"{body[:18000]}\n\n"
        "请根据上面的故事梗概、片名、视觉风格和情绪基调，输出一段 16:9 短片封面文生图 prompt。"
    )
    print("  [DeepSeek] 根据 Step01 生成短片封面提示词...")
    prompt = deepseek_chat(
        _COVER_SYSTEM,
        user_body,
        temperature=0.65,
        max_tokens=1800,
        timeout=180,
    ).strip()
    if not prompt:
        raise RuntimeError("Step06 封面提示词为空，请检查 DeepSeek 配置或 Step01 内容")
    return prompt


def run(research: dict[str, Any], out_dir: str) -> dict[str, Any]:
    d = _resolve_out_dir(out_dir)
    image_dir = d / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    prompt = build_cover_prompt(research)
    cover_path = image_dir / "cover.png"
    size = os.environ.get("SEEDREAM_COVER_SIZE", "2K").strip() or "2K"

    print("  [Seedream] 生成 16:9 短片封面图...")
    written = generate_image(
        prompt,
        cover_path,
        api_key_override=api_key(),
        image_inputs=None,
        size=size,
    )
    rel = written.resolve().relative_to(d.resolve()).as_posix()

    result = {
        "body": prompt,
        "prompt": prompt,
        "image": rel,
        "source_step": 1,
        "aspect_ratio": "16:9",
        "seedream_size": size,
    }
    with open(d / "cover_prompt.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  封面已完成：{rel}")
    return result
