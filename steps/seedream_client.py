"""
火山引擎 Ark — Seedream 文生图 / 图生图客户端。

默认模型：Seedream 4.5（`doubao-seedream-4-5-251128`）。
可通过环境变量 `SEEDREAM_MODEL` 覆盖；流水线 Step 5 与 Web 即时生图共用本模块。
"""
from __future__ import annotations

import base64
import os
import re
import uuid
from pathlib import Path

import requests

SEEDREAM_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
DEFAULT_SEEDREAM_MODEL = "doubao-seedream-4-5-251128"
DEFAULT_SIZE = "2K"


def seedream_model() -> str:
    return os.environ.get("SEEDREAM_MODEL", DEFAULT_SEEDREAM_MODEL).strip() or DEFAULT_SEEDREAM_MODEL


def api_key() -> str:
    k = os.environ.get("VOLCENGINE_API_KEY", os.environ.get("ARK_API_KEY", "")).strip()
    if not k:
        raise RuntimeError("请设置 VOLCENGINE_API_KEY 或 ARK_API_KEY 环境变量")
    return k


def is_configured() -> bool:
    return bool(os.environ.get("VOLCENGINE_API_KEY", os.environ.get("ARK_API_KEY", "")).strip())


def local_image_to_api_field(path: str | Path) -> str:
    p = Path(path)
    raw = p.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    suf = p.suffix.lower()
    mime = "image/png" if suf == ".png" else "image/jpeg"
    return f"data:{mime};base64,{b64}"


def download_image(url: str, dest: Path, key: str) -> None:
    headers = {"Authorization": f"Bearer {key}"}
    r = requests.get(url, headers=headers, timeout=120)
    if r.status_code >= 400:
        r = requests.get(url, timeout=120)
    r.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)


def safe_filename_stem(name: str, *, max_len: int = 80) -> str:
    stem = re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", name.strip(), flags=re.UNICODE)
    stem = stem.strip("_") or "asset"
    return stem[:max_len]


def generate_image(
    prompt: str,
    dest: Path,
    *,
    image_inputs: list[str | Path] | None = None,
    model: str | None = None,
    size: str = DEFAULT_SIZE,
    api_key_override: str | None = None,
) -> Path:
    """
    调用 Seedream 生成一张图并写入 dest（.png）。
    返回写入后的绝对路径。
    """
    prompt = prompt.strip()
    if not prompt:
        raise ValueError("prompt 不能为空")

    key = api_key_override or api_key()
    use_model = (model or seedream_model()).strip()

    payload: dict = {
        "model": use_model,
        "prompt": prompt,
        "sequential_image_generation": "disabled",
        "response_format": "url",
        "size": size,
        "stream": False,
        "watermark": False,
    }

    if image_inputs:
        fields = [
            local_image_to_api_field(p)
            for p in image_inputs
            if p and Path(p).is_file()
        ]
        if not fields:
            raise RuntimeError("图生图但参考图路径无效")
        payload["image"] = fields if len(fields) > 1 else fields[0]

    r = requests.post(
        SEEDREAM_ENDPOINT,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload,
        timeout=180,
    )
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(str(data["error"]))
    img_url = data["data"][0]["url"]

    dest = dest.with_suffix(".png")
    download_image(img_url, dest, key)
    if not dest.is_file() or dest.stat().st_size < 1000:
        raise RuntimeError("图片下载失败或文件过小")
    return dest.resolve()


def new_asset_id(prefix: str = "img") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"
