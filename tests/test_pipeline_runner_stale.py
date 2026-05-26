from __future__ import annotations

import json
import os
import shutil
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from server.pipeline_runner import PROJECT_ROOT, _mark_stale_running_steps  # noqa: E402


class TestPipelineRunnerStale(unittest.TestCase):
    def tearDown(self) -> None:
        shutil.rmtree(PROJECT_ROOT / "outputs" / "test_live_marker_running_step", ignore_errors=True)

    def test_stale_running_step_is_cancelled_without_live_lock(self) -> None:
        state = {
            "out_dir": "outputs/test_stale_running_step",
            "steps": {
                "1": {"status": "success", "error": None, "updated_at": None},
                "2": {"status": "running", "error": None, "updated_at": None},
            },
            "last_global_error": None,
        }

        changed = _mark_stale_running_steps(state)

        self.assertTrue(changed)
        self.assertEqual(state["steps"]["2"]["status"], "cancelled")
        self.assertIn("Backend was stopped", state["steps"]["2"]["error"])
        self.assertIn("Previous running step", state["last_global_error"])

    def test_live_marker_keeps_running_step_active_without_memory_lock(self) -> None:
        out_dir = PROJECT_ROOT / "outputs" / "test_live_marker_running_step"
        out_dir.mkdir(parents=True, exist_ok=True)
        marker = {
            "pid": os.getpid(),
            "step": 3,
            "mode": "step",
            "started_at": "2026-05-25T00:00:00Z",
        }
        (out_dir / ".pipeline_active.json").write_text(json.dumps(marker), encoding="utf-8")
        state = {
            "out_dir": "outputs/test_live_marker_running_step",
            "steps": {
                "1": {"status": "success", "error": None, "updated_at": None},
                "2": {"status": "success", "error": None, "updated_at": None},
                "3": {"status": "running", "error": None, "updated_at": None},
            },
            "last_global_error": None,
        }

        changed = _mark_stale_running_steps(state)

        self.assertFalse(changed)
        self.assertEqual(state["steps"]["3"]["status"], "running")
        self.assertIsNone(state["steps"]["3"]["error"])


if __name__ == "__main__":
    unittest.main()
