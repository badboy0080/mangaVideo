"""Step5 Agent: 视频拼接。

包装原有的 step_08_concat.py，提供 AgentScope 统一接口。
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

from agents.tools import create_deepseek_model


class ConcatAgent:
    """Step5 视频拼接 Agent。

    内部调用原有 step_08_concat.run()，
    使用 ffmpeg 将所有视频片段拼接为最终成片。
    """

    def __init__(self) -> None:
        self._model = create_deepseek_model(stream=True)
        self._agent = Agent(
            name="剪辑师",
            system_prompt="你是视频剪辑专家，负责将视频片段拼接为最终成片。",
            model=self._model,
        )

    @property
    def name(self) -> str:
        return self._agent.name

    def run(self, out_dir: str) -> str:
        from steps.step_08_concat import run as s5

        d = Path(out_dir)
        db_path = str(d / "assets.db")

        conn = sqlite3.connect(db_path)
        try:
            final_mp4 = s5(conn, out_dir)
        finally:
            conn.close()

        return final_mp4
