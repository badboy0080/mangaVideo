"""
Step 5: Seedream 文生图（仅资产）

产出约定：调用生图 API 时使用的 `prompt` **仅**来自 Step 4 模型正文；本步只负责请求与落盘路径。
见 `steps.step_output_policy`。
"""
from __future__ import annotations

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

from db import ensure_image_row, update_image_path
from steps.seedream_client import api_key, generate_image, safe_filename_stem


def _split_bundle(prompt_map: dict) -> tuple[dict, dict]:
    if isinstance(prompt_map, dict) and prompt_map.get("version") == 2:
        return prompt_map.get("assets") or {}, prompt_map.get("shots") or {}
    return prompt_map, {}


def run(conn, prompt_map: dict, out_dir: str, concurrency: int = 5) -> dict:
    """conn 仅兼容旧接口；并发任务内会为 SQLite 各自新建连接。"""
    _ = conn
    assets, shots = _split_bundle(prompt_map)
    _ = shots  # 分镜不生图；保留拆分以便兼容旧 prompt_map
    key = api_key()
    db_path = f"{out_dir}/assets.db"

    img_results: dict[str, str] = {}

    pending_assets = [(rid, data) for rid, data in assets.items() if data.get("prompt")]
    print(f"  资产文生图（角色/场景）：{len(pending_assets)} 张，并发 {concurrency}")

    def gen_asset(item: tuple[str, dict], idx: int, total: int) -> tuple[str, str | None]:
        ref_id, data = item
        name = data["name"]
        prompt = data["prompt"]
        tag = data.get("tag", "character")
        print(f"  [资产 {idx}/{total}] {name} ({tag}) txt2img")
        tconn = sqlite3.connect(db_path)
        try:
            ensure_image_row(tconn, ref_id, tag, name, prompt)
            stem = safe_filename_stem(f"img_{ref_id}")
            dest = Path(out_dir) / "images" / f"{stem}.png"
            path = str(
                generate_image(prompt, dest, api_key_override=key, image_inputs=None)
            ).replace("\\", "/")
            update_image_path(tconn, ref_id, path, "generated")
            return ref_id, path
        except requests.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else 0
            if status_code == 429:
                error_category, hint = "rate_limited", "（可稍后重试）"
            elif status_code >= 400:
                error_category, hint = "api_error", f"（HTTP {status_code}）"
            else:
                error_category, hint = "http_error", ""
            print(f"  [失败] 资产 {name} | error_category={error_category} {hint}: {e}")
            try:
                update_image_path(tconn, ref_id, "", "failed")
            except Exception:
                pass
            return ref_id, None
        except RuntimeError as e:
            error_category = "download_failed"
            print(f"  [失败] 资产 {name} | error_category={error_category}: {e}")
            try:
                update_image_path(tconn, ref_id, "", "failed")
            except Exception:
                pass
            return ref_id, None
        except Exception as e:
            error_category = "unknown"
            print(f"  [失败] 资产 {name} | error_category={error_category}: {type(e).__name__}: {e}")
            try:
                update_image_path(tconn, ref_id, "", "failed")
            except Exception:
                pass
            return ref_id, None
        finally:
            tconn.close()

    total_a = len(pending_assets)
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = {
            ex.submit(gen_asset, pair, i + 1, total_a): pair[0]
            for i, pair in enumerate(pending_assets)
        }
        for fu in as_completed(futs):
            ref_id, path = fu.result()
            if path:
                img_results[ref_id] = path
                meta = assets.get(ref_id, {})
                n = meta.get("name")
                if n:
                    img_results[n] = path

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(out_dir) / "asset_img_results.json", "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in img_results.items() if str(k).startswith("图片")}, f, ensure_ascii=False, indent=2)

    print(f"  生图完成：资产 {len(pending_assets)} 张（无分镜关键帧图）；详见 img_results.json")
    return img_results
