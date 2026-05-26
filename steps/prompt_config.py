"""从大模型「系统提示词」文件或环境变量加载配置。

优先级：
1. 各步骤专用的「文件路径」环境变量（指向 UTF-8 文本）
2. 目录 `MANGA_PROMPTS_DIR`（或默认项目根目录下 `prompts/`）里的同名模板文件

产品经理备忘：`环境变量` 指写在 .env 或系统里的 KEY=value，用来改路径而不用改代码。
"""
from __future__ import annotations

import json
import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_BUILTIN_PROMPTS_DIR = _REPO_ROOT / "prompts"


def prompts_search_dir() -> Path:
    """可配置提示词目录；未设置则用项目内置 `prompts/`。"""
    override = os.environ.get("MANGA_PROMPTS_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    return _BUILTIN_PROMPTS_DIR


def load_system_prompt(
    *,
    env_path_key: str,
    relative_filename: str,
) -> str:
    """
    env_path_key: 例如 STEP02_SCRIPT_SYSTEM_PROMPT_FILE，值为某 .txt 的绝对/相对路径。
    relative_filename: 在 prompts 目录下的默认文件名。
    """
    raw_path = os.environ.get(env_path_key, "").strip()
    if raw_path:
        p = Path(raw_path).expanduser()
        if p.is_file():
            return p.read_text(encoding="utf-8").strip()

    for base in (prompts_search_dir(), _BUILTIN_PROMPTS_DIR):
        candidate = base / relative_filename
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8").strip()

    raise FileNotFoundError(
        f"找不到系统提示词文件「{relative_filename}」。请放入 prompts/ 目录，"
        f"或设置环境变量 {env_path_key} 指向自定义 UTF-8 文本路径。"
    )


def load_pipeline_prompt_config() -> dict:
    """Load the centralized prompt registry."""
    raw_path = os.environ.get("MANGA_PIPELINE_PROMPTS_CONFIG", "").strip()
    path = Path(raw_path).expanduser() if raw_path else _BUILTIN_PROMPTS_DIR / "pipeline_prompts.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing prompt registry: {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not isinstance(data.get("prompts"), dict):
        raise ValueError(f"Invalid prompt registry: {path}")
    return data


def prompt_registry_entry(key: str) -> dict:
    registry = load_pipeline_prompt_config()
    entry = registry["prompts"].get(key)
    if not isinstance(entry, dict):
        raise KeyError(f"Prompt registry key not found: {key}")
    if entry.get("enabled") is False:
        raise ValueError(f"Prompt registry key is disabled: {key}")
    return entry


def load_registered_system_prompt(key: str) -> str:
    entry = prompt_registry_entry(key)
    return load_system_prompt(
        env_path_key=str(entry.get("env_path_key") or ""),
        relative_filename=str(entry.get("relative_filename") or ""),
    )
