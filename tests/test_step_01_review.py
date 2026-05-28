from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from server import pipeline_runner  # noqa: E402
import steps.step_01_research as step_01_research  # noqa: E402
import steps.step_01_review as step_01_review  # noqa: E402


class TestStep01Review(unittest.TestCase):
    def test_review_prompt_and_rules_exist(self) -> None:
        prompt = Path(_ROOT) / "prompts" / "step_01_review" / "_base.txt"
        rules = Path(_ROOT) / "prompts" / "step_01_review" / "rules.json"
        self.assertTrue(prompt.is_file())
        self.assertTrue(rules.is_file())
        self.assertIn("审核 Agent", prompt.read_text(encoding="utf-8"))
        self.assertEqual(json.loads(rules.read_text(encoding="utf-8"))["pass_score"], 80)

    def test_parse_review_response_accepts_json(self) -> None:
        parsed = step_01_review.parse_review_response(
            '{"passed": true, "score": 92, "issues": [], "revision_prompt": ""}',
            pass_score=80,
        )
        self.assertTrue(parsed["passed"])
        self.assertEqual(parsed["score"], 92)
        self.assertEqual(parsed["issues"], [])

    def test_parse_review_response_creates_revision_prompt_when_failed(self) -> None:
        parsed = step_01_review.parse_review_response(
            '{"passed": false, "score": 60, "issues": ["缺少 audio_layers"]}',
            pass_score=80,
        )
        self.assertFalse(parsed["passed"])
        self.assertIn("缺少 audio_layers", parsed["revision_prompt"])


class TestStep01ReviewPipeline(unittest.TestCase):
    def _make_state(self, out_dir: str) -> None:
        state = pipeline_runner.new_run_state(
            "test_run",
            out_dir,
            "测试主题",
            60,
            "电影短片",
            1,
            1,
        )
        pipeline_runner.save_state(out_dir, state)

    def test_step01_retries_once_when_review_fails_then_passes(self) -> None:
        first_output = "# 故事板标题\n缺少 audio_layers"
        second_output = "# 故事板标题\n# audio_layers\n## background_music"
        failed_review = json.dumps(
            {
                "passed": False,
                "score": 60,
                "issues": ["缺少 audio_layers"],
                "revision_prompt": "请补齐 audio_layers。",
            },
            ensure_ascii=False,
        )
        passed_review = json.dumps(
            {"passed": True, "score": 90, "issues": [], "revision_prompt": ""},
            ensure_ascii=False,
        )

        with tempfile.TemporaryDirectory() as tmp:
            self._make_state(tmp)
            with patch.object(step_01_research, "chat", side_effect=[first_output, second_output]) as mock_step01:
                with patch.object(step_01_review, "chat", side_effect=[failed_review, passed_review]):
                    state = pipeline_runner.execute_step(tmp, 1, force=True)

            self.assertEqual(state["steps"]["1"]["status"], "success")
            written = json.loads((Path(tmp) / "script_brief.json").read_text(encoding="utf-8"))
            self.assertEqual(written["creative_brief"], second_output)
            self.assertTrue(written["review"]["passed"])
            self.assertEqual(len(written["review_attempts"]), 2)
            self.assertEqual(mock_step01.call_count, 2)
            self.assertIn("审核返工要求", mock_step01.call_args_list[1].args[1])

    def test_step01_fails_when_review_fails_twice(self) -> None:
        bad_output = "# 故事板标题\n缺少 audio_layers"
        failed_review = json.dumps(
            {
                "passed": False,
                "score": 55,
                "issues": ["缺少 audio_layers"],
                "revision_prompt": "请补齐 audio_layers。",
            },
            ensure_ascii=False,
        )

        with tempfile.TemporaryDirectory() as tmp:
            self._make_state(tmp)
            with patch.object(step_01_research, "chat", side_effect=[bad_output, bad_output]):
                with patch.object(step_01_review, "chat", side_effect=[failed_review, failed_review]):
                    with self.assertRaises(RuntimeError):
                        pipeline_runner.execute_step(tmp, 1, force=True)

            state = pipeline_runner.load_state(tmp)
            self.assertEqual(state["steps"]["1"]["status"], "failed")
            written = json.loads((Path(tmp) / "script_brief.json").read_text(encoding="utf-8"))
            self.assertFalse(written["review"]["passed"])
            self.assertEqual(len(written["review_attempts"]), 2)

    def test_manual_rewrite_from_review_skips_review(self) -> None:
        old_output = "# 旧剧本\n这一句台词太长需要修改"
        new_output = "# 新剧本\n台词已压缩"

        with tempfile.TemporaryDirectory() as tmp:
            self._make_state(tmp)
            old_brief = {
                "theme": "测试主题",
                "body": old_output,
                "topic": "测试主题",
                "duration_seconds": 60,
                "style": "电影短片",
                "creative_brief": old_output,
                "findings": [{"title": "Step 1 剧本纲要", "content": old_output, "url": "", "query": "deepseek|电影短片"}],
                "summary": "# 旧剧本",
                "review": {
                    "passed": False,
                    "score": 70,
                    "issues": ["单一台词超过 20 个中文字"],
                    "revision_prompt": "请压缩台词，或拆成多个分镜表现。",
                },
                "review_attempts": [],
            }
            Path(tmp, "script_brief.json").write_text(json.dumps(old_brief, ensure_ascii=False), encoding="utf-8")
            Path(tmp, "research.json").write_text(json.dumps(old_brief, ensure_ascii=False), encoding="utf-8")

            with patch.object(step_01_research, "chat", return_value=new_output) as mock_step01:
                with patch.object(step_01_review, "chat") as mock_review:
                    state = pipeline_runner.execute_rewrite_step1_from_review(tmp)

            self.assertEqual(state["steps"]["1"]["status"], "success")
            written = json.loads((Path(tmp) / "script_brief.json").read_text(encoding="utf-8"))
            self.assertEqual(written["creative_brief"], new_output)
            self.assertTrue(written["review"]["skipped"])
            self.assertTrue(written["review_skipped_after_manual_rewrite"])
            self.assertEqual(mock_step01.call_count, 1)
            mock_review.assert_not_called()


if __name__ == "__main__":
    unittest.main()
