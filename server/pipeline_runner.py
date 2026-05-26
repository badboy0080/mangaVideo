"""Pipeline step runner and UI state for the 5-step workflow."""
from __future__ import annotations

import contextlib
import json
import os
import shutil
import sqlite3
import sys
import threading
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, TextIO

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

STATE_FILENAME = "pipeline_ui_state.json"
TRASH_DIRNAME = "_trash"
ACTIVE_MARKER_FILENAME = ".pipeline_active.json"

STEP_LABELS: list[tuple[int, str, str, str]] = [
    (1, "script_brief", "剧本", "steps.step_01_research"),
    (2, "storyboard", "分镜", "steps.step_02_storyboard"),
    (3, "gen_assets", "资产", "steps.step_03_generate_assets"),
    (4, "gen_videos", "视频", "steps.step_04_generate_videos"),
    (5, "concat", "成片", "steps.step_08_concat"),
]
STEP_COUNT = len(STEP_LABELS)

_run_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()
_cancel_events: dict[str, threading.Event] = {}
_cancel_guard = threading.Lock()
_capture_io_lock = threading.Lock()


class _TeeIO:
    __slots__ = ("_streams",)

    def __init__(self, *streams: TextIO):
        self._streams = streams

    def write(self, data: str) -> int:
        for s in self._streams:
            s.write(data)
        return len(data) if isinstance(data, str) else 0

    def flush(self) -> None:
        for s in self._streams:
            s.flush()


def _run_lock(key: str) -> threading.Lock:
    with _locks_guard:
        if key not in _run_locks:
            _run_locks[key] = threading.Lock()
        return _run_locks[key]


def _run_lock_is_held(out_dir: str) -> bool:
    key = _cancel_key(out_dir)
    with _locks_guard:
        lk = _run_locks.get(key)
    return bool(lk and lk.locked())


def _active_marker_path(out_dir: str) -> Path:
    return resolve_out_dir(out_dir) / ACTIVE_MARKER_FILENAME


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _write_active_marker(out_dir: str, step: int | None, mode: str) -> None:
    marker = {
        "pid": os.getpid(),
        "step": step,
        "mode": mode,
        "started_at": datetime.utcnow().isoformat() + "Z",
    }
    path = _active_marker_path(out_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(marker, ensure_ascii=False, indent=2), encoding="utf-8")


def _clear_active_marker(out_dir: str) -> None:
    try:
        _active_marker_path(out_dir).unlink()
    except FileNotFoundError:
        pass


def _active_marker_is_live(out_dir: str) -> bool:
    path = _active_marker_path(out_dir)
    if not path.is_file():
        return False
    try:
        marker = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _clear_active_marker(out_dir)
        return False
    pid = marker.get("pid")
    if isinstance(pid, int) and _pid_is_alive(pid):
        return True
    _clear_active_marker(out_dir)
    return False


def _mark_stale_running_steps(state: dict[str, Any]) -> bool:
    """Cancel stale running states left behind by a stopped backend process."""
    out_dir = str(state.get("out_dir") or "")
    if not out_dir or _run_lock_is_held(out_dir) or _active_marker_is_live(out_dir):
        return False

    changed = False
    now = datetime.utcnow().isoformat() + "Z"
    for row in (state.get("steps") or {}).values():
        if isinstance(row, dict) and row.get("status") == "running":
            row["status"] = "cancelled"
            row["error"] = "Backend was stopped before this step finished. Rerun this step to continue."
            row["updated_at"] = now
            changed = True
    if changed:
        state["last_global_error"] = "Previous running step was cancelled because the backend stopped."
        state.pop("stop_requested", None)
    return changed


def resolve_out_dir(out_dir: str) -> Path:
    p = Path(out_dir)
    return p if p.is_absolute() else PROJECT_ROOT / p


def _cancel_key(out_dir: str) -> str:
    return resolve_out_dir(out_dir).as_posix()


def _cancel_event(out_dir: str) -> threading.Event:
    key = _cancel_key(out_dir)
    with _cancel_guard:
        if key not in _cancel_events:
            _cancel_events[key] = threading.Event()
        return _cancel_events[key]


def state_path(out_dir: str) -> Path:
    return resolve_out_dir(out_dir) / STATE_FILENAME


def load_state(out_dir: str) -> dict[str, Any]:
    sp = state_path(out_dir)
    if not sp.is_file():
        raise FileNotFoundError(str(sp))
    with open(sp, encoding="utf-8") as f:
        return json.load(f)


def save_state(out_dir: str, state: dict[str, Any]) -> None:
    d = resolve_out_dir(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    with open(d / STATE_FILENAME, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _write_json(d: Path, name: str, obj: Any) -> None:
    d.mkdir(parents=True, exist_ok=True)
    with open(d / name, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _read_json(d: Path, name: str) -> Any:
    with open(d / name, encoding="utf-8") as f:
        return json.load(f)


def ensure_directories(out_dir: str) -> Path:
    d = resolve_out_dir(out_dir)
    (d / "images").mkdir(parents=True, exist_ok=True)
    (d / "videos").mkdir(parents=True, exist_ok=True)
    return d


def new_run_state(
    run_id: str,
    out_dir: str,
    topic: str,
    duration: int,
    style: str,
    img_concurrency: int,
    video_concurrency: int,
) -> dict[str, Any]:
    now = datetime.utcnow().isoformat() + "Z"
    return {
        "run_id": run_id,
        "out_dir": out_dir.replace("\\", "/"),
        "topic": topic,
        "duration": duration,
        "style": style,
        "img_concurrency": img_concurrency,
        "video_concurrency": video_concurrency,
        "created_at": now,
        "steps": {
            str(i): {
                "key": key,
                "title": title,
                "status": "pending",
                "error": None,
                "updated_at": None,
            }
            for i, key, title, _ in STEP_LABELS
        },
        "last_global_error": None,
    }


def init_run(
    topic: str,
    duration: int = 90,
    style: str = "电影短片",
    img_concurrency: int = 5,
    video_concurrency: int = 3,
) -> dict[str, Any]:
    from db import init as db_init, save_run
    from steps.step_01_research import validate_style

    os.chdir(PROJECT_ROOT)
    style_key = validate_style(style.strip() or "电影短片")
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:4]
    rel = f"outputs/{run_id}"
    ensure_directories(rel)
    conn = db_init(f"{rel}/assets.db")
    try:
        save_run(conn, run_id, topic, "")
    finally:
        conn.close()
    state = new_run_state(run_id, rel, topic, duration, style_key, img_concurrency, video_concurrency)
    save_state(rel, state)
    return state


def clear_cancel(out_dir: str) -> None:
    _cancel_event(out_dir).clear()
    try:
        state = load_state(out_dir)
    except FileNotFoundError:
        return
    if state.pop("stop_requested", None):
        save_state(out_dir, state)


def is_stop_requested(out_dir: str) -> bool:
    return _cancel_event(out_dir).is_set()


def request_stop(out_dir: str) -> dict[str, Any]:
    _cancel_event(out_dir).set()
    try:
        state = load_state(out_dir)
    except FileNotFoundError:
        return {"run_id": Path(out_dir).name, "stop_requested": True, "cancelled_steps": []}
    now = datetime.utcnow().isoformat() + "Z"
    cancelled: list[str] = []
    for sid, row in (state.get("steps") or {}).items():
        if isinstance(row, dict) and row.get("status") == "running":
            row["status"] = "cancelled"
            row["error"] = "User requested stop"
            row["updated_at"] = now
            cancelled.append(sid)
    state["stop_requested"] = True
    if cancelled:
        state["last_global_error"] = "User requested stop"
    save_state(out_dir, state)
    return {"run_id": state.get("run_id"), "stop_requested": True, "cancelled_steps": cancelled}


def _is_reserved_output_dir(name: str) -> bool:
    return name.startswith("_") or name.startswith(".")


def delete_run(run_id: str, *, wait_lock_sec: float = 45.0) -> dict[str, Any]:
    out_dir = f"outputs/{run_id}"
    d = resolve_out_dir(out_dir)
    if not d.is_dir():
        raise FileNotFoundError(run_id)
    request_stop(out_dir)
    key = _cancel_key(out_dir)
    lk = _run_lock(key)
    if not lk.acquire(timeout=max(0.5, wait_lock_sec)):
        raise RuntimeError("Run is still busy; try again later")
    try:
        trash_root = PROJECT_ROOT / "outputs" / TRASH_DIRNAME
        trash_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        dest = trash_root / f"{run_id}_{stamp}"
        if dest.exists():
            dest = trash_root / f"{run_id}_{stamp}_{uuid.uuid4().hex[:6]}"
        shutil.move(str(d), str(dest))
        with _cancel_guard:
            _cancel_events.pop(key, None)
        return {"run_id": run_id, "deleted": True, "trash_path": str(dest.relative_to(PROJECT_ROOT)).replace("\\", "/")}
    finally:
        lk.release()


def _step_ok(state: dict[str, Any], n: int) -> bool:
    return state["steps"].get(str(n), {}).get("status") == "success"


def _require_steps(state: dict[str, Any], required: list[int]) -> None:
    missing = [str(x) for x in required if not _step_ok(state, x)]
    if missing:
        raise RuntimeError(f"Complete steps first: {', '.join(missing)}")


def preflight_run_step(out_dir: str, step: int, force: bool) -> None:
    state = load_state(out_dir)
    if _mark_stale_running_steps(state):
        save_state(out_dir, state)
    if step < 1 or step > STEP_COUNT:
        raise ValueError(f"step must be 1-{STEP_COUNT}")
    cur = state["steps"].get(str(step), {})
    if cur.get("status") == "running":
        raise RuntimeError("Step is already running")
    if cur.get("status") == "success" and not force:
        raise RuntimeError("Step already success; pass force=true to redo")
    _require_steps(state, list(range(1, step)))


def _mark_step(state: dict[str, Any], out_dir: str, step: int, status: str, error: str | None = None) -> None:
    row = state["steps"][str(step)]
    row["status"] = status
    row["error"] = error
    row["updated_at"] = datetime.utcnow().isoformat() + "Z"
    state["last_global_error"] = error if error else None
    save_state(out_dir, state)


def execute_step(out_dir: str, step: int, *, force: bool = False) -> dict[str, Any]:
    os.chdir(PROJECT_ROOT)
    state = load_state(out_dir)
    if step < 1 or step > STEP_COUNT:
        raise ValueError(f"step must be 1-{STEP_COUNT}")
    cur = state["steps"][str(step)]
    if cur["status"] == "running":
        raise RuntimeError("Step is already running")
    if cur["status"] == "success" and not force:
        raise RuntimeError("Step already success; pass force=true to redo")
    if is_stop_requested(out_dir):
        _mark_step(state, out_dir, step, "cancelled", "User requested stop")
        return load_state(out_dir)

    d = resolve_out_dir(out_dir)
    d_out = str(d).replace("\\", "/")
    db_path = str(d / "assets.db")
    log_path = d / "logs" / f"step_{step}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    _mark_step(state, out_dir, step, "running")
    state = load_state(out_dir)

    try:
        with _capture_io_lock:
            with open(log_path, "w", encoding="utf-8") as logf:
                tee_out = _TeeIO(sys.__stdout__, logf)
                tee_err = _TeeIO(sys.__stderr__, logf)
                with contextlib.redirect_stdout(tee_out), contextlib.redirect_stderr(tee_err):
                    try:
                        if step == 1:
                            from steps.step_01_research import run as s1

                            brief = s1(state["topic"], duration_seconds=int(state.get("duration") or 90), style=state.get("style") or "电影短片")
                            _write_json(d, "script_brief.json", brief)
                            _write_json(d, "research.json", brief)
                        elif step == 2:
                            _require_steps(state, [1])
                            from db import init as db_init, save_run
                            from steps.step_02_storyboard import run as s2

                            brief = _read_json(d, "script_brief.json")
                            storyboard = s2(state["topic"], brief, d_out, target_duration=int(state.get("duration") or 90))
                            _write_json(d, "storyboard.json", storyboard)
                            (d / "script.md").write_text(storyboard.get("script") or "", encoding="utf-8")
                            conn = db_init(db_path)
                            try:
                                save_run(conn, state["run_id"], state["topic"], storyboard.get("script") or "")
                            finally:
                                conn.close()
                        elif step == 3:
                            _require_steps(state, [2])
                            from steps.step_03_generate_assets import run as s3

                            storyboard = _read_json(d, "storyboard.json")
                            conn = sqlite3.connect(db_path)
                            try:
                                img_results = s3(conn, storyboard, d_out, concurrency=int(state.get("img_concurrency") or 5))
                            finally:
                                conn.close()
                            _write_json(d, "img_results.json", img_results)
                        elif step == 4:
                            _require_steps(state, [3])
                            from steps.step_04_generate_videos import run as s4

                            storyboard = _read_json(d, "storyboard.json")
                            img_results = _read_json(d, "img_results.json")
                            conn = sqlite3.connect(db_path)
                            try:
                                bundle = s4(conn, storyboard, img_results, db_path, d_out, concurrency=int(state.get("video_concurrency") or 3))
                            finally:
                                conn.close()
                            _write_json(d, "video_prompts.json", bundle.get("video_prompts") or {})
                            _write_json(d, "video_results.json", bundle.get("video_results") or [])
                        elif step == 5:
                            _require_steps(state, [4])
                            from steps.step_08_concat import run as s5

                            conn = sqlite3.connect(db_path)
                            try:
                                final_mp4 = s5(conn, d_out)
                            finally:
                                conn.close()
                            state["final_mp4"] = final_mp4.replace("\\", "/")
                            save_state(out_dir, state)
                    except Exception:
                        traceback.print_exc()
                        raise
        if is_stop_requested(out_dir):
            _mark_step(state, out_dir, step, "cancelled", "User requested stop")
        else:
            _mark_step(state, out_dir, step, "success")
    except Exception as e:
        _mark_step(state, out_dir, step, "failed", str(e))
        raise
    return load_state(out_dir)


def spawn_step_thread(out_dir: str, step: int, force: bool) -> bool:
    key = resolve_out_dir(out_dir).as_posix()
    lk = _run_lock(key)
    if not lk.acquire(blocking=False):
        return False
    clear_cancel(out_dir)
    _write_active_marker(out_dir, step, "step")

    def worker() -> None:
        try:
            execute_step(out_dir, step, force=force)
        except Exception:
            pass
        finally:
            _clear_active_marker(out_dir)
            lk.release()

    threading.Thread(target=worker, daemon=True).start()
    return True


def run_pipeline_sequence(out_dir: str, *, force: bool = False) -> None:
    for step in range(1, STEP_COUNT + 1):
        if is_stop_requested(out_dir):
            break
        state = load_state(out_dir)
        status = state["steps"].get(str(step), {}).get("status")
        if status == "running":
            raise RuntimeError(f"Step {step} is still marked running")
        if status == "success" and not force:
            continue
        execute_step(out_dir, step, force=force)


def spawn_pipeline_all_thread(out_dir: str, force: bool) -> bool:
    key = resolve_out_dir(out_dir).as_posix()
    lk = _run_lock(key)
    if not lk.acquire(blocking=False):
        return False
    clear_cancel(out_dir)
    _write_active_marker(out_dir, None, "run_all")

    def worker() -> None:
        try:
            run_pipeline_sequence(out_dir, force=force)
        except Exception:
            pass
        finally:
            _clear_active_marker(out_dir)
            lk.release()

    threading.Thread(target=worker, daemon=True).start()
    return True


def preflight_run_all(out_dir: str) -> None:
    state = load_state(out_dir)
    if _mark_stale_running_steps(state):
        save_state(out_dir, state)
    for i in range(1, STEP_COUNT + 1):
        if state["steps"].get(str(i), {}).get("status") == "running":
            raise RuntimeError("A step is still running; wait or Redo before run-all")


def hydrate_steps_from_disk(state: dict[str, Any]) -> dict[str, Any]:
    _mark_stale_running_steps(state)
    d = resolve_out_dir(state["out_dir"])
    steps = state.setdefault("steps", {})
    for sid, fname in [("1", "script_brief.json"), ("2", "storyboard.json"), ("3", "img_results.json"), ("4", "video_prompts.json")]:
        if (d / fname).is_file():
            row = steps.setdefault(sid, {"key": "", "title": "", "status": "pending", "error": None, "updated_at": None})
            if row.get("status") == "pending":
                row["status"] = "success"
    if (d / "final.mp4").is_file():
        row = steps.setdefault("5", {"key": "", "title": "", "status": "pending", "error": None, "updated_at": None})
        if row.get("status") == "pending":
            row["status"] = "success"
    return state


def _final_mp4_rel_for_run(st: dict[str, Any], rel_out_dir: str) -> str | None:
    raw = st.get("final_mp4")
    if isinstance(raw, str) and raw.strip():
        return raw.strip().replace("\\", "/")
    if (resolve_out_dir(rel_out_dir) / "final.mp4").is_file():
        return "final.mp4"
    return None


def _cover_image_rel_for_run(rel_out_dir: str) -> str | None:
    img_dir = resolve_out_dir(rel_out_dir) / "images"
    if not img_dir.is_dir():
        return None
    for p in sorted(img_dir.iterdir()):
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            return f"images/{p.name}"
    return None


def _last_edited_at(st: dict[str, Any], run_dir: Path) -> str | None:
    latest: str | None = None
    for row in st.get("steps", {}).values():
        if isinstance(row, dict):
            ua = row.get("updated_at")
            if isinstance(ua, str) and ua and (latest is None or ua > latest):
                latest = ua
    if latest:
        return latest
    if isinstance(st.get("created_at"), str):
        return st["created_at"]
    try:
        return datetime.utcfromtimestamp(run_dir.stat().st_mtime).isoformat() + "Z"
    except OSError:
        return None


def list_runs(limit: int = 50) -> list[dict[str, Any]]:
    os.chdir(PROJECT_ROOT)
    root = PROJECT_ROOT / "outputs"
    if not root.is_dir():
        return []
    dirs = sorted([p for p in root.iterdir() if p.is_dir() and not _is_reserved_output_dir(p.name)], key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    out: list[dict[str, Any]] = []
    for p in dirs:
        rel = f"outputs/{p.name}"
        try:
            st = load_state(rel)
        except FileNotFoundError:
            st = new_run_state(p.name, rel, "(legacy, no pipeline_ui_state.json)", 90, "unknown", 5, 3)
        hydrate_steps_from_disk(st)
        out.append({
            "run_id": st.get("run_id", p.name),
            "out_dir": st.get("out_dir", rel),
            "topic": st.get("topic", ""),
            "created_at": st.get("created_at"),
            "updated_at": _last_edited_at(st, p),
            "summary": {k: v.get("status") for k, v in st.get("steps", {}).items()},
            "final_mp4": _final_mp4_rel_for_run(st, rel),
            "cover_image": _cover_image_rel_for_run(rel),
        })
    return out


def get_run_detail(run_id: str) -> dict[str, Any]:
    out_dir = f"outputs/{run_id}"
    try:
        st = load_state(out_dir)
    except FileNotFoundError:
        d = resolve_out_dir(out_dir)
        if not d.is_dir():
            raise FileNotFoundError(out_dir)
        st = new_run_state(run_id, out_dir, "(legacy, no pipeline_ui_state.json)", 90, "unknown", 5, 3)
    hydrate_steps_from_disk(st)
    meta = {str(i): {"key": k, "title": t} for i, k, t, _ in STEP_LABELS}
    st["steps"] = {sid: {**st.get("steps", {}).get(sid, {}), **meta[sid]} for sid in meta}
    save_state(out_dir, st)
    return st


def safe_rel_file(out_dir: str, rel: str) -> Path:
    rel_norm = rel.replace("\\", "/").strip()
    if not rel_norm or rel_norm.startswith("/"):
        raise ValueError("invalid path")
    if ".." in Path(rel_norm).parts:
        raise ValueError("invalid path")
    base = resolve_out_dir(out_dir).resolve()
    candidate = (base / rel_norm).resolve()
    candidate.relative_to(base)
    return candidate


def read_step_log(out_dir: str, step: int, max_chars: int = 400_000) -> Optional[str]:
    p = resolve_out_dir(out_dir) / "logs" / f"step_{step}.log"
    if not p.is_file():
        return None
    text = p.read_text(encoding="utf-8", errors="replace")
    return text if len(text) <= max_chars else "\n... [truncated] ...\n" + text[-max_chars:]


def get_step_artifacts(out_dir: str, step: int) -> dict[str, Any]:
    d = resolve_out_dir(out_dir)

    def to_rel(p: Path) -> str:
        return p.relative_to(d).as_posix()

    out: dict[str, Any] = {"step": step, "text": None, "text_kind": None, "images": [], "videos": []}
    files = {1: "script_brief.json", 2: "storyboard.json", 3: "img_results.json", 4: "video_prompts.json"}
    if step in files:
        f = d / files[step]
        if f.is_file():
            out["text_kind"] = "json"
            out["text"] = f.read_text(encoding="utf-8", errors="replace")[:512_000]
    if step == 3:
        img_dir = d / "images"
        if img_dir.is_dir():
            exts = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
            paths = sorted([p for p in img_dir.iterdir() if p.is_file() and p.suffix.lower() in exts], key=lambda x: x.name)
            out["images"] = [{"path": to_rel(p), "label": p.name} for p in paths[:48]]
    if step == 4:
        vdir = d / "videos"
        if vdir.is_dir():
            paths = sorted([p for p in vdir.iterdir() if p.suffix.lower() == ".mp4"], key=lambda x: x.name)
            out["videos"] = [{"path": to_rel(p), "label": p.name} for p in paths[:32]]
    if step == 5:
        f = d / "final.mp4"
        if f.is_file():
            out["videos"] = [{"path": to_rel(f), "label": f.name}]
    return out


_DOWNSTREAM: dict[int, list[int]] = {1: [2, 3, 4, 5], 2: [3, 4, 5], 3: [4, 5], 4: [5]}


def _any_step_running(state: dict[str, Any]) -> bool:
    return any(isinstance(row, dict) and row.get("status") == "running" for row in state.get("steps", {}).values())


def _merge_manual_refs(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    for shot_id, row in incoming.items():
        if not isinstance(row, dict):
            continue
        old = existing.get(shot_id)
        if isinstance(old, dict) and "manual_reference_image_paths" in old and "manual_reference_image_paths" not in row:
            row["manual_reference_image_paths"] = old["manual_reference_image_paths"]
    return incoming


def save_step_artifact_text(out_dir: str, step: int, text: str, text_kind: str) -> dict[str, Any]:
    if step not in (1, 2, 4):
        raise ValueError(f"Step {step} does not support text save")
    if text_kind != "json":
        raise ValueError("text_kind must be json")
    d = resolve_out_dir(out_dir)
    if not d.is_dir():
        raise FileNotFoundError(str(d))
    state = load_state(out_dir)
    if _any_step_running(state):
        raise RuntimeError("A step is running; wait before saving edits")
    body = (text or "").strip()
    if not body:
        raise ValueError("text must not be empty")
    try:
        obj = json.loads(body)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e
    if not isinstance(obj, dict):
        raise ValueError("artifact must be a JSON object")

    if step == 1:
        _write_json(d, "script_brief.json", obj)
        _write_json(d, "research.json", obj)
    elif step == 2:
        _write_json(d, "storyboard.json", obj)
        (d / "script.md").write_text(str(obj.get("script") or ""), encoding="utf-8")
    elif step == 4:
        existing = _read_json(d, "video_prompts.json") if (d / "video_prompts.json").is_file() else {}
        _write_json(d, "video_prompts.json", _merge_manual_refs(existing if isinstance(existing, dict) else {}, obj))
    return {"ok": True, "step": step, "text_kind": text_kind, "downstream_steps": _DOWNSTREAM.get(step, [])}


def update_run_topic(out_dir: str, topic: str) -> dict[str, Any]:
    name = (topic or "").strip()
    if not name:
        raise ValueError("topic must not be empty")
    d = resolve_out_dir(out_dir)
    if not d.is_dir():
        raise FileNotFoundError(str(d))
    state = load_state(out_dir)
    if _any_step_running(state):
        raise RuntimeError("A step is running; wait before renaming")
    state["topic"] = name
    save_state(out_dir, state)
    for fname in ("script_brief.json", "research.json"):
        p = d / fname
        if p.is_file():
            try:
                obj = _read_json(d, fname)
                if isinstance(obj, dict):
                    obj["topic"] = name
                    obj["theme"] = name
                    _write_json(d, fname, obj)
            except (OSError, json.JSONDecodeError):
                pass
    return {"ok": True, "run_id": state["run_id"], "topic": name}
