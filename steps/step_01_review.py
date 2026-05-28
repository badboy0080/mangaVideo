from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from steps.deepseek_chat import chat
from steps.prompt_config import prompt_registry_entry, prompts_search_dir

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"
_DEFAULT_RULES: dict[str, Any] = {
    "version": 1,
    "pass_score": 80,
    "max_retry": 1,
    "rule_groups": [
        "核心命题清晰",
        "人物动机可信",
        "冲突具体有力",
        "叙事推进有效",
        "情绪曲线完整",
        "画面叙事能力强",
        "节奏适合目标时长",
        "单一句台词不超过20个中文字符",
        "结尾有记忆点",
        "风格服务故事",
        "忠实用户意图",
    ],
}


def load_step01_review_system_prompt() -> str:
    entry = prompt_registry_entry("step_01_review.system")
    raw_env = str(entry.get("env_path_key") or "")
    raw_rel = str(entry.get("relative_filename") or "step_01_review/_base.txt")

    import os

    override = os.environ.get(raw_env, "").strip() if raw_env else ""
    if override:
        p = Path(override).expanduser()
        if p.is_file():
            return p.read_text(encoding="utf-8").strip()

    for base in (prompts_search_dir(), _PROMPT_DIR):
        candidate = base / raw_rel
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8").strip()
    raise FileNotFoundError(f"缺少 Step01 审核提示词: {raw_rel}")


def load_step01_review_rules() -> dict[str, Any]:
    entry = prompt_registry_entry("step_01_review.system")
    rel = str(entry.get("rules_filename") or "step_01_review/rules.json")
    for base in (prompts_search_dir(), _PROMPT_DIR):
        candidate = base / rel
        if not candidate.is_file():
            continue
        with open(candidate, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {**_DEFAULT_RULES, **data}
    return dict(_DEFAULT_RULES)


def _strip_code_fence(text: str) -> str:
    s = (text or "").strip()
    m = re.match(r"^```(?:json)?\s*(.*?)\s*```$", s, flags=re.S | re.I)
    return m.group(1).strip() if m else s


def parse_review_response(raw: str, *, pass_score: int = 80) -> dict[str, Any]:
    s = _strip_code_fence(raw)
    try:
        data = json.loads(s)
    except json.JSONDecodeError as e:
        return {
            "passed": False,
            "score": 0,
            "issues": [f"审核 Agent 返回内容不是合法 JSON: {e}"],
            "revision_prompt": "请重新生成 Step01 创意正文，重点修复故事质量问题，并保持当前 SYSTEM_PROMPT 要求的正文格式。",
            "raw_response": raw,
        }

    if not isinstance(data, dict):
        data = {}

    score_raw = data.get("score", 0)
    try:
        score = int(score_raw)
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(100, score))

    issues_raw = data.get("issues", [])
    if isinstance(issues_raw, str):
        issues = [issues_raw.strip()] if issues_raw.strip() else []
    elif isinstance(issues_raw, list):
        issues = [str(x).strip() for x in issues_raw if str(x).strip()]
    else:
        issues = []

    passed_raw = data.get("passed", score >= pass_score and not issues)
    passed = bool(passed_raw) and score >= pass_score and not issues
    revision_prompt = str(data.get("revision_prompt") or "").strip()
    if not passed and not revision_prompt:
        joined = "；".join(issues) if issues else "审核未通过，但未给出具体问题"
        revision_prompt = (
            f"请根据以下审核问题重写 Step01 创意正文：{joined}。"
            "保持原有主题、风格和时长，不新增无关情节；不要追求固定字段补齐，优先提升故事表达质量。"
        )

    return {
        "passed": passed,
        "score": score,
        "issues": issues,
        "revision_prompt": revision_prompt,
        "raw_response": raw,
    }


def run(topic: str, style: str, duration_seconds: int, creative_brief: str) -> dict[str, Any]:
    rules = load_step01_review_rules()
    pass_score = int(rules.get("pass_score") or 80)
    system_prompt = load_step01_review_system_prompt()
    user_prompt = (
        f"主题：{topic}\n"
        f"风格类型：{style}\n"
        f"目标时长（秒）：{int(duration_seconds)}\n"
        f"通过分数：{pass_score}\n"
        f"审核规则配置：{json.dumps(rules, ensure_ascii=False)}\n\n"
        "请审核以下 Step01 创意正文：\n"
        "----- STEP01 OUTPUT START -----\n"
        f"{creative_brief or ''}\n"
        "----- STEP01 OUTPUT END -----"
    )
    raw = chat(system_prompt, user_prompt, temperature=0.2, max_tokens=2000, timeout=120).strip()
    if not raw:
        return {
            "passed": False,
            "score": 0,
            "issues": ["审核 Agent 没有返回结果，请检查 DEEPSEEK_API_KEY、网络或审核提示词配置。"],
            "revision_prompt": "请重新生成 Step01 创意正文，保持主题、风格和时长不变，优先补强核心命题、人物动机、冲突、节奏和结尾记忆点。",
            "raw_response": "",
        }
    return parse_review_response(raw, pass_score=pass_score)
