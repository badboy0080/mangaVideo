"""
Step 4: DeepSeek 生成资产清单 + Seedream 文生图提示词

1. **资产清单（人物 / 场景 / 道具）**：调用 DeepSeek，**主要依据** Step 1 纲要中的「【人物与场景清单】」
   输出结构化 JSON，并写入 `assets.json`（覆盖 Step 3 正则结果，若 Step 3 曾跑过）。
2. **定妆提示词**：对每个资产再调 DeepSeek（`step_04_img_single_system.txt`），仍只参考 Step 1 清单，不读分镜剧情。
3. **分镜元数据**：从 Step 2 脚本解析 `@` 与分镜块（不生成分镜图）。
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from steps.deepseek_chat import chat as deepseek_chat
from steps.prompt_config import load_registered_system_prompt
from steps.script_split import split_shots_standard
from steps.utils import is_likely_character

_EXTRACT_ASSETS_SYSTEM = load_registered_system_prompt("step_02_asset_catalog.system")

_IMG_SINGLE_SYSTEM = load_registered_system_prompt("step_02_asset_image.system")

_AT_TAG_RE = re.compile(r"@([\u4e00-\u9fffA-Za-z][\u4e00-\u9fffA-Za-z0-9]*)")


def _split_shots(script: str) -> list[tuple[str, str]]:
    blocks = split_shots_standard(script)
    return [(sn, body) for sn, _sec, body in blocks]


# _is_likely_character 已提取至 steps/utils.py，从那里统一导入


def _resolve_out_dir(out_dir: str) -> Path:
    p = Path(out_dir)
    if not p.is_absolute():
        p = Path(__file__).resolve().parent.parent / out_dir
    return p


def _empty_catalog() -> dict[str, Any]:
    return {
        "characters": [],
        "scenes": [],
        "props": [],
        "total_chars": 0,
        "total_scenes": 0,
        "total_props": 0,
    }


def _parse_json_object(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if not raw:
        return None
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```\s*$", "", raw)
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _normalize_catalog_item(item: Any) -> dict[str, str] | None:
    if not isinstance(item, dict):
        return None
    name = _normalize_asset_name(str(item.get("name") or ""))
    if not name:
        return None
    desc = str(item.get("description") or "").strip() or name
    return {"name": name, "description": desc[:6000], "refs": []}


def _normalize_catalog(data: dict[str, Any]) -> dict[str, Any]:
    out = _empty_catalog()
    for key in ("characters", "scenes", "props"):
        rows: list[dict] = []
        seen: set[str] = set()
        for item in data.get(key) or []:
            row = _normalize_catalog_item(item)
            if not row:
                continue
            nk = row["name"].casefold()
            if nk in seen:
                continue
            seen.add(nk)
            rows.append(row)
        out[key] = rows
    out["total_chars"] = len(out["characters"])
    out["total_scenes"] = len(out["scenes"])
    out["total_props"] = len(out["props"])
    return out


def _legacy_assets_to_catalog(assets: dict | None) -> dict[str, Any]:
    """Step 3 正则结果 → 与 assets.json 同结构（DeepSeek 失败时回退）。"""
    assets = assets or {}
    out = _empty_catalog()
    for key, tag in [("characters", "character"), ("scenes", "scene"), ("props", "prop")]:
        for item in assets.get(key) or []:
            if not isinstance(item, dict):
                continue
            name = _normalize_asset_name(str(item.get("name") or ""))
            if not name:
                continue
            out[key].append(
                {
                    "name": name,
                    "description": (item.get("description") or name)[:6000],
                    "refs": list(item.get("refs") or []),
                }
            )
    out["total_chars"] = len(out["characters"])
    out["total_scenes"] = len(out["scenes"])
    out["total_props"] = len(out["props"])
    return out


def _catalog_has_items(catalog: dict[str, Any]) -> bool:
    return bool(catalog.get("characters") or catalog.get("scenes") or catalog.get("props"))


def _attach_script_refs(catalog: dict[str, Any], script: str) -> dict[str, Any]:
    """为清单条目补全分镜引用（仅整理，不改描述）。"""
    if not (script or "").strip():
        return catalog
    name_to_tag: dict[str, str] = {}
    for key, tag in [("characters", "character"), ("scenes", "scene"), ("props", "prop")]:
        for item in catalog.get(key) or []:
            if isinstance(item, dict) and item.get("name"):
                name_to_tag[str(item["name"])] = tag

    shots = re.split(r"分镜\s*\d+[｜|]\s*\d+\s*秒", script)
    for i, shot in enumerate(shots[1:], 1):
        for ref in set(_AT_TAG_RE.findall(shot)):
            tag = name_to_tag.get(ref)
            if not tag:
                continue
            bucket = catalog.get(
                {"character": "characters", "scene": "scenes", "prop": "props"}[tag]
            )
            for item in bucket or []:
                if item.get("name") == ref:
                    refs = item.setdefault("refs", [])
                    label = f"分镜{i}"
                    if label not in refs:
                        refs.append(label)
                    break
    return catalog


def _deepseek_extract_asset_catalog(
    research: dict | None,
    script: str,
) -> tuple[dict[str, Any], str]:
    """
    用 DeepSeek 从 Step 1 清单生成人物/场景/道具。
    返回 (catalog, 来源说明)。
    """
    inventory_raw, inventory_note = _resolve_step1_inventory(research)
    inv = _cap_inventory_block(inventory_raw)
    if not inv.strip():
        return _empty_catalog(), inventory_note or "empty_inventory"

    at_refs = sorted(set(_AT_TAG_RE.findall(script or "")))
    at_line = ", ".join(f"@{x}" for x in at_refs) if at_refs else "（分镜中未出现 @）"

    user_body = (
        "### Step 1 人物与场景清单（唯一权威，请据此分类与描述）\n\n"
        f"{inv}\n\n"
        "### 分镜中出现的 @ 名称（仅核对称呼是否遗漏，禁止从分镜剧情发明新设定）\n"
        f"{at_line}\n"
    )

    print("  [DeepSeek] 根据 Step 1 清单生成人物 / 场景 / 道具列表…")
    raw = deepseek_chat(
        _EXTRACT_ASSETS_SYSTEM,
        user_body,
        temperature=0.35,
        max_tokens=4000,
        timeout=180,
    )
    parsed = _parse_json_object(raw or "")
    if not parsed:
        print("  [警告] DeepSeek 资产清单非 JSON 或为空，将尝试回退 Step 3 结果（若有）")
        return _empty_catalog(), f"{inventory_note}|parse_failed"

    catalog = _normalize_catalog(parsed)
    catalog = _attach_script_refs(catalog, script)
    catalog["total_chars"] = len(catalog["characters"])
    catalog["total_scenes"] = len(catalog["scenes"])
    catalog["total_props"] = len(catalog["props"])
    print(
        f"  资产清单：{catalog['total_chars']} 角色 / "
        f"{catalog['total_scenes']} 场景 / {catalog['total_props']} 道具"
    )
    return catalog, inventory_note


def _write_assets_json(out_dir: str, catalog: dict[str, Any]) -> None:
    d = _resolve_out_dir(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    path = d / "assets.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"  已写入 {path}")


def _catalog_to_prompt_rows(catalog: dict[str, Any]) -> list[dict]:
    rows: list[dict] = []
    for tag, key in [
        ("character", "characters"),
        ("scene", "scenes"),
        ("prop", "props"),
    ]:
        for item in catalog.get(key) or []:
            if not isinstance(item, dict):
                continue
            name = _normalize_asset_name(str(item.get("name") or ""))
            if not name:
                continue
            rows.append(
                {
                    "name": name,
                    "tag": tag,
                    "description": (item.get("description") or name)[:6000],
                    "refs": list(item.get("refs") or []),
                }
            )
    return rows


def _mentions_in_shot(shot_content: str) -> list[str]:
    seen: list[str] = []
    for m in _AT_TAG_RE.findall(shot_content):
        if m not in seen:
            seen.append(m)
    return seen


# Step 1 清单块送入单次请求的长度上限（字符）
STEP04_INVENTORY_CAP_DEFAULT = "56000"


def _cap_inventory_block(block: str) -> str:
    """防止极端长纲要撑爆上下文；默认截断末尾。"""
    s = (block or "").strip()
    if not s:
        return ""
    cap_raw = os.environ.get("STEP04_INVENTORY_CHAR_CAP", STEP04_INVENTORY_CAP_DEFAULT).strip()
    try:
        cap = max(2048, int(cap_raw))
    except ValueError:
        cap = int(STEP04_INVENTORY_CAP_DEFAULT)
    if len(s) <= cap:
        return s
    return s[:cap] + "\n\n（清单内容已在上限处截断；请依据前文为该资产建模。）"


def _extract_step1_inventory_block(creative_brief: str) -> tuple[str, str]:
    """
    仅从 Step 1 纲要中取「全局角色/道具/场景」权威段落。
    返回 (段落, 标记来源)。
    """
    text = (creative_brief or "").strip()
    if not text:
        return "", ""

    anchor = "【人物与场景清单】"
    i = text.find(anchor)
    if i >= 0:
        after = text[i + len(anchor) :].lstrip(" ：:\u3000\t")
        accum: list[str] = []
        for raw_line in after.split("\n"):
            ls = raw_line.strip()
            if ls.startswith("【"):
                header = ls.split("】", 1)[0] + "】"
                if header == anchor or ls.startswith("【人物与场景清单"):
                    accum.append(raw_line)
                    continue
                break
            accum.append(raw_line)
        chunk = "\n".join(accum).strip()
        if chunk:
            return chunk, anchor

    m = re.search(
        r"(?ms)^#{1,3}\s*[一1][、.‧•．][^\n]*核心设定[^\n]*\s*\r?\n(.*?)"
        r"(?=^#{1,3}\s*(?:二|三|四|五|六|七八九十2-9])[、.]|\Z)",
        text,
    )
    if m:
        blk = (m.group(1) or "").strip()
        if blk:
            return blk, "### 一、核心设定"

    return "", ""


def _resolve_step1_inventory(research: dict | None) -> tuple[str, str]:
    """综合 creative_brief 与 findings[].content。"""
    if not isinstance(research, dict):
        return "", "no_research"
    bodies: list[tuple[str, str]] = []
    main = (research.get("creative_brief") or "").strip()
    if main:
        bodies.append(("creative_brief", main))
    for f in research.get("findings") or []:
        if isinstance(f, dict):
            c = (f.get("content") or "").strip()
            if c:
                bodies.append(("findings", c))
    for label, blob in bodies:
        block, marker = _extract_step1_inventory_block(blob)
        if block.strip():
            return block, marker or label
        if "##" not in blob and "】" not in blob and len(blob) < 500:
            continue
    try:
        fallback_cap = max(4096, int(os.environ.get("STEP04_FALLBACK_BRIEF_CAP", "16000")))
    except ValueError:
        fallback_cap = 16000
    brief = research.get("creative_brief") or ""
    excerpt = brief.strip()
    if not excerpt and bodies:
        excerpt = bodies[0][1]
    excerpt = excerpt[:fallback_cap].strip()
    if excerpt:
        return (
            excerpt,
            "⚠️ 未检测到「【人物与场景清单】」或「### 一、核心设定」；已退回 Step 1 纲要前缀节选",
        )
    return "", "empty"


def _normalize_asset_name(name: str) -> str:
    return (name or "").strip().lstrip("@")


def _dedupe_merge_asset_rows(rows: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        tg = (row.get("tag") or "character").strip().lower()
        if tg not in ("character", "scene", "prop"):
            tg = "character"
        nm = _normalize_asset_name(row.get("name") or "")
        if not nm:
            continue
        groups.setdefault((tg, nm), []).append(row)

    merged: list[dict] = []
    for (tg, nm), grp in sorted(groups.items(), key=lambda x: (x[0][0], x[0][1])):
        texts: list[str] = []
        seen_t: set[str] = set()
        for r in grp:
            d = (r.get("description") or "").strip()
            if d and d not in seen_t:
                seen_t.add(d)
                texts.append(d)
        description_merged = "\n".join(texts) if texts else nm
        refs: list[str] = []
        seen_r: set[str] = set()
        for r in grp:
            rr = r.get("refs") or []
            if isinstance(rr, str):
                rr = [rr]
            if not isinstance(rr, list):
                continue
            for x in rr:
                s = str(x).strip()
                if s and s not in seen_r:
                    seen_r.add(s)
                    refs.append(s)
        merged.append(
            {
                "name": nm,
                "tag": tg,
                "description": description_merged[:6000],
                "refs": refs,
            }
        )
    return merged


def _generate_single_prompt(
    name: str,
    auxiliary_note: str,
    tag: str,
    inventory_authority: str,
    *,
    inventory_source_label: str = "",
) -> str:
    style_hint = {
        "character": "角色：按「电影级设定集 + 同一角色三视图 + 写实或描述一致画风」前缀；中段写衣帽材质姿态；后缀「干净纯色背景、设计参考」。",
        "scene": "场景：按「场景概念图/广角」类前缀；中段写空间与光影；后缀「整洁无杂物、可作背景参考」。",
        "prop": "道具：「道具设定参考」前缀；中段写形态材质；后缀「纯色/中性背景、突出单体」。",
    }
    hint = style_hint.get(tag, style_hint["character"])

    auxiliary = (auxiliary_note or "").strip() or "（上游未提供该资产的局部摘录）"
    inv_block = _cap_inventory_block(inventory_authority)
    provenance = (inventory_source_label or "").strip() or "Step 1「人物与场景清单」或核心设定小节"

    if inv_block.strip():
        user_body = (
            "### Step 1 纲要摘录：全局人物 / 道具 / 场景清单\n"
            "### （本条为唯一人设与陈设出处；禁止使用 Step 2 分镜正文，禁止按分镜重复描写发明第二套样貌）\n\n"
            f"摘录备注：{provenance}\n\n"
            f"{inv_block}\n\n"
            "---\n"
            f"当前要写成「定妆级」静态参考图的资产：**{name}**\n"
            "（应与分镜 `@` 名称一致或能从清单条目语义唯一对应）\n"
            f"type（character / scene / prop）：{tag}\n\n"
            "### 本条资产在清单中的描述（优先依据）\n"
            f"{auxiliary[:1400]}\n\n"
            f"{hint}\n\n"
            "**硬性要求：**\n"
            "（1）只根据上方清单里与该资产对应的一至两行来写视觉；同一主角全片只有一套外观。\n"
            "（2）禁止复述情节、走位、对白；不要动态叙事用词。\n"
            "（3）严格遵守系统 Prompt 的三段式，只输出一段话的正文。\n"
        )
    else:
        user_body = (
            f"【警告】未拿到 Step 1 人物场景清单节选，只能凭下方摘录硬写；应尽量保守、避免发明新人设。\n\n"
            f"资产名称：{name}\n描述：{auxiliary}\n类型（character/scene/prop）：{tag}\n\n"
            f"{hint}\n\n"
            "请严格按系统说明中的「三段式语义」写成**一段连贯中文提示词**。\n"
            "只输出正文。"
        )

    # 统一通过 deepseek_chat 调用，内置重试与 key 管理（P0 修复：不再直接 requests.post）
    content = (deepseek_chat(_IMG_SINGLE_SYSTEM, user_body, temperature=0.8, max_tokens=500, timeout=180) or "").strip()
    if content:
        return content
    print(f"  [警告] DeepSeek 未返回资产提示词（{name}），prompt 保持为空")
    return ""


def _infer_empty_shot(refs: list[str]) -> bool:
    """空镜：分镜内不出现人物向 @（角色）；仅有场景/道具视为空镜。"""
    if not refs:
        return True
    return not any(is_likely_character(r) for r in refs)


def run(assets: dict | None, script: str, out_dir: str, research: dict | None = None) -> dict:
    """
    返回 prompt_map.json 结构 version 2：
      assets: { "图片N": { name, prompt, tag, kind, description } }
      shots:  { "shot_NN": { shot_num, refs_in_shot, empty_shot, ... } }

    会先调用 DeepSeek 生成/更新 `assets.json`（人物、场景、道具）。
    `assets` 参数仅作 DeepSeek 失败时的回退（通常为 Step 3 正则结果）。
    """
    catalog, inventory_note = _deepseek_extract_asset_catalog(research, script)
    if not _catalog_has_items(catalog) and assets:
        print("  使用 Step 3 正则提取结果作为资产清单回退")
        catalog = _legacy_assets_to_catalog(assets)
        inventory_note = (inventory_note or "") + "|fallback_step3"

    if out_dir:
        _write_assets_json(out_dir, catalog)

    inventory_raw, _ = _resolve_step1_inventory(research)
    inventory_authority = _cap_inventory_block(inventory_raw)

    hint_line = inventory_note.replace("\n", " ")[:220].strip()
    if hint_line:
        print(f"  Step 1 清单来源：{hint_line}")

    raw_rows = _catalog_to_prompt_rows(catalog)
    merged_items = _dedupe_merge_asset_rows(raw_rows)
    if len(merged_items) != len(raw_rows):
        print(
            f"  同名资产合并：{len(raw_rows)} 条 → {len(merged_items)} 个唯一（tag+名称）以确保一人一张定妆图 Prompt"
        )

    assets_out: dict[str, dict] = {}
    print(
        f"  资产提示词：{len(merged_items)} 个（DeepSeek **仅参考 Step 1 清单**，约 {len(inventory_authority)} 字符；分镜不参与人设）"
    )
    inv_label = inventory_note.strip() if inventory_note else "（未挂载 research.json）"

    for idx, item in enumerate(merged_items, start=1):
        ref_id = f"图片{idx}"
        desc = item.get("description") or item["name"]
        assets_out[ref_id] = {
            "name": item["name"],
            "prompt": _generate_single_prompt(
                item["name"],
                desc,
                item["tag"],
                inventory_authority,
                inventory_source_label=inv_label,
            ),
            "tag": item["tag"],
            "kind": "asset",
            "description": desc,
            "refs_from_script": item.get("refs") or [],
        }
        print(f"  @图片{idx}: {item['name']} ({item['tag']})")

    shots_out: dict[str, dict] = {}
    shot_blocks = _split_shots(script)

    for shot_num, shot_content in shot_blocks:
        refs = _mentions_in_shot(shot_content)
        empty_guess = _infer_empty_shot(refs)
        snum = int(shot_num)
        sk = f"shot_{str(snum).zfill(2)}"
        shots_out[sk] = {
            "shot_num": snum,
            "name": f"分镜{snum}",
            "refs_in_shot": refs,
            "empty_shot": empty_guess,
            "reference_tag_priority": ["scene", "character", "prop"],
            "kind": "shot",
            "tag": "shot",
        }

    print(f"  分镜元数据：{len(shots_out)} 条（无生成分镜图提示词）")

    return {
        "version": 2,
        "assets": assets_out,
        "shots": shots_out,
        "step4_inventory_source_hint": inventory_note[:500] if inventory_note else "",
        "step4_asset_catalog": {
            "characters": catalog.get("characters") or [],
            "scenes": catalog.get("scenes") or [],
            "props": catalog.get("props") or [],
        },
    }
