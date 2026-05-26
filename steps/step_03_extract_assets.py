"""
Step 3: 从 Step 2 分镜正文中整理资产索引（不调用 LLM，可选）

产出约定：正则解析 `@` 标签；`description` 为分镜摘录（最多 200 字）。
**权威资产清单（人物/场景/道具）由 Step 4 调用 DeepSeek 依据 Step 1「人物与场景清单」生成并写入 assets.json。**
未跑 Step 3 也可直接跑 Step 4（仅需 Step 2 分镜 + Step 1 纲要）。
"""
import re

_PROP_HINT = ("剑", "刀", "枪", "盾", "杖", "锤", "弓", "道具", "武器", "手机", "钥匙", "背包", "公文包", "信封", "酒杯", "项链")


def _classify_tag(tag: str) -> str:
    """返回 character | scene | prop"""
    if any(h in tag for h in _PROP_HINT):
        return "prop"

    known_scenes = {
        "办公区", "工位", "小巷", "街道", "屋顶", "城市", "室外", "室内",
        "深夜", "清晨", "走廊", "电梯", "会议室", "全景", "背景", "环境",
    }
    known_char_prefixes = (
        "阿", "张", "王", "李", "刘", "陈", "杨", "赵", "黄", "周",
        "吴", "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马",
        "罗", "梁", "宋", "郑", "谢", "韩", "唐", "冯", "于", "董", "小",
    )

    if tag in known_scenes:
        return "scene"
    if any(tag.startswith(p) for p in known_char_prefixes):
        return "character"
    if tag in ["主角", "配角", "反派", "旁白", "同事A", "同事B", "主管", "领导"]:
        return "character"
    if any(kw in tag for kw in ["全景", "工位", "办公", "区", "背景", "会议室", "走廊"]):
        return "scene"
    # 默认按角色处理（与旧逻辑一致）；极短且无场景词时仍可能是小道具，已在 _PROP_HINT 覆盖常见道具字
    return "character"


def run(script: str) -> dict:
    """
    返回资产列表:
    {
        "characters": [...],
        "scenes": [...],
        "props": [...],
    }
    """
    char_pattern = re.compile(r"@([\u4e00-\u9fffA-Za-z][\u4e00-\u9fffA-Za-z0-9]*)")
    all_refs = char_pattern.findall(script)

    characters: dict[str, dict] = {}
    scenes: dict[str, dict] = {}
    props: dict[str, dict] = {}

    shots = re.split(r"分镜\s*\d+[｜|]\s*\d+\s*秒", script)

    def touch(bucket: dict, tag: str) -> None:
        if tag not in bucket:
            bucket[tag] = {"name": tag, "refs": [], "description": ""}

    for tag in all_refs:
        kind = _classify_tag(tag)
        if kind == "scene":
            touch(scenes, tag)
        elif kind == "prop":
            touch(props, tag)
        else:
            touch(characters, tag)

    for i, shot in enumerate(shots[1:], 1):
        shot_refs = char_pattern.findall(shot)
        for ref in set(shot_refs):
            if ref in characters:
                characters[ref]["refs"].append(f"分镜{i}")
            elif ref in scenes:
                scenes[ref]["refs"].append(f"分镜{i}")
            elif ref in props:
                props[ref]["refs"].append(f"分镜{i}")

    for asset_dict in list(characters.values()) + list(scenes.values()) + list(props.values()):
        name = asset_dict["name"]
        idx = script.find(f"@{name}")
        if idx >= 0:
            asset_dict["description"] = script[idx : idx + 200].strip()

    char_list = list(characters.values())
    scene_list = list(scenes.values())
    prop_list = list(props.values())

    print(f"  提取资产：{len(char_list)} 角色 / {len(scene_list)} 场景 / {len(prop_list)} 道具")
    for c in char_list:
        print(f"    @角色 {c['name']} → {', '.join(c['refs'][:3])}{'...' if len(c['refs']) > 3 else ''}")
    for s in scene_list:
        print(f"    @场景 {s['name']} → {', '.join(s['refs'][:3])}{'...' if len(s['refs']) > 3 else ''}")
    for p in prop_list:
        print(f"    @道具 {p['name']} → {', '.join(p['refs'][:3])}{'...' if len(p['refs']) > 3 else ''}")

    return {
        "characters": char_list,
        "scenes": scene_list,
        "props": prop_list,
        "total_chars": len(char_list),
        "total_scenes": len(scene_list),
        "total_props": len(prop_list),
    }
