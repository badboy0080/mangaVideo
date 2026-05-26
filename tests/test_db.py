"""
??????????unittest?Python ????????????????
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

# ????????? import db
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import db  # noqa: E402


class TestDb(unittest.TestCase):
    """?? SQLite ??????????"""

    def setUp(self) -> None:
        self._prev_db_path = db.DB_PATH
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmpdir.name, "test_assets.db")
        self.conn = db.init(self.db_path)

    def tearDown(self) -> None:
        self.conn.close()
        self._tmpdir.cleanup()
        db.DB_PATH = self._prev_db_path

    def test_init_creates_runs_table_and_save_run_roundtrip(self) -> None:
        """???????? runs ??????????"""
        run_id = "run_test_001"
        topic = "????"
        script = "# ??\n- ??1"
        db.save_run(self.conn, run_id, topic, script)

        row = self.conn.execute(
            "SELECT id, topic, script FROM runs WHERE id = ?", (run_id,)
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], run_id)
        self.assertEqual(row[1], topic)
        self.assertEqual(row[2], script)

    def test_insert_image_updates_and_get_by_name(self) -> None:
        """????????????????????"""
        img_id = db.insert_image(self.conn, "character", "??", "prompt text")
        self.assertTrue(img_id.startswith("img_"))

        db.update_image_path(self.conn, img_id, "/fake/path.png", "generated")
        row = db.get_image_by_name(self.conn, "??")
        self.assertIsNotNone(row)
        self.assertEqual(row[0], img_id)
        self.assertEqual(row[1], "/fake/path.png")
        self.assertEqual(row[2], "character")


if __name__ == "__main__":
    unittest.main()
