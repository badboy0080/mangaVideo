from __future__ import annotations

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from steps.script_split import split_shots_standard  # noqa: E402


class TestScriptSplit(unittest.TestCase):
    def test_splits_markdown_prefixed_storyboard_headers(self) -> None:
        script = """# 第一幕

## 分镜 1｜8秒｜小明走神

图生视频（I2V）— 整段复制

镜头缓慢推近。

---

## 分镜 2｜6秒｜穿越转场

图生视频（I2V）— 整段复制

光线包围角色。
"""

        shots = split_shots_standard(script)

        self.assertEqual(len(shots), 2)
        self.assertEqual(shots[0][0], "1")
        self.assertEqual(shots[0][1], 8)
        self.assertIn("镜头缓慢推近", shots[0][2])
        self.assertEqual(shots[1][0], "2")
        self.assertEqual(shots[1][1], 6)


if __name__ == "__main__":
    unittest.main()
