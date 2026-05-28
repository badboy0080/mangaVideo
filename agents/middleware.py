"""AgentScope Middleware: 流水线 Hook 监控。

提供三个自定义 Middleware：
- PipelineLoggingMiddleware：将 Agent 执行日志写入 logs/step_N.log
- ProgressMiddleware：实时更新 pipeline_ui_state.json 状态
- StopCheckMiddleware：检查用户是否请求停止
"""
from __future__ import annotations

import sys
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, AsyncGenerator, TextIO

from agentscope.middleware import MiddlewareBase

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class PipelineLoggingMiddleware(MiddlewareBase):
    """将 Agent 推理过程写入步骤日志文件。

    每个 step 的日志写入 outputs/{run_id}/logs/step_{N}.log，
    与原有日志系统完全兼容。
    """

    def __init__(self, log_path: Path) -> None:
        super().__init__()
        self._log_path = log_path
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_file: TextIO | None = None

    def _write(self, text: str) -> None:
        if self._log_file is None:
            self._log_file = open(self._log_path, "a", encoding="utf-8")
        self._log_file.write(text)
        self._log_file.flush()

    def close(self) -> None:
        if self._log_file:
            self._log_file.close()
            self._log_file = None

    async def on_reply(
        self,
        agent: "Agent",
        input_kwargs: dict,
        next_handler: Callable[..., AsyncGenerator],
    ) -> AsyncGenerator:
        self._write(f"\n--- Agent [{agent.name}] 开始执行 ---\n")
        self._write(f"时间: {datetime.utcnow().isoformat()}Z\n\n")
        try:
            async for item in next_handler(**input_kwargs):
                yield item
        except Exception as e:
            self._write(f"\n[错误] {type(e).__name__}: {e}\n")
            raise
        finally:
            self._write(f"\n--- Agent [{agent.name}] 执行结束 ---\n")
            self.close()

    async def on_model_call(
        self,
        agent: "Agent",
        input_kwargs: dict,
        next_handler: Callable,
    ):
        self._write(f"[模型调用] {agent.name}\n")
        try:
            result = await next_handler(**input_kwargs)
            return result
        except Exception as e:
            self._write(f"[模型错误] {e}\n")
            raise


class ProgressMiddleware(MiddlewareBase):
    """实时更新 pipeline_ui_state.json 中的步骤状态。

    每步开始/结束时更新状态文件，前端轮询即可看到进度。
    """

    def __init__(self, out_dir: str, step: int) -> None:
        super().__init__()
        self._out_dir = Path(out_dir)
        self._step = step
        self._state_file = self._out_dir / "pipeline_ui_state.json"

    def _update_status(self, status: str, error: str | None = None) -> None:
        if not self._state_file.is_file():
            return
        try:
            state = json.loads(self._state_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        steps = state.get("steps", {})
        row = steps.get(str(self._step), {})
        if isinstance(row, dict):
            row["status"] = status
            row["error"] = error
            row["updated_at"] = datetime.utcnow().isoformat() + "Z"
        if error:
            state["last_global_error"] = error
        else:
            state["last_global_error"] = None

        try:
            self._state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    async def on_reply(
        self,
        agent: "Agent",
        input_kwargs: dict,
        next_handler: Callable[..., AsyncGenerator],
    ) -> AsyncGenerator:
        self._update_status("running")
        try:
            async for item in next_handler(**input_kwargs):
                yield item
            self._update_status("success")
        except Exception as e:
            self._update_status("failed", str(e))
            raise


class StopCheckMiddleware(MiddlewareBase):
    """检查用户是否请求停止流水线。

    如果 stop_requested 标记为 True，在每次推理前抛出异常。
    """

    def __init__(self, stop_checker: Callable[[], bool]) -> None:
        super().__init__()
        self._check = stop_checker

    async def on_reasoning(
        self,
        agent: "Agent",
        input_kwargs: dict,
        next_handler: Callable[..., AsyncGenerator],
    ) -> AsyncGenerator:
        if self._check():
            raise RuntimeError("User requested stop")
        async for item in next_handler(**input_kwargs):
            yield item
