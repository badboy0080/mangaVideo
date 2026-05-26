#!/usr/bin/env python3
"""按 web/asset-prompts.json 批量生成首页热门预设缩略图。"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from server.seedream_service import generate_ui_asset, status  # noqa: E402

PRESETS_JSON = ROOT / "web" / "asset-prompts.json"
OUT_DIR = ROOT / "web" / "public" / "presets"


def main() -> int:
    st = status()
    if not st["configured"]:
        print("错误：未配置 ARK_API_KEY / VOLCENGINE_API_KEY", file=sys.stderr)
        return 1

    data = json.loads(PRESETS_JSON.read_text(encoding="utf-8"))
    presets = data.get("presets") or []
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"模型: {st['model']}，共 {len(presets)} 张")
    ok = 0
    for i, item in enumerate(presets, 1):
        pid = item["id"]
        style = item.get("style", pid)
        prompt = item["prompt"]
        dest = OUT_DIR / f"{pid}.png"
        print(f"\n[{i}/{len(presets)}] {style} -> {dest.name}")
        try:
            result = generate_ui_asset(
                prompt,
                purpose=f"hot_preset_{style}",
                save_as=f"preset_{pid}",
            )
            shutil.copy2(result["path"], dest)
            print(f"  OK {dest.resolve()}")
            ok += 1
        except Exception as e:
            print(f"  失败: {e}", file=sys.stderr)

    print(f"\n完成: {ok}/{len(presets)}")
    return 0 if ok == len(presets) else 1


if __name__ == "__main__":
    raise SystemExit(main())
