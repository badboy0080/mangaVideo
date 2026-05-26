# -*- coding: utf-8 -*-
"""Fail if web/src contains corrupted UI text (3+ consecutive question marks)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_SRC = ROOT / "web" / "src"

# Allow JS/TS operators: optional chaining, nullish coalescing (not 3+ ? in a row in strings)
CORRUPT = re.compile(r"\?{3,}")

def main() -> int:
    bad: list[str] = []
    for path in sorted(WEB_SRC.rglob("*")):
        if path.suffix not in {".tsx", ".ts", ".jsx", ".js"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            print(f"read error {path}: {e}", file=sys.stderr)
            return 2
        for i, line in enumerate(text.splitlines(), 1):
            if CORRUPT.search(line):
                bad.append(f"{path.relative_to(ROOT)}:{i}: {line.strip()[:100]}")

    if bad:
        print("Corrupted Chinese (???+) found in web/src:", file=sys.stderr)
        for item in bad:
            print(f"  {item}", file=sys.stderr)
        print("\nRun: python scripts/restore_app_chinese.py", file=sys.stderr)
        return 1

    print("OK: no ??? corruption in web/src")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
