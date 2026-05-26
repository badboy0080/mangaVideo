"""
DeepSeek V4 Pro API 调用封装
"""
import os, json, requests

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL   = "deepseek-v4-pro"          # 官方模型名
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

def call_deepseek(system_prompt: str, user_prompt: str,
                  temperature: float = 0.7, max_tokens: int = 8192) -> str:
    """调用 DeepSeek V4 Pro，返回完整回复字符串"""
    if not DEEPSEEK_API_KEY:
        raise RuntimeError(
            "请设置环境变量 DEEPSEEK_API_KEY\n"
            "  Linux/macOS: export DEEPSEEK_API_KEY=你的key\n"
            "  Windows WSL:  echo 'export DEEPSEEK_API_KEY=你的key' >> ~/.bashrc && source ~/.bashrc"
        )

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        "thinking": {
            "type": "enabled",
            "budget_tokens": 4096
        },
        "reasoning_effort": "high",
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }

    resp = requests.post(
        DEEPSEEK_API_URL,
        headers=headers,
        json=payload,
        timeout=180
    )
    resp.raise_for_status()
    data = resp.json()

    # V4 Pro 思考内容在 additional_kwargs.thinking 中，此处取 final 回复
    return data["choices"][0]["message"]["content"]
