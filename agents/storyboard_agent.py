"""Step2 Agent: 分镜脚本生成。

包装原有的 step_02_storyboard.py，提供 AgentScope 统一接口。
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


class StoryboardAgent:
    """Step2 分镜脚本 Agent。

    内部调用原有 step_02_storyboard.run()，
    生成分镜脚本并保存 script.md。
    """

    def __init__(self) -> None:
        self._model = create_deepseek_model(stream=True)
        self._agent = Agent(
            name="分镜导演",
            system_prompt="你是分镜脚本专家，负责将剧本拆解为逐镜分镜脚本。",
            model=self._model,
        )

    @property
    def name(self) -> str:
        return self._agent.name

    def run(
        self,
        topic: str,
        out_dir: str,
        target_duration: int = 90,
    ) -> dict[str, Any]:
        from db import init as db_init, save_run
        from steps.step_02_storyboard import run as s2

        d = Path(out_dir)
        db_path = str(d / "assets.db")
        brief = read_json(d, "script_brief.json")

        storyboard = s2(topic, brief, out_dir, target_duration=target_duration)

        write_json(d, "storyboard.json", storyboard)
        (d / "script.md").write_text(storyboard.get("script") or "", encoding="utf-8")

        conn = db_init(db_path)
        try:
            run_id = d.name
            save_run(conn, run_id, topic, storyboard.get("script") or "")
        finally:
            conn.close()

        return storyboard
