"""Step4 Agent: 视频片段生成。

包装原有的 step_04_generate_videos.py，提供 AgentScope 统一接口。
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from agentscope.agent import Agent

from agents.tools import create_deepseek_model, read_json, write_json


class VideoGenAgent:
    """Step4 视频生成 Agent。

    内部调用原有 step_04_generate_videos.run()，
    使用 Seedance 生成视频片段。
    """

    def __init__(self) -> None:
        self._model = create_deepseek_model(stream=True)
        self._agent = Agent(
            name="视频生成师",
            system_prompt="你是视频生成专家，负责根据分镜和图片生成视频片段。",
            model=self._model,
        )

    @property
    def name(self) -> str:
        return self._agent.name

    def run(
        self,
        out_dir: str,
        concurrency: int = 3,
    ) -> dict[str, Any]:
        from steps.step_04_generate_videos import run as s4

        d = Path(out_dir)
        db_path = str(d / "assets.db")
        storyboard = read_json(d, "storyboard.json")
        img_results = read_json(d, "img_results.json")

        conn = sqlite3.connect(db_path)
        try:
            bundle = s4(conn, storyboard, img_results, db_path, out_dir, concurrency=concurrency)
        finally:
            conn.close()

        write_json(d, "video_prompts.json", bundle.get("video_prompts") or {})
        write_json(d, "video_results.json", bundle.get("video_results") or [])
        return bundle
