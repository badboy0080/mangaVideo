"""Step 2: generate storyboard plus asset image prompts.

This is the new 5-step workflow facade. It reuses the battle-tested legacy
split steps internally, but exposes one artifact contract to the runner/UI.
"""
from __future__ import annotations

from typing import Any

from steps.step_02_script import run as run_script
from steps.step_03_extract_assets import run as extract_assets_fallback
from steps.step_04_prompts_img import run as build_asset_prompts


def run(topic: str, script_brief: dict, out_dir: str, target_duration: int = 90) -> dict[str, Any]:
    script_data = run_script(topic, script_brief, out_dir, target_duration=target_duration)
    script = script_data.get("script") or ""
    fallback_assets = extract_assets_fallback(script) if script else {}
    prompt_map = build_asset_prompts(fallback_assets, script, out_dir, script_brief)

    storyboard: dict[str, Any] = {
        "version": 1,
        "script": script,
        "script_path": script_data.get("script_path", ""),
        "shot_count": script_data.get("shots", 0),
        "assets": prompt_map.get("assets") or {},
        "shots": prompt_map.get("shots") or {},
        "asset_catalog": prompt_map.get("step4_asset_catalog")
        or {"characters": [], "scenes": [], "props": []},
        "prompt_map_version": prompt_map.get("version", 2),
        "inventory_source_hint": prompt_map.get("step4_inventory_source_hint", ""),
    }
    return storyboard


def to_prompt_map(storyboard: dict[str, Any]) -> dict[str, Any]:
    """Return the legacy prompt_map v2 shape consumed by asset generation."""
    return {
        "version": int(storyboard.get("prompt_map_version") or 2),
        "assets": storyboard.get("assets") or {},
        "shots": storyboard.get("shots") or {},
        "step4_asset_catalog": storyboard.get("asset_catalog")
        or {"characters": [], "scenes": [], "props": []},
        "step4_inventory_source_hint": storyboard.get("inventory_source_hint", ""),
    }


def to_script_data(storyboard: dict[str, Any]) -> dict[str, Any]:
    return {
        "script": storyboard.get("script") or "",
        "script_path": storyboard.get("script_path") or "",
        "shots": int(storyboard.get("shot_count") or len(storyboard.get("shots") or {})),
        "assets": storyboard.get("assets") or {},
        "asset_catalog": storyboard.get("asset_catalog")
        or {"characters": [], "scenes": [], "props": []},
    }
