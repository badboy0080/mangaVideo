"""Common utilities and tool wrappers for pipeline agents.

Provides shared helper functions that agents use to interact with
external services (Seedream, Seedance, ffmpeg), filesystem, and
AgentScope message system.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from agentscope.credential import DeepSeekCredential
from agentscope.model import DeepSeekChatModel


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_deepseek_model(
    model_name: str = "deepseek-chat",
    stream: bool = True,
) -> DeepSeekChatModel:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        config_path = os.path.expanduser("~/.deepseek/api_key")
        if os.path.isfile(config_path):
            with open(config_path, encoding="utf-8") as f:
                api_key = f.read().strip()

    return DeepSeekChatModel(
        credential=DeepSeekCredential(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
        ),
        model=model_name,
        stream=stream,
        max_retries=3,
        context_size=65536,
    )


def read_json(d: Path, name: str) -> Any:
    import json
    with open(d / name, encoding="utf-8") as f:
        return json.load(f)


def write_json(d: Path, name: str, obj: Any) -> None:
    import json
    d.mkdir(parents=True, exist_ok=True)
    with open(d / name, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
