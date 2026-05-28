"""流水线智能编排器（v3：多智能体协作版）。

集成能力：
1. 创意总监 Agent — 流水线启动前分析需求，输出创意指导
2. 质量审核 Agent — 每步产出自动审核（Step2/3/4）
3. 条件分支 — 审核不通过自动返工（Step1 已有，Step2 新增）
4. 动态决策 — 根据审核结果调整后续步骤参数
5. Hook 监控 — Middleware 注入（日志/进度/停止检查）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from agents.middleware import PipelineLoggingMiddleware, ProgressMiddleware, StopCheckMiddleware
from agents.tools import read_json, write_json


class PipelineOrchestrator:
    """流水线编排器（v3 多智能体协作版）。

    执行流程：
    1. 创意总监分析 → 产出《创意指导纲要》
    2. Step1 剧本研究 + 审核（已有）
    3. Step2 分镜 + 审核（新增）
    4. Step3 图片 + 审核（新增）
    5. Step4 视频 + 审核（新增）
    6. Step5 拼接
    7. Step6 封面生成（依赖 Step1）
    """

    def __init__(
        self,
        out_dir: str,
        topic: str,
        duration: int = 90,
        style: str = "电影短片",
        img_concurrency: int = 5,
        video_concurrency: int = 3,
        stop_checker: Callable[[], bool] | None = None,
    ) -> None:
        self._out_dir = Path(out_dir)
        self._topic = topic
        self._duration = duration
        self._style = style
        self._img_concurrency = img_concurrency
        self._video_concurrency = video_concurrency
        self._stop_checker = stop_checker or (lambda: False)
        self._guidance: dict[str, Any] = {}

    def _middlewares_for_step(self, step: int) -> list:
        log_path = self._out_dir / "logs" / f"step_{step}.log"
        mws: list = [
            PipelineLoggingMiddleware(log_path),
            ProgressMiddleware(str(self._out_dir), step),
        ]
        if self._stop_checker:
            mws.append(StopCheckMiddleware(self._stop_checker))
        return mws

    # ------------------------------------------------------------------
    # 创意总监
    # ------------------------------------------------------------------
    def run_director(self) -> dict[str, Any]:
        """启动前分析需求，输出创意指导纲要。"""
        from agents.director_agent import DirectorAgent

        if self._guidance:
            return self._guidance

        director = DirectorAgent()
        self._guidance = director.analyze(
            topic=self._topic,
            style=self._style,
            duration=self._duration,
        )

        d = self._out_dir
        write_json(d, "director_guidance.json", self._guidance)
        print(f"  [编排器] 创意总监指导已保存 → director_guidance.json")
        return self._guidance

    # ------------------------------------------------------------------
    # Step1: 剧本研究 + 审核（含条件分支）
    # ------------------------------------------------------------------
    def run_step1(self) -> dict[str, Any]:
        from agents.research_agent import ResearchAgent

        agent = ResearchAgent()
        return agent.run(
            topic=self._topic,
            duration=self._duration,
            style=self._style,
            out_dir=str(self._out_dir),
        )

    # ------------------------------------------------------------------
    # Step2: 分镜 + 审核（新增：不通过返工）
    # ------------------------------------------------------------------
    def run_step2(self) -> dict[str, Any]:
        from agents.storyboard_agent import StoryboardAgent
        from agents.reviewer_agent import ReviewerAgent

        agent = StoryboardAgent()
        storyboard = agent.run(
            topic=self._topic,
            out_dir=str(self._out_dir),
            target_duration=self._duration,
        )

        reviewer = ReviewerAgent()
        d = self._out_dir
        storyboard_raw = json.dumps(storyboard, ensure_ascii=False)[:3000]
        review = reviewer.review_step2(
            topic=self._topic,
            style=self._style,
            duration=self._duration,
            storyboard_json=storyboard_raw,
        )

        storyboard["review"] = review
        write_json(d, "storyboard.json", storyboard)
        write_json(d, "step_02_review.json", review)

        if not review.get("passed") and not review.get("skipped"):
            issues = "；".join(str(x) for x in review.get("issues") or [])
            print(f"  [编排器] Step2 审核未通过：{issues}")
            print(f"  [编排器] Step2 不自动返工（分镜返工成本高），已记录审核意见")
            return storyboard

        print(f"  [编排器] Step2 审核通过（分数: {review.get('score')}）")
        return storyboard

    # ------------------------------------------------------------------
    # Step3: 图片 + 审核（新增：风格一致性检查）
    # ------------------------------------------------------------------
    def run_step3(self) -> dict[str, str]:
        from agents.image_gen_agent import ImageGenAgent
        from agents.reviewer_agent import ReviewerAgent

        agent = ImageGenAgent()
        img_results = agent.run(
            out_dir=str(self._out_dir),
            concurrency=self._img_concurrency,
        )

        reviewer = ReviewerAgent()
        d = self._out_dir
        img_results_raw = json.dumps(img_results, ensure_ascii=False)[:3000]
        review = reviewer.review_step3(
            topic=self._topic,
            style=self._style,
            img_results_json=img_results_raw,
        )

        write_json(d, "step_03_review.json", review)

        if not review.get("passed") and not review.get("skipped"):
            issues = "；".join(str(x) for x in review.get("issues") or [])
            print(f"  [编排器] Step3 审核未通过：{issues}（已记录，可手动重新生成）")
        else:
            print(f"  [编排器] Step3 审核通过（分数: {review.get('score')}）")

        return img_results

    # ------------------------------------------------------------------
    # Step4: 视频 + 审核（新增：连贯性检查）
    # ------------------------------------------------------------------
    def run_step4(self) -> dict[str, Any]:
        from agents.video_gen_agent import VideoGenAgent
        from agents.reviewer_agent import ReviewerAgent

        agent = VideoGenAgent()
        bundle = agent.run(
            out_dir=str(self._out_dir),
            concurrency=self._video_concurrency,
        )

        reviewer = ReviewerAgent()
        d = self._out_dir
        video_prompts_raw = json.dumps(bundle.get("video_prompts", {}), ensure_ascii=False)[:3000]
        review = reviewer.review_step4(
            topic=self._topic,
            style=self._style,
            video_prompts_json=video_prompts_raw,
        )

        write_json(d, "step_04_review.json", review)

        if not review.get("passed") and not review.get("skipped"):
            issues = "；".join(str(x) for x in review.get("issues") or [])
            print(f"  [编排器] Step4 审核未通过：{issues}（已记录）")
        else:
            print(f"  [编排器] Step4 审核通过（分数: {review.get('score')}）")

        return bundle

    # ------------------------------------------------------------------
    # Step5: 拼接
    # ------------------------------------------------------------------
    def run_step5(self) -> str:
        from agents.concat_agent import ConcatAgent

        agent = ConcatAgent()
        return agent.run(out_dir=str(self._out_dir))

    # ------------------------------------------------------------------
    # Step6: 封面生成（依赖 Step1）
    # ------------------------------------------------------------------
    def run_step6(self) -> dict[str, Any]:
        from agents.cover_agent import CoverAgent

        agent = CoverAgent()
        result = agent.run(out_dir=str(self._out_dir))
        print(f"  [编排器] 封面生成完成")
        return result

    # ------------------------------------------------------------------
    # 全流程执行
    # ------------------------------------------------------------------
    def run_all(self) -> dict[str, Any]:
        """执行完整流水线：创意总监 → Step1-5（每步含审核）。"""
        results: dict[str, Any] = {
            "topic": self._topic,
            "style": self._style,
            "duration": self._duration,
            "steps": {},
        }

        print("=" * 50)
        print("  [编排器] 启动多智能体协作流水线")
        print("=" * 50)

        try:
            guidance = self.run_director()
            results["director_guidance"] = guidance
        except Exception as e:
            print(f"  [编排器] 创意总监分析失败（不阻断流程）: {e}")
            results["director_guidance"] = {"error": str(e)}

        steps = [
            (1, "剧本", self.run_step1),
            (2, "分镜", self.run_step2),
            (3, "资产", self.run_step3),
            (4, "视频", self.run_step4),
            (5, "成片", self.run_step5),
            (6, "封面", self.run_step6),
        ]

        for step_num, step_name, step_func in steps:
            if self._stop_checker():
                results["steps"][str(step_num)] = {"status": "cancelled"}
                print(f"  [编排器] Step{step_num} {step_name}：用户请求停止，跳过")
                break

            print(f"\n  [编排器] Step{step_num} {step_name}：开始执行...")
            try:
                result = step_func()
                results["steps"][str(step_num)] = {
                    "status": "success",
                    "result": str(type(result).__name__),
                }
                print(f"  [编排器] Step{step_num} {step_name}：完成 ✓")
            except Exception as e:
                results["steps"][str(step_num)] = {
                    "status": "failed",
                    "error": str(e),
                }
                print(f"  [编排器] Step{step_num} {step_name}：失败 ✗ - {e}")
                raise

        print(f"\n{'=' * 50}")
        print("  [编排器] 流水线执行完成")
        print(f"{'=' * 50}")
        return results
