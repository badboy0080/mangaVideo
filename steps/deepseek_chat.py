"""调用 DeepSeek Chat Completions（与流水线其他步骤共用同一模型与鉴权方式）。

修复（P0）：
- 删除 subprocess.run(["curl",...]) 调用方式
  → API Key 不再暴露于进程参数列表，Windows 无需依赖 curl.exe
- 改用带自动重试的 requests.Session（429 / 5xx 退避重试 3 次）
- 统一 key 查找逻辑，供所有 step 共享
"""
from __future__ import annotations

import os

import requests
from requests.adapters import HTTPAdapter, Retry

DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

# 共享 Session：429/5xx 自动退避重试，最多 3 次
_retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503])
_session = requests.Session()
_session.mount("https://", HTTPAdapter(max_retries=_retry))


def _get_api_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        config_path = os.path.expanduser("~/.deepseek/api_key")
        if os.path.isfile(config_path):
            with open(config_path, encoding="utf-8") as f:
                key = f.read().strip()
    return key


def chat(
    system: str,
    user: str,
    *,
    temperature: float = 0.8,
    max_tokens: int = 8000,
    timeout: int = 180,
) -> str:
    """返回助手正文；未配置 API Key 或调用失败时返回空字符串。"""
    api_key = _get_api_key()
    if not api_key:
        return ""

    try:
        r = _session.post(
            DEEPSEEK_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        r.raise_for_status()
        data = r.json()
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
    except Exception as e:
        print(f"  [DeepSeek] 调用失败: {type(e).__name__}: {e}")
    return ""
