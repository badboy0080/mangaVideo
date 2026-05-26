"""
FastAPI control plane for manga-pipeline (per-step run + state).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from server.pipeline_runner import (
    delete_run,
    get_run_detail,
    get_step_artifacts,
    init_run,
    list_runs,
    preflight_run_all,
    preflight_run_step,
    read_step_log,
    request_stop,
    resolve_out_dir,
    safe_rel_file,
    save_step_artifact_text,
    spawn_pipeline_all_thread,
    spawn_step_thread,
    update_run_topic,
)
from server.seedream_service import generate_ui_asset, safe_ui_asset_file, status as seedream_status
from steps.step_01_research import validate_style

app = FastAPI(title="Manga Pipeline Control", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    # Vite 占用 5173 时会改用 5174+；部分系统下 localhost 解析为 IPv6 [::1]，需放行。
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1|\[::1\]):\d+$",
    # 前端 fetch 未携带 Cookie，关闭 credentials 可减少浏览器跨域限制。
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SeedreamGenerateBody(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)
    purpose: str = Field("", max_length=200)
    save_as: str = Field("", max_length=80)
    size: str = Field("2K", max_length=16)
    reference_paths: list[str] = Field(default_factory=list)


@app.get("/api/seedream/status")
def seedream_status_route() -> dict:
    return seedream_status()


@app.post("/api/seedream/generate")
def seedream_generate(body: SeedreamGenerateBody) -> dict:
    if not seedream_status()["configured"]:
        raise HTTPException(
            503,
            "未配置 VOLCENGINE_API_KEY 或 ARK_API_KEY，无法调用 Seedream",
        )
    try:
        return generate_ui_asset(
            body.prompt.strip(),
            purpose=body.purpose.strip(),
            save_as=body.save_as.strip(),
            reference_paths=body.reference_paths,
            size=body.size.strip() or "2K",
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except RuntimeError as e:
        raise HTTPException(502, str(e)) from e


@app.get("/api/ui-assets/{filename}")
def ui_asset_file(filename: str):
    try:
        file_path = safe_ui_asset_file(filename)
    except ValueError:
        raise HTTPException(400, "invalid filename")
    if not file_path.is_file():
        raise HTTPException(404, "not found")
    return FileResponse(file_path, filename=file_path.name)


class CreateRunBody(BaseModel):
    topic: str = Field(..., min_length=1)
    duration: int = Field(90, ge=10, le=600)
    style: str = Field("电影短片", min_length=1, max_length=64)
    img_concurrency: int = Field(5, ge=1, le=16)
    video_concurrency: int = Field(3, ge=1, le=8)


class SaveArtifactTextBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=512_000)
    text_kind: str = Field(..., pattern="^(json|markdown)$")


class UpdateRunTopicBody(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)


@app.get("/api/health")
def health() -> dict:
    # Bump when adding endpoints so the UI / dev can confirm the running process is up to date.
    return {
        "ok": True,
        "api_revision": 15,
        "project_root": str(ROOT.resolve()),
        "cwd": str(Path.cwd().resolve()),
        "seedream": seedream_status(),
        "routes": [
            "step_log",
            "step_artifacts",
            "save_artifact_text",
            "patch_run_topic",
            "run_file",
            "run_all",
            "stop",
            "delete_run",
            "seedream_generate",
            "ui_assets",
        ],
    }


@app.post("/api/runs")
def create_run(body: CreateRunBody) -> dict:
    try:
        style_key = validate_style(body.style.strip() or "电影短片")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return init_run(
        topic=body.topic,
        duration=body.duration,
        style=style_key,
        img_concurrency=body.img_concurrency,
        video_concurrency=body.video_concurrency,
    )


@app.get("/api/runs")
def runs_list(limit: int = Query(50, ge=1, le=200)) -> list:
    return list_runs(limit=limit)


@app.post("/api/runs/{run_id}/steps/{step}/run")
def run_step(run_id: str, step: int, force: bool = Query(False)) -> dict:
    if step < 1 or step > 5:
        raise HTTPException(400, "step must be 1-5")
    out_dir = f"outputs/{run_id}"
    try:
        preflight_run_step(out_dir, step, force)
    except FileNotFoundError:
        raise HTTPException(404, "run not found")
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    if not spawn_step_thread(out_dir, step, force):
        raise HTTPException(409, "Another step is already running for this output folder")
    return {"queued": True, "run_id": run_id, "step": step}


@app.post("/api/runs/{run_id}/run-all")
def run_all(run_id: str, force: bool = Query(False)) -> dict:
    """Queue steps 1-5 in one thread; skips success unless force=true."""
    out_dir = f"outputs/{run_id}"
    try:
        preflight_run_all(out_dir)
    except FileNotFoundError:
        raise HTTPException(404, "run not found") from None
    except RuntimeError as e:
        raise HTTPException(409, str(e)) from None
    if not spawn_pipeline_all_thread(out_dir, force):
        raise HTTPException(
            409,
            "Pipeline already busy for this run (another step or run-all is executing).",
        )
    return {"queued": True, "run_id": run_id, "mode": "run_all", "force": force}


@app.get("/api/runs/{run_id}/steps/{step}/log", response_class=PlainTextResponse)
def step_log(run_id: str, step: int) -> PlainTextResponse:
    if step < 1 or step > 5:
        raise HTTPException(400, "step must be 1-5")
    out_dir = f"outputs/{run_id}"
    d = resolve_out_dir(out_dir)
    if not d.is_dir():
        raise HTTPException(
            404,
            detail={
                "error": "run_dir_missing",
                "run_id": run_id,
                "expected_dir": str(d.resolve()),
                "project_root": str(ROOT.resolve()),
                "cwd": str(Path.cwd().resolve()),
                "hint": "If detail loads but log 404s, the API may be running from a different copy of the repo; "
                "restart uvicorn from the same folder as this project's outputs/.",
            },
        )
    text = read_step_log(out_dir, step)
    if text is None:
        return PlainTextResponse(
            "(No log file yet. Run this step once; logs are saved under outputs/<run_id>/logs/step_N.log)",
        )
    return PlainTextResponse(text)


@app.get("/api/runs/{run_id}/steps/{step}/artifacts")
def step_artifacts(run_id: str, step: int) -> dict:
    if step < 1 or step > 5:
        raise HTTPException(400, "step must be 1-5")
    out_dir = f"outputs/{run_id}"
    d = resolve_out_dir(out_dir)
    if not d.is_dir():
        raise HTTPException(
            404,
            detail={
                "error": "run_dir_missing",
                "run_id": run_id,
                "expected_dir": str(d.resolve()),
                "project_root": str(ROOT.resolve()),
                "cwd": str(Path.cwd().resolve()),
                "hint": "Restart API from project root that contains this outputs/ folder.",
            },
        )
    return get_step_artifacts(out_dir, step)


@app.put("/api/runs/{run_id}/steps/{step}/artifacts/text")
def save_artifact_text(run_id: str, step: int, body: SaveArtifactTextBody) -> dict:
    if step < 1 or step > 5:
        raise HTTPException(400, "step must be 1-5")
    out_dir = f"outputs/{run_id}"
    try:
        return save_step_artifact_text(out_dir, step, body.text, body.text_kind)
    except FileNotFoundError:
        raise HTTPException(404, "run not found") from None
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except RuntimeError as e:
        raise HTTPException(409, str(e)) from e


@app.patch("/api/runs/{run_id}")
def patch_run(run_id: str, body: UpdateRunTopicBody) -> dict:
    out_dir = f"outputs/{run_id}"
    try:
        return update_run_topic(out_dir, body.topic)
    except FileNotFoundError:
        raise HTTPException(404, "run not found") from None
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except RuntimeError as e:
        raise HTTPException(409, str(e)) from e


@app.get("/api/runs/{run_id}/file")
def run_asset_file(run_id: str, path: str = Query(..., description="Relative path under run folder, e.g. images/foo.png")):
    out_dir = f"outputs/{run_id}"
    d = resolve_out_dir(out_dir)
    if not d.is_dir():
        raise HTTPException(404, "run not found")
    try:
        file_path = safe_rel_file(out_dir, path)
    except ValueError:
        raise HTTPException(400, "invalid path")
    if not file_path.is_file():
        raise HTTPException(404, "not found")
    return FileResponse(file_path, filename=file_path.name)


@app.post("/api/runs/{run_id}/stop")
def stop_run(run_id: str) -> dict:
    """Cooperative stop: finish current step at most, then do not start the next."""
    out_dir = f"outputs/{run_id}"
    d = resolve_out_dir(out_dir)
    if not d.is_dir():
        raise HTTPException(404, "run not found")
    try:
        return request_stop(out_dir)
    except FileNotFoundError:
        raise HTTPException(404, "run not found") from None


@app.delete("/api/runs/{run_id}")
def remove_run(run_id: str) -> dict:
    """Move run folder to outputs/_trash (hidden from history)."""
    try:
        return delete_run(run_id)
    except FileNotFoundError:
        raise HTTPException(404, "run not found") from None
    except RuntimeError as e:
        raise HTTPException(409, str(e)) from e


@app.get("/api/runs/{run_id}")
def run_detail(run_id: str) -> dict:
    try:
        return get_run_detail(run_id)
    except FileNotFoundError:
        raise HTTPException(404, "run not found")


def main() -> None:
    import uvicorn

    uvicorn.run(
        "server.main:app",
        host="127.0.0.1",
        port=8765,
        reload=False,
    )


if __name__ == "__main__":
    main()
