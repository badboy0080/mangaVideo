"""质量审核 Agent：全流程质量把关。

支持对流水线任意步骤的产出进行质量审核。
与 Step1 审核 Agent 配合使用，共同构成全流程质量体系。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from agentscope.agent import Agent

from agents.tools import create_deepseek_model


STORYBOARD_REVIEW_PROMPT = """你是分镜审核专家。审核 Step2 生成的分镜脚本质量。

## 审核维度

1. **镜头数量合理**：分镜数量是否匹配目标时长（通常每 8-15 秒一个分镜）
2. **画面描述具体**：每个分镜是否有具体的画面描述，而不是空洞的形容词
3. **角色一致性**：同一角色在不同分镜中的描述是否一致
4. **节奏变化**：是否有景别变化（全景/中景/特写交替）
5. **叙事连贯**：分镜之间是否有因果或情绪递进关系

## 输出格式
只输出 JSON：
{
  "passed": true,
  "score": 85,
  "issues": [],
  "revision_prompt": ""
}
"""

ASSET_REVIEW_PROMPT = """你是视觉资产审核专家。审核 Step3 生成的图片资产质量。

## 审核维度

1. **覆盖完整性**：是否覆盖了所有必需的角色、场景、道具
2. **风格统一性**：同类型资产的视觉风格是否一致
3. **功能匹配**：资产是否匹配分镜中的描述
4. **数量合理**：资产数量是否适中（不过多不过少）

## 输出格式
只输出 JSON：
{
  "passed": true,
  "score": 85,
  "issues": [],
  "revision_prompt": ""
}
"""

VIDEO_REVIEW_PROMPT = """你是视频片段审核专家。审核 Step4 生成的视频片段质量。

## 审核维度

1. **片段完整性**：每个分镜是否有对应的视频片段
2. **时长匹配**：视频片段时长是否接近分镜指定的时长
3. **画面连贯**：相邻片段的画面风格是否一致
4. **动作流畅**：视频内容是否自然流畅

## 输出格式
只输出 JSON：
{
  "passed": true,
  "score": 85,
  "issues": [],
  "revision_prompt": ""
}
"""

_STEP_REVIEW_PROMPTS = {
    "storyboard": STORYBOARD_REVIEW_PROMPT,
    "assets": ASSET_REVIEW_PROMPT,
    "videos": VIDEO_REVIEW_PROMPT,
}

_DEFAULT_PASS_SCORE = 75


class ReviewerAgent:
    """通用质量审核 Agent。

    支持对 Step2（分镜）、Step3（资产）、Step4（视频）进行审核。
    Step1 已有专用审核 Agent，不重复实现。
    """

    def __init__(self) -> None:
        self._model = create_deepseek_model(stream=True)
        self._agent = Agent(
            name="质量审核员",
            system_prompt="你是专业质量审核专家，负责审核流水线各步骤的产出质量。",
            model=self._model,
        )

    @property
    def name(self) -> str:
        return self._agent.name

    def review_step2(
        self,
        topic: str,
        style: str,
        duration: int,
        storyboard_json: str,
        pass_score: int = _DEFAULT_PASS_SCORE,
    ) -> dict[str, Any]:
        """审核 Step2 分镜脚本质量。"""
        return self._review(
            step_name="storyboard",
            system_prompt=STORYBOARD_REVIEW_PROMPT,
            topic=topic,
            style=style,
            duration=duration,
            artifact=storyboard_json,
            pass_score=pass_score,
        )

    def review_step3(
        self,
        topic: str,
        style: str,
        img_results_json: str,
        pass_score: int = _DEFAULT_PASS_SCORE,
    ) -> dict[str, Any]:
        """审核 Step3 图片资产质量。"""
        return self._review(
            step_name="assets",
            system_prompt=ASSET_REVIEW_PROMPT,
            topic=topic,
            style=style,
            duration=0,
            artifact=img_results_json,
            pass_score=pass_score,
        )

    def review_step4(
        self,
        topic: str,
        style: str,
        video_prompts_json: str,
        pass_score: int = _DEFAULT_PASS_SCORE,
    ) -> dict[str, Any]:
        """审核 Step4 视频片段质量。"""
        return self._review(
            step_name="videos",
            system_prompt=VIDEO_REVIEW_PROMPT,
            topic=topic,
            style=style,
            duration=0,
            artifact=video_prompts_json,
            pass_score=pass_score,
        )

    def _review(
        self,
        step_name: str,
        system_prompt: str,
        topic: str,
        style: str,
        duration: int,
        artifact: str,
        pass_score: int,
    ) -> dict[str, Any]:
        from steps.deepseek_chat import chat

        user_prompt = (
            f"项目主题：{topic}\n"
            f"风格类型：{style}\n"
        )
        if duration > 0:
            user_prompt += f"目标时长（秒）：{duration}\n"
        user_prompt += (
            f"通过分数：{pass_score}\n\n"
            f"请审核以下 {step_name} 产出：\n"
            f"----- OUTPUT START -----\n"
            f"{artifact}\n"
            f"----- OUTPUT END -----"
        )

        print(f"  [审核员] 审核 Step {step_name} 质量...")
        raw = chat(system_prompt, user_prompt, temperature=0.2, max_tokens=1500, timeout=120)

        if not raw:
            return {
                "passed": True,
                "score": pass_score,
                "issues": [],
                "revision_prompt": "",
                "skipped": True,
                "note": "审核 Agent 无响应，自动通过",
            }

        try:
            s = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.S | re.I)
            data = json.loads(s)
        except json.JSONDecodeError:
            return {
                "passed": True,
                "score": pass_score,
                "issues": [f"审核 Agent 返回格式异常: {raw[:200]}"],
                "revision_prompt": "",
                "skipped": True,
            }

        score = max(0, min(100, int(data.get("score", pass_score))))
        issues = data.get("issues", [])
        if isinstance(issues, str):
            issues = [issues]
        passed = bool(data.get("passed", score >= pass_score))

        return {
            "passed": passed,
            "score": score,
            "issues": issues,
            "revision_prompt": str(data.get("revision_prompt", "")),
        }
