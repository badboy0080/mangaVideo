# Volcengine Ark Seedance 2.0: create video task, poll status, download MP4.
# API docs: https://www.volcengine.com/docs/82379/1520757?lang=zh
# Auth: ARK_API_KEY or VOLCENGINE_API_KEY (same as other Ark calls).
from __future__ import annotations

import base64
import json
import os
import time
from typing import Any, List, Optional

import requests

DEFAULT_CREATE_URL = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"
# From Ark samples; plain doubao-seedance-2-0 often 404s on new accounts.
DEFAULT_MODEL = "doubao-seedance-2-0-260128"
_DURATION_MIN = 4
_DURATION_MAX = 15


def _api_key() -> str:
    return os.environ.get("ARK_API_KEY") or os.environ.get("VOLCENGINE_API_KEY", "")


def _create_url() -> str:
    return os.environ.get("SEEDANCE_ENDPOINT", DEFAULT_CREATE_URL).rstrip("/")


def _model_name() -> str:
    return os.environ.get("SEEDANCE_MODEL", DEFAULT_MODEL)


def _file_to_data_url(path: str) -> str:
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    if ext == "jpg":
        ext = "jpeg"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/{ext};base64,{data}"


def _build_content(prompt: str, reference_paths: List[str]) -> list:
    """Build Ark `content`: text + each ref as `reference_image` (max 9 files)."""
    content: list = [{"type": "text", "text": prompt}]
    seen: set[str] = set()
    paths: list[str] = []
    for p in reference_paths:
        if not p or not os.path.isfile(p):
            continue
        key = os.path.abspath(p)
        if key in seen:
            continue
        seen.add(key)
        paths.append(p)
        if len(paths) >= 9:
            break
    for p in paths:
        content.append({
            "type": "image_url",
            "image_url": {"url": _file_to_data_url(p)},
            "role": "reference_image",
        })
    return content


def _collect_valid_ref_paths(reference_paths: List[str], *, cap: int = 9) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for p in reference_paths:
        if not p or not os.path.isfile(p):
            continue
        k = os.path.abspath(p.replace("/", os.sep))
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
        if len(out) >= cap:
            break
    return out


def _is_privacy_real_person_create_error(status_code: int, body_text: str) -> bool:
    if status_code != 400:
        return False
    t = body_text or ""
    if "InputImageSensitiveContentDetected" in t and "PrivacyInformation" in t:
        return True
    if "may contain real person" in t.lower():
        return True
    try:
        data = json.loads(body_text)
        err = (data.get("error") or {}) if isinstance(data, dict) else {}
        code = str(err.get("code") or "")
        msg = str(err.get("message") or "")
        if "PrivacyInformation" in code or "real person" in msg.lower():
            return True
    except (json.JSONDecodeError, TypeError):
        pass
    return False


def _privacy_fallback_ref_sequences(paths: list[str]) -> list[list[str]]:
    """
    When the platform flags reference images as possible real-person photos,
    try progressively safer subsets (drop first ref is often the character sheet).
    """
    p = list(paths)
    seqs: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()

    def push(xs: list[str]) -> None:
        t = tuple(xs)
        if t in seen:
            return
        seen.add(t)
        seqs.append(list(t))

    if not p:
        push([])
        return seqs

    push(p)
    if len(p) >= 2:
        push(p[1:])
        push(p[:-1])
    if len(p) >= 1:
        push([p[-1]])
        push([p[0]])
    push([])
    return seqs


def _privacy_fallback_enabled() -> bool:
    v = (os.environ.get("SEEDANCE_PRIVACY_FALLBACK") or "1").strip().lower()
    return v not in ("0", "false", "no", "off")


_PRIVACY_FAIL_HINT_ZH = (
    "Volcengine/Seedance: reference images flagged as possible real-person photos (privacy).\n"
    "[??] ??? Step 4/5??????????????/??/3D ??????????????"
    "????? @ ?????????????????"
    "????????????????????????? SEEDANCE_PRIVACY_FALLBACK=1???????"
)


def _post_create_response(
    prompt: str,
    ref_paths: list[str],
    *,
    duration_ms: Optional[int],
    ratio: str,
    headers: dict,
    create_url: str,
) -> requests.Response:
    content = _build_content(prompt, ref_paths)
    payload: dict[str, Any] = {
        "model": _model_name(),
        "content": content,
        "generate_audio": True,
        "ratio": ratio,
        "watermark": False,
    }
    if duration_ms is not None:
        sec = int(round(duration_ms / 1000.0))
        payload["duration"] = max(_DURATION_MIN, min(_DURATION_MAX, sec))
    return requests.post(create_url, headers=headers, json=payload, timeout=120)


def _extract_task_id(task_data: dict) -> Optional[str]:
    tid = task_data.get("task_id") or task_data.get("id")
    if tid:
        return str(tid)
    inner = task_data.get("data")
    if isinstance(inner, dict):
        return str(inner.get("task_id") or inner.get("id") or "") or None
    return None


def _extract_video_url(status_data: dict[str, Any]) -> Optional[str]:
    def pick(d: dict) -> Optional[str]:
        for key in ("video_url", "url", "output_url", "video"):
            v = d.get(key)
            if isinstance(v, str) and v.startswith("http"):
                return v
        return None

    u = pick(status_data)
    if u:
        return u
    # Ark returns { "status": "succeeded", "content": { "video_url": "https://..." } }
    top_content = status_data.get("content")
    if isinstance(top_content, dict):
        u = pick(top_content)
        if u:
            return u
        nested = top_content.get("video_url")
        if isinstance(nested, dict) and isinstance(nested.get("url"), str):
            u2 = nested["url"]
            if u2.startswith("http"):
                return u2
    inner = status_data.get("data")
    if isinstance(inner, dict):
        u = pick(inner)
        if u:
            return u
        result = inner.get("result") or inner.get("output")
        if isinstance(result, dict):
            u = pick(result)
            if u:
                return u
            content = result.get("content") or result.get("video")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        u = pick(item)
                        if u:
                            return u
                        iu = item.get("image_url") or item.get("video_url")
                        if isinstance(iu, dict):
                            u = iu.get("url")
                            if isinstance(u, str) and u.startswith("http"):
                                return u
    return None


def _normalize_status(status_data: dict[str, Any]) -> str:
    s = status_data.get("status")
    if not s and isinstance(status_data.get("data"), dict):
        s = status_data["data"].get("status")
    if not s:
        return ""
    return str(s).lower()


def _download_video(url: str, dest: str) -> None:
    with requests.get(url, timeout=300, stream=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)


def _poll_and_download(
    *,
    create_url: str,
    task_id: str,
    output_mp4_path: str,
    headers: dict,
    max_wait_sec: int,
    poll_interval: int,
) -> str:
    status_url = f"{create_url}/{task_id}"
    print(f"  [Seedance] task_id={task_id} refs_ok, polling...")

    deadline = time.monotonic() + max_wait_sec
    last_status = ""

    while time.monotonic() < deadline:
        time.sleep(poll_interval)
        try:
            s_resp = requests.get(status_url, headers=headers, timeout=60)
        except requests.RequestException as exc:
            print(f"  [Seedance] poll error: {exc}, retry...")
            continue
        if not s_resp.ok:
            print(f"  [Seedance] poll HTTP {s_resp.status_code}, retry...")
            continue
        body = s_resp.json()
        st = _normalize_status(body)
        if st and st != last_status:
            print(f"  [Seedance] status={st}")
            last_status = st

        if st in ("succeed", "succeeded", "success", "completed"):
            video_url = _extract_video_url(body)
            if not video_url:
                raise RuntimeError(f"Seedance done but no video URL: {body}")
            _download_video(video_url, output_mp4_path)
            if not os.path.isfile(output_mp4_path) or os.path.getsize(output_mp4_path) < 1000:
                raise RuntimeError("Downloaded video missing or too small")
            return output_mp4_path

        if st in ("failed", "error", "cancelled", "canceled"):
            raise RuntimeError(f"Seedance task failed: {body}")

    raise TimeoutError(f"Seedance poll timeout {max_wait_sec}s task_id={task_id}")


def generate_video_sync(
    prompt: str,
    reference_image_paths: List[str],
    output_mp4_path: str,
    *,
    duration_ms: Optional[int] = None,
    ratio: str = "16:9",
    max_wait_sec: int = 900,
    poll_interval: int = 5,
) -> str:
    """
    POST create task, GET poll until terminal state, download file.
    Seedance 2.0: all images use role reference_image; at most 9 paths; prompts should mention @asset names where applicable.
    If create returns real-person / privacy error on reference images and SEEDANCE_PRIVACY_FALLBACK is enabled (default),
    retries with fewer reference images (drop first, single ref, text-only).
    Returns output_mp4_path on success.
    """
    key = _api_key()
    if not key:
        raise RuntimeError("Set ARK_API_KEY or VOLCENGINE_API_KEY for Seedance")

    create_url = _create_url()
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    parent = os.path.dirname(os.path.abspath(output_mp4_path))
    if parent:
        os.makedirs(parent, exist_ok=True)

    paths = _collect_valid_ref_paths(reference_image_paths)
    sequences = (
        _privacy_fallback_ref_sequences(paths)
        if _privacy_fallback_enabled()
        else [paths]
    )

    task_id: Optional[str] = None
    last_body = ""
    last_code = 0

    for attempt_i, refs in enumerate(sequences):
        resp = _post_create_response(
            prompt, refs, duration_ms=duration_ms, ratio=ratio, headers=headers, create_url=create_url
        )
        last_code = resp.status_code
        last_body = resp.text[:1200]
        if resp.ok:
            tid = _extract_task_id(resp.json())
            if tid:
                task_id = str(tid)
                if attempt_i > 0:
                    print(f"  [Seedance] create ok with {len(refs)} reference image(s) after fallback")
                break
            raise RuntimeError(f"Seedance response missing task_id: {resp.text[:800]}")
        can_retry = (
            _privacy_fallback_enabled()
            and _is_privacy_real_person_create_error(resp.status_code, resp.text)
            and attempt_i + 1 < len(sequences)
        )
        if can_retry:
            nnext = len(sequences[attempt_i + 1])
            print(
                f"  [Seedance] reference image privacy/real-person check (HTTP {resp.status_code}), "
                f"retrying with {nnext} image(s)..."
            )
            continue
        detail = f"Seedance create task HTTP {resp.status_code}: {last_body}"
        if _is_privacy_real_person_create_error(resp.status_code, resp.text):
            detail = f"{detail}\n{_PRIVACY_FAIL_HINT_ZH}"
        raise RuntimeError(detail)

    if not task_id:
        msg = f"Seedance create failed HTTP {last_code}: {last_body}"
        if _is_privacy_real_person_create_error(last_code, last_body):
            msg = f"{msg}\n{_PRIVACY_FAIL_HINT_ZH}"
        raise RuntimeError(msg)

    return _poll_and_download(
        create_url=create_url,
        task_id=task_id,
        output_mp4_path=output_mp4_path,
        headers=headers,
        max_wait_sec=max_wait_sec,
        poll_interval=poll_interval,
    )
