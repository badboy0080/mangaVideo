#!/usr/bin/env python3
"""
用 Seedream 4.5 生成单张图片（供 Cursor 助手或本地调试）。

示例：
  python scripts/seedream_generate.py --prompt "2.5D kids comic, yellow hoodie child, white background"
  python scripts/seedream_generate.py --prompt "..." --purpose hot_preset_电影短片 --save-as preset_movie
  python scripts/seedream_generate.py --prompt "..." --copy-to web/public/presets/movie.png
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from server.seedream_service import generate_ui_asset, status  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Seedream 4.5 单张生图")
    p.add_argument("--prompt", required=True, help="英文或中文提示词")
    p.add_argument("--purpose", default="", help="用途标记，写入 manifest")
    p.add_argument("--save-as", default="", help="文件名主干（不含扩展名）")
    p.add_argument("--copy-to", default="", help="生成后复制到该路径（如 web/public/presets/x.png）")
    p.add_argument("--size", default="2K", help="尺寸，默认 2K")
    args = p.parse_args()

    st = status()
    if not st["configured"]:
        print("错误：未配置 VOLCENGINE_API_KEY 或 ARK_API_KEY", file=sys.stderr)
        return 1

    print(f"模型: {st['model']}")
    try:
        result = generate_ui_asset(
            args.prompt,
            purpose=args.purpose,
            save_as=args.save_as,
            size=args.size,
        )
    except Exception as e:
        print(f"生图失败: {e}", file=sys.stderr)
        return 1

    print(f"已保存: {result['path']}")
    print(f"预览 URL（需 API 运行）: {result['url']}")

    if args.copy_to:
        dest = Path(args.copy_to)
        if not dest.is_absolute():
            dest = ROOT / dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(result["path"], dest)
        print(f"已复制到: {dest.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
