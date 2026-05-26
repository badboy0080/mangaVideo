"""Step 4: build Seedance prompts and generate video segments."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from steps.step_02_storyboard import to_script_data
from steps.step_06_video_prompts import run as build_video_prompts
from steps.step_07_generate_videos import run as generate_videos


def _resolve_out_dir(out_dir: str) -> Path:
    p = Path(out_dir)
    if not p.is_absolute():
        p = Path(__file__).resolve().parent.parent / out_dir
    return p


def _read_existing_manual_refs(out_dir: str) -> dict[str, list[str]]:
    path = _resolve_out_dir(out_dir) / "video_prompts.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[str, list[str]] = {}
    for shot_id, row in data.items():
        if not isinstance(row, dict):
            continue
        refs = row.get("manual_reference_image_paths")
        if isinstance(refs, list):
            clean = [str(x) for x in refs if str(x).strip()]
            if clean:
                out[str(shot_id)] = clean
    return out


def _merge_manual_refs(video_prompts: dict[str, Any], manual_refs: dict[str, list[str]]) -> dict[str, Any]:
    for shot_id, row in video_prompts.items():
        if not isinstance(row, dict):
            continue
        existing_manual = row.get("manual_reference_image_paths")
        if not isinstance(existing_manual, list):
            existing_manual = []
        manual = manual_refs.get(shot_id, existing_manual)
        row["manual_reference_image_paths"] = [str(x) for x in manual if str(x).strip()]
    return video_prompts


def run(
    conn,
    storyboard: dict[str, Any],
    img_results: dict[str, str],
    db_path: str,
    out_dir: str,
    concurrency: int = 3,
) -> dict[str, Any]:
    _ = conn
    manual_refs = _read_existing_manual_refs(out_dir)
    video_prompts = build_video_prompts(to_script_data(storyboard), img_results, db_path, out_dir)
    video_prompts = _merge_manual_refs(video_prompts, manual_refs)

    tconn = sqlite3.connect(db_path)
    try:
        video_results = generate_videos(tconn, video_prompts, out_dir, concurrency=concurrency)
    finally:
        tconn.close()

    return {"video_prompts": video_prompts, "video_results": video_results}
