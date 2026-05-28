"""
Step 6: 生成分镜视频提示词（Seedance）

产出约定：
- 入库 `prompt`：优先 Step 6 DeepSeek 润色正文；润色无效时用 Step 2 解析出的 I2V 原文（仍为 LLM 产出）。
- 禁止本地前缀拼接、禁止 `_build_narrative` 式叙事回退、禁止 `_infer_style` 等启发式文案写入 prompt。
- `duration_ms` / 参考图路径 / `@` 解析为整理字段。见 `steps.step_output_policy`。
"""
import os
import re
import sqlite3

from pypinyin import lazy_pinyin

from steps.deepseek_chat import chat as deepseek_chat
from steps.prompt_config import load_registered_system_prompt
from steps.script_split import split_shots_standard
from steps.utils import is_likely_character

_STEP06_POLISH = load_registered_system_prompt("step_04_video.system")


def run(script_data: dict, img_results: dict, db_path: str, out_dir: str) -> dict:
    """
    img_results: Step 5 产出，资产中文名、「图片N」等 -> 本地路径。
    db_path: SQLite 数据库路径。
    """
    _ = out_dir
    script = script_data["script"]

    storyboard_assets = script_data.get("assets") or {}
    asset_catalog = script_data.get("asset_catalog") or {}
    name_to_path = _build_image_alias_map(img_results, storyboard_assets, asset_catalog)
    token_to_display = _build_token_display_map(storyboard_assets, asset_catalog)
    character_aliases = _build_character_aliases(storyboard_assets, asset_catalog)

    char_pattern = re.compile(r"@([\u4e00-\u9fffA-Za-z][\u4e00-\u9fffA-Za-z0-9_]*)")
    all_chars_in_script = char_pattern.findall(script)
    unique_chars = [c for c in dict.fromkeys(all_chars_in_script) if _is_character_ref(c, character_aliases)]

    role_nick = {}
    for i, c in enumerate(unique_chars, 1):
        role_nick[c] = f"R{i}"

    video_prompts = {}
    shot_blocks = split_shots_standard(script)

    for shot_num, header_seconds, shot_content in shot_blocks:
        shot_id = f"shot_{str(shot_num).zfill(2)}"

        duration_sec, duration_src = _resolve_duration_seconds(
            header_seconds,
            shot_content,
        )
        duration_ms = int(duration_sec * 1000)

        mentions_ordered = list(dict.fromkeys(char_pattern.findall(shot_content)))
        chars_here = [x for x in mentions_ordered if x in role_nick]
        non_char_refs = [x for x in mentions_ordered if x not in role_nick]

        paths_ordered: list[str] = []
        for m in mentions_ordered:
            pth = name_to_path.get(m, "") or _resolve_semantic_alias(m, name_to_path, asset_catalog)
            if pth and pth not in paths_ordered:
                paths_ordered.append(pth)
        reference_image_paths = paths_ordered[:9]
        if mentions_ordered and not reference_image_paths:
            print(f"    [提示] {shot_id} 本分镜正文含 @引用，但未匹配到本地参考图（请核对资产名称与 @ 完全一致）")

        raw_i2v = _extract_i2v_prompt(shot_content)
        dialogues = _extract_dialogues(shot_content, token_to_display)
        i2v_note = ""
        used_polish = False
        core_body = ""

        if raw_i2v and not _looks_like_i2v_placeholder(raw_i2v):
            polished = _polish_i2v_block(
                raw_i2v, shot_num=int(shot_num), segment_seconds=duration_sec
            ).strip()
            if len(polished) >= 20:
                core_body = polished
                used_polish = True
                i2v_note = raw_i2v[:500] + ("…" if len(raw_i2v) > 500 else "")
            else:
                core_body = raw_i2v.strip()
                i2v_note = "（润色未返回有效正文，已用 Step02 I2V 原文）"
                print(f"    [提示] {shot_id} DeepSeek 润色过短或为空，改用 I2V 原文")
        elif raw_i2v:
            i2v_note = "（Step02 I2V 段落疑似占位/过短，未写入 prompt）"
            print(f"    [警告] {shot_id} I2V 无效，prompt 保持为空（请重跑 Step 2 或检查分镜格式）")
        else:
            i2v_note = "（未解析到 Step02 图生视频 I2V 正文，prompt 保持为空）"
            print(f"    [警告] {shot_id} 未找到 I2V 块，prompt 保持为空")

        final_prompt = core_body

        video_prompts[shot_id] = {
            "prompt": final_prompt,
            "reference_image_paths": reference_image_paths,
            "duration_ms": duration_ms,
            "chars_in_shot": chars_here,
            "scenes_in_shot": non_char_refs,
            "dialogues_in_shot": dialogues,
            "style": "",
            "i2v_source": i2v_note,
            "duration_source": duration_src,
            "prompt_source": "step06_polish" if used_polish else ("step02_i2v" if core_body else "empty"),
        }

        from db import insert_video_clip

        image_refs_for_db = {
            f"<role>{role_nick.get(c, c)}</role>": name_to_path.get(c, "")
            for c in chars_here
        }
        tconn = sqlite3.connect(db_path)
        try:
            insert_video_clip(tconn, shot_id, final_prompt, image_refs_for_db)
        finally:
            tconn.close()

        print(f"  {shot_id} [{duration_ms/1000:.0f}s] duration←{duration_src}")
        print(f"    角色: {', '.join(chars_here) or '无'}")
        print(f"    参考图({len(reference_image_paths)}): {', '.join(os.path.basename(p) for p in reference_image_paths) or '无'}")
        if dialogues:
            print(f"    台词: {' / '.join(d['cue'] for d in dialogues)}")
        if core_body:
            src = "Step06 润色" if used_polish else "Step02 I2V 原文"
            print(f"    prompt 来源: {src}（{len(core_body)} 字）")
        else:
            print("    prompt 来源: 空（无 LLM 可用正文）")

    return video_prompts


def _norm_key(value: str) -> str:
    return re.sub(r"[\s_：:，,。.\-]+", "", str(value or "").strip()).casefold()


def _name_aliases(name: str) -> set[str]:
    raw = str(name or "").strip().lstrip("@")
    if not raw:
        return set()
    aliases = {raw, _norm_key(raw)}
    if re.search(r"[\u4e00-\u9fff]", raw):
        py = lazy_pinyin(raw, errors="ignore")
        if py:
            snake = "_".join(py)
            compact = "".join(py)
            family_given = f"{py[0]}_{''.join(py[1:])}" if len(py) > 2 else snake
            aliases.update(
                {
                    snake,
                    compact,
                    family_given,
                    snake.casefold(),
                    compact.casefold(),
                    family_given.casefold(),
                    snake.title(),
                    compact.title(),
                    family_given.title(),
                    _norm_key(snake),
                    _norm_key(compact),
                    _norm_key(family_given),
                }
            )
    return {x for x in aliases if x}


def _add_alias(mapping: dict[str, str], alias: str, path: str) -> None:
    if not alias or not path:
        return
    mapping.setdefault(alias, path)
    mapping.setdefault(_norm_key(alias), path)


def _build_image_alias_map(
    img_results: dict,
    storyboard_assets: dict,
    asset_catalog: dict,
) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for ref_id, path in (img_results or {}).items():
        rid = str(ref_id)
        pth = str(path)
        _add_alias(mapping, rid, pth)
        _add_alias(mapping, rid.replace("图片_", "").strip(), pth)
        for alias in _name_aliases(rid):
            _add_alias(mapping, alias, pth)

    for ref_id, meta in (storyboard_assets or {}).items():
        if not isinstance(meta, dict):
            continue
        path = mapping.get(str(ref_id)) or mapping.get(_norm_key(str(ref_id)))
        name = str(meta.get("name") or "").strip()
        if not path and name:
            path = mapping.get(name) or mapping.get(_norm_key(name))
        if not path:
            continue
        _add_alias(mapping, str(ref_id), path)
        for alias in _name_aliases(name):
            _add_alias(mapping, alias, path)

    for bucket in ("characters", "scenes", "props"):
        for item in (asset_catalog or {}).get(bucket, []) or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            path = mapping.get(name) or mapping.get(_norm_key(name))
            if not path:
                continue
            for alias in _name_aliases(name):
                _add_alias(mapping, alias, path)
    return mapping


def _build_token_display_map(storyboard_assets: dict, asset_catalog: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for meta in (storyboard_assets or {}).values():
        if not isinstance(meta, dict):
            continue
        name = str(meta.get("name") or "").strip()
        if not name:
            continue
        for alias in _name_aliases(name):
            out.setdefault(alias, name)
            out.setdefault(_norm_key(alias), name)
    for bucket in ("characters", "scenes", "props"):
        for item in (asset_catalog or {}).get(bucket, []) or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            for alias in _name_aliases(name):
                out.setdefault(alias, name)
                out.setdefault(_norm_key(alias), name)
    return out


def _build_character_aliases(storyboard_assets: dict, asset_catalog: dict) -> set[str]:
    aliases: set[str] = set()
    for meta in (storyboard_assets or {}).values():
        if not isinstance(meta, dict) or meta.get("tag") != "character":
            continue
        for alias in _name_aliases(str(meta.get("name") or "")):
            aliases.add(alias)
            aliases.add(_norm_key(alias))
    for item in (asset_catalog or {}).get("characters", []) or []:
        if not isinstance(item, dict):
            continue
        for alias in _name_aliases(str(item.get("name") or "")):
            aliases.add(alias)
            aliases.add(_norm_key(alias))
    return aliases


def _is_character_ref(name: str, character_aliases: set[str]) -> bool:
    raw = str(name or "").strip()
    return raw in character_aliases or _norm_key(raw) in character_aliases or is_likely_character(raw)


_EN_ZH_HINTS: dict[str, tuple[str, ...]] = {
    "modern": ("现代",),
    "ancient": ("古", "晋朝", "古代"),
    "classroom": ("教室", "课堂"),
    "pond": ("池塘", "水池"),
    "courtyard": ("庭院", "院"),
    "office": ("办公室", "办公"),
    "room": ("房间", "室内"),
    "river": ("河", "江"),
    "bank": ("河岸", "岸边"),
    "battle": ("战场", "战斗"),
    "field": ("场", "平原"),
    "camp": ("营地",),
    "forest": ("森林", "树林"),
    "street": ("街", "街道"),
    "brush": ("毛笔", "笔"),
    "writing": ("书法", "写字"),
    "ink": ("墨",),
    "inkstone": ("墨砚", "砚"),
    "wood": ("木",),
    "wooden": ("木",),
    "board": ("木板", "板"),
    "paper": ("宣纸", "纸"),
    "desk": ("桌", "课桌"),
    "table": ("桌", "石桌"),
}


def _resolve_semantic_alias(ref: str, mapping: dict[str, str], asset_catalog: dict) -> str:
    words = [w for w in re.split(r"[_\W]+", str(ref or "").casefold()) if w]
    hints: list[str] = []
    for w in words:
        hints.extend(_EN_ZH_HINTS.get(w, ()))
    if not hints:
        return ""

    best_name = ""
    best_score = 0
    tied = False
    for bucket in ("characters", "scenes", "props"):
        for item in (asset_catalog or {}).get(bucket, []) or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "")
            haystack = name + "\n" + str(item.get("description") or "")
            score = sum(1 for h in hints if h and h in haystack)
            if score > best_score:
                best_name = name
                best_score = score
                tied = False
            elif score and score == best_score:
                tied = True
    if not best_name or tied:
        return ""
    return mapping.get(best_name) or mapping.get(_norm_key(best_name)) or ""


_DIALOGUE_ROW_RE = re.compile(r"^\s*\|\s*台词\s*\|\s*(.*?)\s*\|\s*$", re.MULTILINE)
_DIALOGUE_SPLIT_RE = re.compile(r"[；;]\s*")
_QUOTED_DIALOGUE_RE = re.compile(
    r"@?([\u4e00-\u9fffA-Za-z][\u4e00-\u9fffA-Za-z0-9_]*)\s*(?:对白)?\s*[：:]?\s*[“\"]([^”\"]+)[”\"]"
)
_EMOTION_RE = re.compile(r"(愉快|开心|高兴|坚定|疑惑|惊讶|低声|大声|焦急|平静|温柔|严肃|兴奋|害怕|失落|冷静|急切|自信)")


def _display_name(token: str, token_to_display: dict[str, str]) -> str:
    raw = str(token or "").strip().lstrip("@")
    return token_to_display.get(raw) or token_to_display.get(_norm_key(raw)) or raw


def _clean_dialogue_text(text: str) -> str:
    s = str(text or "").strip()
    s = s.strip("`")
    s = s.strip("{}")
    s = s.strip("“”\"'")
    return s.strip()


def _dialogue_cue(speaker: str, line: str, context: str) -> str:
    emotion_m = _EMOTION_RE.search(context or "")
    if emotion_m:
        return f"{speaker}{emotion_m.group(1)}的说“{line}”"
    return f"{speaker}说“{line}”"


def _extract_dialogues(shot_content: str, token_to_display: dict[str, str]) -> list[dict[str, str]]:
    rows: list[str] = []
    for m in _DIALOGUE_ROW_RE.finditer(shot_content or ""):
        body = m.group(1).strip()
        if body and body not in ("无对白", "无"):
            rows.append(body)
    if not rows:
        return []

    out: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        quoted_matches = list(_QUOTED_DIALOGUE_RE.finditer(row))
        if quoted_matches:
            for m in quoted_matches:
                speaker = _display_name(m.group(1), token_to_display)
                line = _clean_dialogue_text(m.group(2))
                key = (speaker, line)
                if line and key not in seen:
                    seen.add(key)
                    out.append({"speaker": speaker, "line": line, "cue": _dialogue_cue(speaker, line, shot_content)})
            continue
        for part in _DIALOGUE_SPLIT_RE.split(row):
            chunk = part.strip()
            if not chunk or chunk in ("无对白", "无"):
                continue
            m = re.match(r"@?([\u4e00-\u9fffA-Za-z][\u4e00-\u9fffA-Za-z0-9_]*)\s*[：:]\s*(.+)", chunk)
            if m:
                speaker = _display_name(m.group(1), token_to_display)
                line = _clean_dialogue_text(m.group(2))
            else:
                speaker = "角色"
                line = _clean_dialogue_text(chunk)
            if not line:
                continue
            key = (speaker, line)
            if key in seen:
                continue
            seen.add(key)
            out.append({"speaker": speaker, "line": line, "cue": _dialogue_cue(speaker, line, shot_content)})
    return out


def _inject_dialogues(prompt: str, dialogues: list[dict[str, str]]) -> str:
    body = (prompt or "").strip()
    cues = [d["cue"] for d in dialogues if d.get("cue") and d["cue"] not in body]
    if not body or not cues:
        return body
    dialogue_text = "。".join(cues) + "。"
    marker = re.search(r"(?:no music,\s*no subtitles(?:,\s*no text overlay)?|no subtitles)", body, re.IGNORECASE)
    if marker:
        return (body[: marker.start()].rstrip("。 \n") + "。" + dialogue_text + body[marker.start():]).strip()
    return (body.rstrip("。") + "。" + dialogue_text).strip()


SEEDANCE_SEGMENT_SEC_MIN = 4
SEEDANCE_SEGMENT_SEC_MAX = 15


def _clamp_segment_seconds(sec: int) -> int:
    return max(SEEDANCE_SEGMENT_SEC_MIN, min(SEEDANCE_SEGMENT_SEC_MAX, sec))


def _extract_duration_body(shot_content: str) -> int | None:
    """正文内兜底：<duration-ms> 或 「时长」「X 秒」表述。"""
    m = re.search(r"<duration-ms>(\d+)</duration-ms>", shot_content)
    if m:
        return max(1, int(m.group(1)) // 1000)
    m2 = re.search(r"时长\s*[^\d]{0,6}(\d+)\s*秒", shot_content)
    if m2:
        return max(1, int(m2.group(1)))
    return None


def _resolve_duration_seconds(
    header_seconds: int | None,
    shot_content: str,
) -> tuple[int, str]:
    """与 Step02 对齐：优先分镜标题行「N｜X 秒」；读入后夹紧到 Seedance 单段区间。"""
    raw: int | None = None
    src = "default"
    if header_seconds is not None:
        raw = header_seconds
        src = "header"
    else:
        raw = _extract_duration_body(shot_content)
        if raw is not None:
            src = "body"
    if raw is None:
        raw = 10
        src = "default"
    clamped = _clamp_segment_seconds(raw)
    return clamped, src if clamped == raw else f"{src}_clamped"


def _extract_i2v_prompt(shot_content: str) -> str:
    """截取「图生视频（I2V）」整段复制之后到下一分隔或文末的正文。"""
    m = re.search(
        r"图生视频\s*[（(]?\s*I2V\s*[）)]?\s*[—\-–]*\s*整段复制[^\n]*\n+([\s\S]+?)"
        r"(?=\n\s*-{3,}|\n\s*(?:#{1,6}\s*)?分镜\s*\d+\s*[｜|]|\n\s*##\s*镜头\s*\d+|\Z)",
        shot_content,
        re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return ""
    return m.group(1).strip()


def _looks_like_i2v_placeholder(s: str) -> bool:
    t = (s or "").strip()
    if len(t) < 12:
        return True
    if t.startswith("[") and ("完整" in t[:120] or "整段复制" in t[:120] or "禁止" in t[:120]):
        return True
    return False


def _polish_i2v_block(raw: str, shot_num: int, segment_seconds: int) -> str:
    """DeepSeek 润色；无 Key 或失败则返回空串，由调用方沿用 Step02 I2V 原文。"""
    user = (
        f"分镜编号：{shot_num}\n本段目标成片时长：约 {segment_seconds} 秒（Seedance 单段 4～15 秒内），"
        "I2V 描述中时序与动作量请与该时长匹配。\n\n【I2V 原文】\n"
        f"{raw.strip()}"
    )
    polished = deepseek_chat(
        _STEP06_POLISH,
        user,
        temperature=0.35,
        max_tokens=2000,
        timeout=90,
    ).strip()
    if len(polished) >= 20:
        return polished
    return ""
