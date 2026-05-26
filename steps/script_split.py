"""
从 Step 02 输出的 script.md / script 正文里拆分「分镜 N｜X 秒」块。

旧的 DOTALL + 惰性匹配在遇到「幕标题、说明段」夹在两个分镜之间时会匹配失败，
导致只剩一条超大的 shot_01。这里改为按「行首分镜标题」定位切片，数量与 Step 2 对齐。
"""

from __future__ import annotations

import re


# 整行均为分镜标题：分镜 N｜X秒｜第三段可有可无；允许模型加 Markdown 标题前缀。
_SHOT_HDR = re.compile(
    r"(?m)^[^\S\r\n]*(?:#{1,6}[^\S\r\n]*)?分镜\s*(\d+)\s*[｜|]\s*(\d+)\s*秒[^\r\n]*$",
)


def split_shots_by_headers(script: str) -> list[tuple[str, int | None, str]]:
    """
    返回 [(镜号字符串, 标题秒数(int 或 clamp 前已由调用方处理), 该镜正文), ...]

    - 若在全文找不到任何匹配，返回 []（由调用方再走 legacy）。
    """
    spans: list[tuple[int, int, str, str]] = []
    for m in _SHOT_HDR.finditer(script):
        spans.append((m.start(), m.end(), m.group(1), m.group(2)))

    if not spans:
        return []

    out: list[tuple[str, int | None, str]] = []
    for i, (_start_hdr, end_hdr, sn, secs) in enumerate(spans):
        start_body = end_hdr
        end_body = spans[i + 1][0] if i + 1 < len(spans) else len(script)
        body = script[start_body:end_body].strip()
        try:
            sec_i = max(1, int(secs))
        except ValueError:
            sec_i = None
        out.append((sn.strip(), sec_i, body))

    return out


def split_shots_legacy(script: str) -> list[tuple[str, int | None, str]]:
    """与原 step_06 相同的后备：整段正则 + ## 镜头。"""
    pattern = re.compile(
        r"(?:^|\n)\s*(?:#{1,6}\s*)?分镜\s*(\d+)\s*[｜|]\s*(\d+)\s*秒\s*[｜|]?\s*(.+?)(?=\n\s*(?:#{1,6}\s*)?分镜\s*\d+\s*[｜|]|\Z)",
        re.DOTALL,
    )
    matches = pattern.findall(script)
    if matches:
        out: list[tuple[str, int | None, str]] = []
        for sn, secs, body in matches:
            try:
                s = max(1, int(secs))
            except ValueError:
                s = None
            out.append((sn.strip(), s, body.strip()))
        return out
    pattern2 = re.compile(r"##\s*镜头\s*(\d+)\s*\r?\n(.+?)(?=##\s*镜头|\Z)", re.DOTALL)
    matches2 = pattern2.findall(script)
    return [(m[0].strip(), None, m[1].strip()) for m in matches2]


def split_shots_standard(script: str) -> list[tuple[str, int | None, str]]:
    """
    首选按行首分镜标题切块；若没有标题行则用 legacy。"""
    out = split_shots_by_headers(script)
    return out if out else split_shots_legacy(script)
