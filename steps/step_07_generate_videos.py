# Step 7: image-to-video via Volcengine Ark Seedance 2.0 (async task + poll + download).
# Docs: https://www.volcengine.com/docs/82379/1520757?lang=zh
import os
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import seedance_video


def _resolve_reference_paths(data: dict) -> list[str]:
    """新版本：reference_image_paths；兼容旧 artifact 的 first_frame_path + extra_ref_paths。"""
    paths = data.get("reference_image_paths")
    manual_paths = data.get("manual_reference_image_paths")
    if isinstance(paths, list) or isinstance(manual_paths, list):
        out: list[str] = []
        for p in (paths if isinstance(paths, list) else []):
            if p and str(p) not in out:
                out.append(str(p))
        for p in (manual_paths if isinstance(manual_paths, list) else []):
            if p and str(p) not in out:
                out.append(str(p))
        return out[:9]
    out: list[str] = []
    ff = data.get("first_frame_path") or ""
    if ff:
        out.append(str(ff))
    for p in data.get("extra_ref_paths") or []:
        if p and str(p) not in out:
            out.append(str(p))
    seen: set[str] = set()
    deduped: list[str] = []
    for p in out:
        if not p:
            continue
        try:
            k = os.path.abspath(p.replace("/", os.sep))
        except OSError:
            k = p
        if k in seen:
            continue
        seen.add(k)
        deduped.append(p)
        if len(deduped) >= 9:
            break
    return deduped


def run(conn, video_prompts: dict, out_dir: str, concurrency: int = 3) -> list:
    _ = conn
    os.makedirs(f"{out_dir}/videos", exist_ok=True)
    results = []
    pending = [(sid, data) for sid, data in video_prompts.items() if _resolve_reference_paths(data)]
    db_path = f"{out_dir}/assets.db"

    print(f"  Segments (Seedance 2.0): {len(pending)}, concurrency={concurrency}")

    def generate_one(shot_id: str, data: dict, idx: int, total: int):
        prompt = data["prompt"]
        ref_paths = _resolve_reference_paths(data)
        duration_ms = data.get("duration_ms")

        print(f"  [{idx}/{total}] task: {shot_id}")
        print(f"    reference_images ({len(ref_paths)}): {[os.path.basename(p) for p in ref_paths[:6]]}")

        output_path = f"{out_dir}/videos/{shot_id}.mp4"
        try:
            t0 = time.monotonic()
            seedance_video.generate_video_sync(
                prompt,
                ref_paths,
                output_path,
                duration_ms=duration_ms,
                max_wait_sec=900,
                poll_interval=5,
            )
            elapsed = time.monotonic() - t0
            from db import update_clip_path
            tconn = sqlite3.connect(db_path)
            try:
                update_clip_path(tconn, shot_id, output_path, "generated")
            finally:
                tconn.close()
            print(f"  [OK] {shot_id} -> {output_path} ({elapsed:.0f}s)")
            return shot_id, output_path
        except Exception as e:
            print(f"  [fail] {shot_id}: {e}")
            from db import update_clip_path
            tconn = sqlite3.connect(db_path)
            try:
                update_clip_path(tconn, shot_id, "", "failed")
            finally:
                tconn.close()
            return shot_id, None

    total = len(pending)
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(generate_one, sid, data, i + 1, total): (sid, data)
            for i, (sid, data) in enumerate(pending)
        }
        for future in as_completed(futures):
            shot_id, path = future.result()
            if path:
                results.append(path)

    print(f"  Video done: {len(results)}/{total} ok")
    return sorted(results)
