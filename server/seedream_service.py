"""
Web / 助手即时生图：落盘到 outputs/_ui_assets，供 API 与脚本共用。
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from server.pipeline_runner import PROJECT_ROOT
from steps.seedream_client import (
    DEFAULT_SEEDREAM_MODEL,
    generate_image,
    is_configured,
    new_asset_id,
    safe_filename_stem,
    seedream_model,
)

UI_ASSETS_REL = "outputs/_ui_assets"
MANIFEST_NAME = "manifest.jsonl"


def ui_assets_dir() -> Path:
    d = PROJECT_ROOT / UI_ASSETS_REL
    d.mkdir(parents=True, exist_ok=True)
    return d


def manifest_path() -> Path:
    return ui_assets_dir() / MANIFEST_NAME


def append_manifest(entry: dict[str, Any]) -> None:
    entry.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    with open(manifest_path(), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def safe_ui_asset_file(filename: str) -> Path:
    name = filename.replace("\\", "/").strip()
    if not name or "/" in name or name.startswith("."):
        raise ValueError("invalid filename")
    base = ui_assets_dir().resolve()
    candidate = (base / name).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as e:
        raise ValueError("path escape") from e
    return candidate


def status() -> dict[str, Any]:
    return {
        "configured": is_configured(),
        "model": seedream_model(),
        "default_model": DEFAULT_SEEDREAM_MODEL,
        "assets_dir": str(ui_assets_dir().resolve()),
    }


def generate_ui_asset(
    prompt: str,
    *,
    purpose: str = "",
    save_as: str = "",
    reference_paths: list[str] | None = None,
    size: str = "2K",
) -> dict[str, Any]:
    asset_id = new_asset_id("ui")
    if save_as:
        stem = safe_filename_stem(save_as)
        filename = f"{stem}.png"
    else:
        filename = f"{asset_id}.png"

    dest = ui_assets_dir() / filename
    refs: list[str] = []
    if reference_paths:
        for raw in reference_paths:
            p = Path(raw)
            if not p.is_absolute():
                p = (PROJECT_ROOT / raw).resolve()
            if p.is_file():
                refs.append(str(p))

    written = generate_image(
        prompt,
        dest,
        image_inputs=refs or None,
        size=size,
    )

    rel = f"{UI_ASSETS_REL}/{written.name}".replace("\\", "/")
    entry = {
        "asset_id": asset_id,
        "filename": written.name,
        "rel_path": rel,
        "purpose": purpose.strip(),
        "prompt": prompt[:2000],
        "model": seedream_model(),
    }
    append_manifest(entry)

    return {
        "ok": True,
        "asset_id": asset_id,
        "filename": written.name,
        "rel_path": rel,
        "path": str(written),
        "purpose": purpose,
        "model": seedream_model(),
        "url": f"/api/ui-assets/{written.name}",
    }
