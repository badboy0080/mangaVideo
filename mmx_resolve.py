"""?? MiniMax CLI?mmx??????????? PATH????? node_modules/.bin?"""
from __future__ import annotations

import shutil
from pathlib import Path

_ROOT = Path(__file__).resolve().parent


def mmx_executable() -> str:
    w = shutil.which("mmx")
    if w:
        return w
    bindir = _ROOT / "node_modules" / ".bin"
    for name in ("mmx.cmd", "mmx.exe", "mmx"):
        p = bindir / name
        if p.is_file():
            return str(p)
    return "mmx"
