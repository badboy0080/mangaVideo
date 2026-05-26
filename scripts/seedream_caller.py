"""
火山引擎 Seedream 4.5 文生图 API 调用封装

API 文档: https://ark.cn-beijing.volces.com/api/v3/images/generations
模型:     doubao-seedream-4-5-251128
"""
import os, json, requests, uuid

SEEDREAM_API_KEY = os.environ.get("ARK_API_KEY", "")
SEEDREAM_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
SEEDREAM_MODEL   = "doubao-seedream-5-0-260128"


def call_seedream(prompt: str,
                  output_dir: str,
                  output_filename: str = None,
                  size: str = "2K",
                  aspect_ratio: str = None) -> dict:
    """
    调用 Seedream 4.5 文生图 API。

    参数:
        prompt         - 图片描述文本
        output_dir     - 图片本地保存目录（需已存在）
        output_filename- 文件名（不含扩展名），默认自动生成 UUID
        size           - 图片尺寸规格，默认 "2K"
        aspect_ratio   - 废弃，保留兼容性

    返回:
        {
            "image_path": "/path/to/saved/image.png",
            "url": "https://..."   # 原始 URL（如果 API 返回）
        }

    依赖环境变量:
        ARK_API_KEY  - 火山引擎 API Key
    """
    if not SEEDREAM_API_KEY:
        raise RuntimeError(
            "请设置环境变量 ARK_API_KEY\n"
            "  Linux/macOS: export ARK_API_KEY=你的key\n"
            "  Windows WSL:  echo 'export ARK_API_KEY=你的key' >> ~/.bashrc && source ~/.bashrc"
        )

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    if output_filename is None:
        output_filename = str(uuid.uuid4().hex[:8])

    # 生成带扩展名的本地路径
    local_path = os.path.join(output_dir, f"{output_filename}.png")

    headers = {
        "Authorization": f"Bearer {SEEDREAM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": SEEDREAM_MODEL,
        "prompt": prompt,
        "sequential_image_generation": "disabled",
        "response_format": "url",       # 返回 URL，代码内下载到本地
        "size": size,
        "stream": False,
        "watermark": False
    }

    resp = requests.post(
        SEEDREAM_ENDPOINT,
        headers=headers,
        json=payload,
        timeout=300   # 生图可能较慢
    )
    resp.raise_for_status()
    data = resp.json()

    # 解析返回的 URL 并下载图片
    image_url = None
    if "data" in data and len(data["data"]) > 0:
        image_url = data["data"][0].get("url")

    if image_url:
        img_resp = requests.get(image_url, timeout=60)
        img_resp.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(img_resp.content)

    return {
        "image_path": local_path,
        "url": image_url,
        "raw_response": data
    }
