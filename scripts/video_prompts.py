"""
分镜脚本解析 + 图生视频提示词生成

输入：分镜脚本（含 @图片N 角色引用）
输出：每镜头的 Seedance 2.0 视频提示词
"""
import re, json
from typing import Dict, List

# ── 解析器 ──────────────────────────────────────────────────

def parse_storyboard(raw: str) -> Dict:
    """
    解析分镜脚本，返回结构化数据
    支持格式：
      - 演员行: 演员: @角色名=场景, @角色名=场景
      - 场景行: 场景: L1=描述, L2=描述
      - 道具行: 道具: P1=描述, P2=描述
      - 镜头行: S01 内容...
    """
    actors = {}   # name -> ref_id
    scenes = {}   # scene_id -> description
    props = {}    # prop_id -> description
    shots = []    # list of {id, text, refs}

    img_ref = re.compile(r"@(\S+)")
    lines = raw.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 演员行: 演员: @name=ref, @name2=ref2, ...
        if line.startswith("演员:") or re.match(r"^@", line):
            content = re.sub(r"^演员:\s*", "", line)
            # 解析 @name=ref 格式，支持多对逗号分隔
            # ref 用 [^,\s]+ 避免吞掉逗号
            pairs = re.findall(r"@(\S+?)=([^,\s]+)", content)
            for name, ref in pairs:
                actors[name] = ref
            continue

        # 场景行: 场景: L1=desc, L2=desc
        if line.startswith("场景:") or re.match(r"^L\d+=", line):
            content = re.sub(r"^场景:\s*", "", line)
            pairs = re.findall(r"(L\d+)=([^,]+)", content)
            for sid, desc in pairs:
                scenes[sid] = desc.strip()
            continue

        # 道具行: 道具: P1=desc, P2=desc
        if line.startswith("道具:") or re.match(r"^P\d+=", line):
            content = re.sub(r"^道具:\s*", "", line)
            pairs = re.findall(r"(P\d+)=([^,]+)", content)
            for pid, desc in pairs:
                props[pid] = desc.strip()
            continue

        # 镜头行: S01 内容...
        m = re.match(r"^(S\d+)\s+(.+)", line)
        if m:
            shot_text = m.group(2)
            refs = img_ref.findall(shot_text)
            shots.append({"id": m.group(1), "text": shot_text, "refs": refs})

    return {"actors": actors, "scenes": scenes, "props": props, "shots": shots}


def build_video_prompt(scene_id: str, role_map: Dict[str,str],
                       shot_text: str, duration_ms: int) -> str:
    """
    将分镜文字转换为 Seedance 2.0 可用的视频提示词
    替换 @角色名 为 <role>Rn</role>
    替换 @图片N 格式为 <role>Rn</role>  (N -> 角色表里映射的ID)
    """
    prompt = shot_text
    # 替换 @角色名 -> <role>Rn</role>
    for ref, role_id in role_map.items():
        prompt = prompt.replace(f"@{ref}", f"<role>{role_id}</role>")
    # 替换 @图片N (如 @图片1) -> 找到对应的角色 asset_id
    img_ref_pattern = re.compile(r"@图片(\d+)")
    def replace_img_ref(m):
        idx = int(m.group(1))
        # 角色按顺序排列: A1, A2, A3...
        # 这里简单处理：idx 1=A1, 2=A2...
        # 实际应以资产表里的顺序为准
        return f"<role>A{idx}</role>"
    prompt = img_ref_pattern.sub(replace_img_ref, prompt)

    location_tag = f"<location>{scene_id}</location>"
    duration_tag = f"<duration-ms>{duration_ms}</duration-ms>"

    header = (
        "画面风格和类型: 真人写实, 电影风格, 冷色调, 男频科幻/游戏\n"
        "生成一个由以下1个分镜组成的视频。\n"
        f"本片段场景设定在: {location_tag}\n\n"
    )
    body = (
        f"分镜1{duration_tag}:\n"
        f"{prompt}\n"
        "────────────────────────────────────────"
    )
    return header + body


if __name__ == "__main__":
    # 简单自测
    sample = """
    @阿强=L1, @吸血鬼1=L2
    L1=深夜科技公司开放式办公区
    L2=霓虹灯照亮的小巷
    S01 16:9，@阿强坐在开放式办公区工位，盯屏幕发呆
    S02 16:9，@阿强站在霓虹灯照亮的小巷中央，周围是吸血鬼
    """
    parsed = parse_storyboard(sample)
    print(json.dumps(parsed, ensure_ascii=False, indent=2))
