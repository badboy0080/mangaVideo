"""Step3 Agent: 图片资产生成。

包装原有的 step_03_generate_assets.py，提供 AgentScope 统一接口。
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


class ImageGenAgent:
    """Step3 图片生成 Agent。

    内部调用原有 step_03_generate_assets.run()，
    使用 Seedream 生成角色/场景/道具图片。
    """

    def __init__(self) -> None:
        self._model = create_deepseek_model(stream=True)
        self._agent = Agent(
            name="美术生成师",
            system_prompt="你是视觉资产生成专家，负责根据分镜生成角色、场景和道具图片。",
            model=self._model,
        )

    @property
    def name(self) -> str:
        return self._agent.name

    def run(
        self,
        out_dir: str,
        concurrency: int = 5,
    ) -> dict[str, str]:
        from steps.step_03_generate_assets import run as s3

        d = Path(out_dir)
        db_path = str(d / "assets.db")
        storyboard = read_json(d, "storyboard.json")

        conn = sqlite3.connect(db_path)
        try:
            img_results = s3(conn, storyboard, out_dir, concurrency=concurrency)
        finally:
            conn.close()

        write_json(d, "img_results.json", img_results)
        return img_results
