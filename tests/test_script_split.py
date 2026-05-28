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

    def test_ignores_document_status_blocks_before_shots(self) -> None:
        script = """故事板 已更新
项目名：测试片

分镜 1｜5 秒｜开场

图生视频（I2V）— 整段复制

镜头固定，雾气缓慢流动。

分镜 2｜10 秒｜转折

图生视频（I2V）— 整段复制

摄像机缓慢推近。
"""

        shots = split_shots_standard(script)

        self.assertEqual(len(shots), 2)
        self.assertEqual(shots[0][0], "1")
        self.assertEqual(shots[0][1], 5)
        self.assertIn("雾气缓慢流动", shots[0][2])

    def test_splits_bold_markdown_storyboard_headers(self) -> None:
        script = """### 第一幕：测试

**分镜 1｜8 秒｜小乐翻阅《史记》**

图生视频（I2V）— 整段复制

镜头从书架推近到书签。

---

**分镜 2｜6 秒｜穿越瞬间**

图生视频（I2V）— 整段复制

金光旋转，角色被吸入书页。
"""

        shots = split_shots_standard(script)

        self.assertEqual(len(shots), 2)
        self.assertEqual(shots[0][0], "1")
        self.assertEqual(shots[0][1], 8)
        self.assertIn("镜头从书架推近", shots[0][2])
        self.assertEqual(shots[1][0], "2")
        self.assertEqual(shots[1][1], 6)


if __name__ == "__main__":
    unittest.main()
