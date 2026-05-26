from __future__ import annotations

import os
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from steps.step_04_generate_videos import _merge_manual_refs  # noqa: E402
from steps.step_07_generate_videos import _resolve_reference_paths  # noqa: E402
from steps.step_06_video_prompts import (  # noqa: E402
    _build_image_alias_map,
    _build_token_display_map,
    _extract_dialogues,
    _inject_dialogues,
    _resolve_semantic_alias,
)


class TestStep04GenerateVideos(unittest.TestCase):
    def test_merge_manual_refs_preserves_existing_values(self) -> None:
        prompts = {"shot_01": {"prompt": "move", "reference_image_paths": ["a.png"]}}
        merged = _merge_manual_refs(prompts, {"shot_01": ["manual.png"]})
        self.assertEqual(merged["shot_01"]["manual_reference_image_paths"], ["manual.png"])

    def test_resolve_reference_paths_merges_dedupes_and_caps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for i in range(12):
                p = os.path.join(tmp, f"{i}.png")
                with open(p, "wb") as f:
                    f.write(b"x")
                paths.append(p)

            result = _resolve_reference_paths(
                {
                    "reference_image_paths": paths[:8],
                    "manual_reference_image_paths": [paths[1], *paths[8:12]],
                }
            )

        self.assertEqual(len(result), 9)
        self.assertEqual(result[0], paths[0])
        self.assertEqual(result[1], paths[1])
        self.assertEqual(result[-1], paths[8])

    def test_dialogue_cue_is_injected_into_prompt(self) -> None:
        token_map = _build_token_display_map(
            {"图片1": {"name": "小明", "tag": "character"}},
            {"characters": [{"name": "小明"}], "scenes": [], "props": []},
        )
        shot = """
| 项目 | 内容 |
|------|------|
| 台词 | @Xiao_Ming：原来这就是入木三分！ |
| 情绪效果 | 愉快、惊奇 |
"""
        dialogues = _extract_dialogues(shot, token_map)
        prompt = _inject_dialogues("摄像机缓慢推近。{原来这就是入木三分！} no music, no subtitles", dialogues)

        self.assertEqual(dialogues[0]["speaker"], "小明")
        self.assertIn("小明愉快的说“原来这就是入木三分！”", prompt)
        self.assertTrue(prompt.endswith("no music, no subtitles"))

    def test_image_alias_map_matches_pinyin_element_id(self) -> None:
        mapping = _build_image_alias_map(
            {"图片1": "xiao.png", "小明": "xiao.png", "图片2": "wang.png", "王羲之": "wang.png"},
            {
                "图片1": {"name": "小明", "tag": "character"},
                "图片2": {"name": "王羲之", "tag": "character"},
            },
            {"characters": [{"name": "小明"}, {"name": "王羲之"}], "scenes": [], "props": []},
        )

        self.assertEqual(mapping["Xiao_Ming"], "xiao.png")
        self.assertEqual(mapping["xiaoming"], "xiao.png")
        self.assertEqual(mapping["Wang_Xizhi"], "wang.png")

    def test_extracts_multiple_quoted_dialogues_from_single_row(self) -> None:
        token_map = _build_token_display_map(
            {
                "图片1": {"name": "小明", "tag": "character"},
                "图片2": {"name": "王羲之", "tag": "character"},
            },
            {"characters": [{"name": "小明"}, {"name": "王羲之"}], "scenes": [], "props": []},
        )
        shot = '| 台词 | 镜头1：@Wang_Xizhi 对白“日复一日。” 镜头2：@Xiao_Ming 对白“这水怎么是黑的？” |'

        dialogues = _extract_dialogues(shot, token_map)

        self.assertEqual([d["speaker"] for d in dialogues], ["王羲之", "小明"])
        self.assertEqual([d["line"] for d in dialogues], ["日复一日。", "这水怎么是黑的？"])

    def test_semantic_alias_matches_common_scene_element_id(self) -> None:
        mapping = {"现代书法教室": "classroom.png", "晋朝庭院": "courtyard.png"}
        catalog = {
            "characters": [],
            "scenes": [
                {"name": "现代书法教室", "description": "明亮教室，墙上挂满书法作品"},
                {"name": "晋朝庭院", "description": "青砖庭院，中央有石桌"},
            ],
            "props": [],
        }

        self.assertEqual(_resolve_semantic_alias("Modern_Classroom", mapping, catalog), "classroom.png")
        self.assertEqual(_resolve_semantic_alias("Ancient_Courtyard", mapping, catalog), "courtyard.png")


if __name__ == "__main__":
    unittest.main()
