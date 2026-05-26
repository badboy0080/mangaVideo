from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import steps.step_01_research as step_01_research  # noqa: E402


class TestStep01Research(unittest.TestCase):
    def test_style_prompt_files_exist(self) -> None:
        base = Path(__file__).resolve().parent.parent / "prompts" / "step_01" / "_base.txt"
        self.assertTrue(base.is_file(), "_base.txt missing")
        for key in step_01_research.STYLE_PRESETS:
            p = Path(__file__).resolve().parent.parent / "prompts" / "step_01" / "styles" / f"{key}.txt"
            self.assertTrue(p.is_file(), f"missing style prompt: {key}")
            self.assertGreater(len(p.read_text(encoding="utf-8").strip()), 50)

    def test_resolve_style_alias(self) -> None:
        self.assertEqual(step_01_research.resolve_style_key("广告片"), "品牌广告")
        self.assertEqual(step_01_research.resolve_style_key("电影短片"), "电影短片")

    def test_validate_style_rejects_unknown(self) -> None:
        with self.assertRaises(ValueError):
            step_01_research.validate_style("自定义风格")

    def test_load_prompt_includes_style_chapter(self) -> None:
        sys = step_01_research.load_step01_system_prompt("品牌广告")
        self.assertIn("风格专章", sys)
        self.assertIn("当前风格类型：品牌广告", sys)
        self.assertIn("品牌创意总监", sys)

    def test_load_prompt_alias_same_as_canonical(self) -> None:
        a = step_01_research.load_step01_system_prompt("广告片")
        b = step_01_research.load_step01_system_prompt("品牌广告")
        self.assertEqual(a, b)

    def test_run_passes_page_values_directly_to_deepseek(self) -> None:
        brief = "这是 DeepSeek 返回的剧本纲要正文。"

        with patch.object(step_01_research, "chat", return_value=brief) as mock_chat:
            result = step_01_research.run("记忆坠城", duration_seconds=60, style="动画叙事")

        system_arg = mock_chat.call_args[0][0]
        self.assertIn("当前风格类型：动画叙事", system_arg)
        mock_chat.assert_called_once_with(
            system_arg,
            "主题：记忆坠城\n风格类型：动画叙事\n时长（秒）：60",
            temperature=0.75,
            max_tokens=6000,
            timeout=180,
        )
        self.assertEqual(result["topic"], "记忆坠城")
        self.assertEqual(result["theme"], "记忆坠城")
        self.assertEqual(result["duration_seconds"], 60)
        self.assertEqual(result["style"], "动画叙事")
        self.assertEqual(result["body"], brief)
        self.assertEqual(result["creative_brief"], brief)
        self.assertEqual(result["findings"][0]["content"], brief)

    def test_run_keeps_empty_when_deepseek_returns_empty(self) -> None:
        with patch.object(step_01_research, "chat", return_value=""):
            result = step_01_research.run("失控实验", duration_seconds=45, style="电影短片")

        self.assertEqual(result["topic"], "失控实验")
        self.assertEqual(result["theme"], "失控实验")
        self.assertEqual(result["duration_seconds"], 45)
        self.assertEqual(result["style"], "电影短片")
        self.assertEqual(result["body"], "")
        self.assertEqual(result["creative_brief"], "")
        self.assertEqual(result["findings"][0]["content"], "")
        self.assertEqual(result["summary"], "")


if __name__ == "__main__":
    unittest.main()
