#!/usr/bin/env python3
"""CLI entrypoint for the 5-step manga/video pipeline."""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from db import init as db_init, save_run


def run_step(name: str, module: str, func: str, *args, **kwargs):
    print(f"\n{'=' * 60}")
    print(f"  Step {name}")
    print(f"{'=' * 60}")
    try:
        mod = __import__(module, fromlist=[func])
        fn = getattr(mod, func)
        result = fn(*args, **kwargs)
        print(f"[OK] Step {name} complete")
        return result
    except Exception as e:
        print(f"[FAIL] Step {name}: {type(e).__name__}: {e}")
        raise RuntimeError(f"Step {name!r} failed; pipeline stopped") from e


def write_json(out_dir: str, filename: str, obj) -> None:
    with open(Path(out_dir) / filename, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manga/video generation pipeline")
    parser.add_argument("topic", help="Theme or creative concept")
    parser.add_argument("--duration", type=int, default=90, help="Target duration in seconds")
    parser.add_argument("--style", default="电影短片", help="Style preset")
    parser.add_argument("--output", default=None, help="Output directory")
    parser.add_argument("--img-concurrency", type=int, default=5, help="Image generation concurrency")
    parser.add_argument("--video-concurrency", type=int, default=3, help="Video generation concurrency")
    args = parser.parse_args()

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:4]
    out_dir = args.output or f"outputs/{run_id}"
    os.makedirs(f"{out_dir}/images", exist_ok=True)
    os.makedirs(f"{out_dir}/videos", exist_ok=True)

    db_path = f"{out_dir}/assets.db"
    conn = db_init(db_path)
    save_run(conn, run_id, args.topic, "")

    print(f"\n>>> Topic: {args.topic}")
    print(f">>> Target duration: {args.duration}s")
    print(f">>> Style: {args.style}")
    print(f">>> Output: {out_dir}")
    print(f">>> Run ID: {run_id}")

    script_brief = run_step(
        "01 - Script brief",
        "steps.step_01_research",
        "run",
        args.topic,
        duration_seconds=args.duration,
        style=args.style,
    )
    write_json(out_dir, "script_brief.json", script_brief)
    write_json(out_dir, "research.json", script_brief)

    storyboard = run_step(
        "02 - Storyboard and asset prompts",
        "steps.step_02_storyboard",
        "run",
        args.topic,
        script_brief,
        out_dir,
        target_duration=args.duration,
    )
    write_json(out_dir, "storyboard.json", storyboard)
    with open(Path(out_dir) / "script.md", "w", encoding="utf-8") as f:
        f.write(storyboard.get("script") or "")
    save_run(conn, run_id, args.topic, storyboard.get("script") or "")

    img_results = run_step(
        "03 - Generate assets",
        "steps.step_03_generate_assets",
        "run",
        conn,
        storyboard,
        out_dir,
        concurrency=args.img_concurrency,
    )
    write_json(out_dir, "img_results.json", img_results)

    video_bundle = run_step(
        "04 - Seedance 2.0 videos",
        "steps.step_04_generate_videos",
        "run",
        conn,
        storyboard,
        img_results,
        db_path,
        out_dir,
        concurrency=args.video_concurrency,
    )
    write_json(out_dir, "video_prompts.json", video_bundle.get("video_prompts") or {})
    write_json(out_dir, "video_results.json", video_bundle.get("video_results") or [])

    final_mp4 = run_step(
        "05 - Concat final video",
        "steps.step_08_concat",
        "run",
        conn,
        out_dir,
    )

    print(f"\n{'=' * 60}")
    print("  Pipeline complete")
    print(f"  Final video: {final_mp4}")
    print(f"  Output: {out_dir}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
