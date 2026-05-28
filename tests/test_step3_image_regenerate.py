from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from db import ensure_image_row, init as db_init, update_image_path  # noqa: E402
from server import pipeline_runner  # noqa: E402
from steps.step_04_prompts_img import _catalog_to_prompt_rows, _normalize_catalog  # noqa: E402


class TestStep3ImageRegenerate(unittest.TestCase):
    def _make_run(self, tmp: str) -> Path:
        out = Path(tmp)
        (out / "images").mkdir(parents=True, exist_ok=True)
        state = pipeline_runner.new_run_state("test_run", tmp, "测试主题", 60, "电影短片", 1, 1)
        pipeline_runner.save_state(tmp, state)
        conn = db_init(str(out / "assets.db"))
        try:
            ensure_image_row(conn, "图片1", "character", "主角", "old prompt")
            img = out / "images" / "img_图片1.png"
            img.write_bytes(b"old image bytes")
            update_image_path(conn, "图片1", str(img), "generated")
        finally:
            conn.close()
        return out

    def test_step3_artifacts_include_image_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self._make_run(tmp)
            arts = pipeline_runner.get_step_artifacts(tmp, 3)

        self.assertEqual(len(arts["images"]), 1)
        self.assertEqual(arts["images"][0]["label"], "主角")
        self.assertEqual(arts["images"][0]["prompt"], "old prompt")
        self.assertEqual(arts["images"][0]["ref_id"], "图片1")

    def test_regenerate_step3_image_updates_prompt_and_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = self._make_run(tmp)
            img = out / "images" / "img_图片1.png"

            def fake_generate(prompt: str, dest: Path, **_: object) -> Path:
                dest.write_bytes(f"new:{prompt}".encode("utf-8"))
                return dest.resolve()

            with patch("steps.seedream_client.api_key", return_value="fake-key"):
                with patch("steps.seedream_client.generate_image", side_effect=fake_generate):
                    result = pipeline_runner.regenerate_step3_image(
                        tmp,
                        "images/img_图片1.png",
                        "new prompt",
                    )

            self.assertTrue(result["ok"])
            self.assertEqual(result["prompt"], "new prompt")
            self.assertEqual(img.read_bytes(), b"new:new prompt")

            conn = sqlite3.connect(str(out / "assets.db"))
            try:
                row = conn.execute("SELECT prompt, status FROM images WHERE id = ?", ("图片1",)).fetchone()
            finally:
                conn.close()
            self.assertEqual(row, ("new prompt", "generated"))

    def test_asset_catalog_ignores_props_for_generation(self) -> None:
        catalog = _normalize_catalog(
            {
                "characters": [{"name": "主角", "description": "蓝色外套"}],
                "scenes": [{"name": "老街", "description": "雨夜街道"}],
                "props": [{"name": "钥匙", "description": "黄铜钥匙"}],
            }
        )

        self.assertEqual(catalog["props"], [])
        self.assertEqual(catalog["total_props"], 0)

        rows = _catalog_to_prompt_rows(catalog)
        self.assertEqual([row["tag"] for row in rows], ["character", "scene"])
        self.assertNotIn("钥匙", [row["name"] for row in rows])


if __name__ == "__main__":
    unittest.main()
