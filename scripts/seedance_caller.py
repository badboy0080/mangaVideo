# Backward-compat wrapper; see seedance_video.py
import os
import time

import seedance_video

SEEDANCE_ENDPOINT = os.environ.get(
    "SEEDANCE_ENDPOINT",
    "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks",
)
ARK_API_KEY = os.environ.get("ARK_API_KEY", "")


def call_seedance(
    video_prompt: str,
    reference_image_paths: list,
    output_dir: str,
    duration: int = 8,
    ratio: str = "16:9",
    max_wait_sec: int = 300,
    poll_interval: int = 10,
) -> dict:
    if not reference_image_paths:
        raise ValueError("reference_image_paths is required")

    out_name = f"seedance_{int(time.time())}.mp4"
    out_path = os.path.join(output_dir, out_name)

    path = seedance_video.generate_video_sync(
        video_prompt,
        reference_image_paths[:9],
        out_path,
        duration_ms=int(duration * 1000),
        ratio=ratio,
        max_wait_sec=max_wait_sec,
        poll_interval=poll_interval,
    )
    return {"video_path": path, "task_id": None}
