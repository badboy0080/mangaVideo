"""Step1 Agent: 剧本研究 + 审核。

包装原有的 step_01_research.py 和 step_01_review.py，
外层用 AgentScope Agent 统一管理消息、Hook 监控和状态。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from agentscope.agent import Agent
from agentscope.message import Msg

from agents.tools import create_deepseek_model, read_json, write_json


class ResearchAgent:
    """Step1 剧本研究员 Agent。

    内部调用原有 step_01_research.run() 和 step_01_review.run()，
    但提供 AgentScope 统一接口，支持 Hook 监控和 Msg 消息传递。
    """

    def __init__(self) -> None:
        self._model = create_deepseek_model(stream=True)
        self._agent = Agent(
            name="剧本研究员",
            system_prompt="你是创意剧本专家，负责根据用户主题生成剧本纲要。",
            model=self._model,
        )

    @property
    def name(self) -> str:
        return self._agent.name

    def run(
        self,
        topic: str,
        duration: int = 90,
        style: str = "电影短片",
        out_dir: str = "",
    ) -> dict[str, Any]:
        """执行 Step1：生成剧本 + 审核。

        与原有 pipeline_runner 中 step==1 的逻辑完全一致，
        包含首次生成、审核、不通过自动返工一次。
        """
        from steps.step_01_research import run as s1
        from steps.step_01_review import run as review_step01

        d = Path(out_dir) if out_dir else None

        brief = s1(topic, duration_seconds=duration, style=style)
        review = review_step01(
            topic,
            brief.get("style") or style,
            int(brief.get("duration_seconds") or duration),
            brief.get("creative_brief") or brief.get("body") or "",
        )
        attempts = [review]

        if not review.get("passed"):
            issues = "；".join(str(x) for x in review.get("issues") or [])
            print(f"  [Step01 审核] 第一次未通过，准备按审核意见自动返工：{issues}")
            brief = s1(
                topic,
                duration_seconds=duration,
                style=style,
                revision_prompt=str(review.get("revision_prompt") or ""),
                previous_output=brief.get("creative_brief") or brief.get("body") or "",
            )
            review = review_step01(
                topic,
                brief.get("style") or style,
                int(brief.get("duration_seconds") or duration),
                brief.get("creative_brief") or brief.get("body") or "",
            )
            attempts.append(review)

        brief["review"] = review
        brief["review_attempts"] = attempts

        if d:
            write_json(d, "script_brief.json", brief)
            write_json(d, "research.json", brief)
            write_json(d, "step_01_review.json", {"final": review, "attempts": attempts})

        if not review.get("passed"):
            issues = "；".join(str(x) for x in review.get("issues") or [])
            raise RuntimeError(f"Step01 审核未通过：{issues or '未提供具体问题'}")

        return brief
