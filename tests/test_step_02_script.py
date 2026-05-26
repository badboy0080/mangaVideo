from __future__ import annotations

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import steps.step_02_script as step_02_script  # noqa: E402


class TestStep02Script(unittest.TestCase):
    def test_run_keeps_empty_when_deepseek_returns_empty(self) -> None:
        research = {"style": "电影", "creative_brief": "纲要"}
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(step_02_script, "deepseek_chat", return_value=""):
                result = step_02_script.run("测试主题", research, tmp, target_duration=60)
            self.assertEqual(result["script"], "")
            self.assertEqual(result["shots"], 0)
            with open(result["script_path"], encoding="utf-8") as f:
                self.assertEqual(f.read(), "")

    def test_script_md_is_model_body_only(self) -> None:
        body = "分镜 1｜8 秒｜测试\n\n图生视频（I2V）— 整段复制\n\n镜头推进。"
        research = {"style": "动画", "creative_brief": "纲要"}
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(step_02_script, "deepseek_chat", return_value=body):
                result = step_02_script.run("测试主题", research, tmp, target_duration=30)
            self.assertEqual(result["script"], body)
            with open(result["script_path"], encoding="utf-8") as f:
                saved = f.read()
            self.assertEqual(saved, body)
            self.assertNotIn("# 测试主题", saved)


if __name__ == "__main__":
    unittest.main()
