"""Step 3: generate character, prop, and scene images from storyboard prompts."""
from __future__ import annotations

from typing import Any

from steps.step_02_storyboard import to_prompt_map
from steps.step_05_generate_imgs import run as generate_images


def run(conn, storyboard: dict[str, Any], out_dir: str, concurrency: int = 5) -> dict[str, str]:
    return generate_images(conn, to_prompt_map(storyboard), out_dir, concurrency=concurrency)
