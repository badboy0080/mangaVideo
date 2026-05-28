"""Step6 Agent: 短片封面生成。"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from agentscope.agent import Agent

from agents.tools import create_deepseek_model, read_json, write_json


class CoverAgent:
    """Step6 封面生成 Agent。"""

    def __init__(self) -> None:
        self._model = create_deepseek_model(stream=True)
        self._agent = Agent(
            name="封面设计师",
            system_prompt="你是短片封面海报设计师，负责根据剧本概要生成电影节质感封面。",
            model=self._model,
        )

    @property
    def name(self) -> str:
        return self._agent.name

    def run(self, out_dir: str) -> dict[str, Any]:
        from steps.step_09_generate_cover import run as s6

        d = Path(out_dir)
        research = read_json(d, "research.json")
        result = s6(research, out_dir)
        write_json(d, "cover_prompt.json", result)
        return result
