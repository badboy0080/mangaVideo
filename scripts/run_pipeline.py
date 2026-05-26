#!/usr/bin/env python3
"""
manga-pipeline 协调器
用法: python run_pipeline.py "失业警报：当AI开始抢工作" 120
  参数1: 主题
  参数2: 目标总时长（秒）
"""
import sys, os, json, uuid, time, re
sys.path.insert(0, os.path.dirname(__file__))

from init_db import (
    init_db, create_project, upsert_asset, upsert_storyboard,
    update_storyboard_video, update_project_final_mp4,
    get_assets, get_storyboard, get_project
)
from deepseek_caller import call_deepseek
from seedream_caller import call_seedream
from seedance_caller import call_seedance
from video_prompts import parse_storyboard, build_video_prompt

# ── 加载提示词模板 ─────────────────────────────────────────
PROMPT_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")

def load_prompt(name: str) -> str:
    with open(os.path.join(PROMPT_DIR, f"{name}.txt"), encoding="utf-8") as f:
        return f.read()

# ── 阶段 1: 主题研究 ───────────────────────────────────────
def phase_research(theme: str) -> str:
    print(f"\n[Phase 1] 研究主题: {theme}")
    # 简单搜索背景（可用 web_search skill，实际项目可换为真实搜索）
    # 这里留空，DeepSeek 写脚本时会自己补全背景
    return f"围绕主题「{theme}」进行创作"


# ── 阶段 2: DeepSeek 写分镜脚本 ───────────────────────────
def phase_script(theme: str, total_duration_s: int) -> str:
    print(f"\n[Phase 2] 生成 {total_duration_s}s 分镜脚本")
    system_prompt = load_prompt("deepseek_script_system")
    user_prompt = load_prompt("deepseek_script_user").format(
        theme=theme,
        total_duration_s=total_duration_s
    )
    script = call_deepseek(system_prompt, user_prompt)
    return script


# ── 阶段 3: 解析资产 ───────────────────────────────────────
def phase_parse_assets(script: str, project_id: str) -> dict:
    print(f"\n[Phase 3] 解析资产")
    parsed = parse_storyboard(script)

    # 写入演员到 DB（metadata 记下关联场景）
    # 演员按插入顺序分配 A1, A2, A3...
    # name_to_aid 必须在 Phase 5 里用，要保证顺序一致
    name_to_aid_map = {}
    for i, (name, scene_ref) in enumerate(parsed["actors"].items()):
        asset_id = f"A{i+1}"
        name_to_aid_map[name] = asset_id
        metadata = {"scene_ref": scene_ref}
        upsert_asset(project_id, asset_id, "actor", name, prompt="（待生成）",
                     metadata=metadata)
    # 场景按脚本中 ID 直接入库（L1, L2, L3...）

    # 写入场景到 DB
    for sid, desc in parsed["scenes"].items():
        upsert_asset(project_id, sid, "scene", desc, prompt="（待生成）")

    # 写入道具到 DB
    for pid, desc in parsed.get("props", {}).items():
        upsert_asset(project_id, pid, "prop", desc, prompt="（待生成）")

    # 写入分镜
    n = len(parsed["shots"])
    duration_per_shot = 0
    for shot in parsed["shots"]:
        upsert_storyboard(
            project_id, shot["id"], shot["id"],
            shot["text"], shot["refs"],
            duration_ms=duration_per_shot
        )

    return parsed


# ── 阶段 4: 生成资产图 ────────────────────────────────────
def phase_generate_images(project_id: str, parsed: dict, theme: str) -> dict:
    print(f"\n[Phase 4] 生成资产图片")
    # 调用 DeepSeek 生成每项资产的详细生图提示词
    asset_prompt_tpl = load_prompt("asset_prompt_user")
    system_prompt    = load_prompt("asset_prompt_system")

    asset_map = {}  # asset_ref -> local_path

    all_assets = []
    for name, _ in parsed["actors"].items():
        all_assets.append(("actor", name))
    for sid, desc in parsed["scenes"].items():
        all_assets.append(("scene", desc))

    for i, (asset_type, name_or_desc) in enumerate(all_assets, 1):
        asset_id = f"A{i}" if asset_type == "actor" else f"L{i-len(parsed['actors'])}"
        prompt = call_deepseek(
            system_prompt,
            asset_prompt_tpl.format(
                asset_type=asset_type,
                name_or_desc=name_or_desc,
                theme=theme
            )
        )
        # 调用 Seedream（新版签名：prompt + output_dir + filename）
        output_dir = os.path.join(os.path.dirname(__file__), "..",
                                  "output", project_id, "assets")
        os.makedirs(output_dir, exist_ok=True)
        try:
            result = call_seedream(
                prompt=prompt,
                output_dir=output_dir,
                output_filename=asset_id
            )
            img_path = result.get("image_path")
        except Exception as e:
            print(f"  [!] Seedream failed for {asset_id}: {e}")
            img_path = None

        upsert_asset(project_id, asset_id, asset_type,
                     name_or_desc, prompt,
                     image_local_path=img_path)
        if img_path:
            asset_map[asset_id] = img_path

    return asset_map


# ── 阶段 5: 生成视频片段 ─────────────────────────────────
def phase_videos_and_concat(project_id: str, total_duration_s: int):
    print(f"\n[Phase 5] 生成视频片段")
    shots = get_storyboard(project_id)
    assets = get_assets(project_id)

    # asset_id -> image_local_path 映射
    asset_image_map = {a["id"]: a["image_local_path"] for a in assets if a["image_local_path"]}
    # name -> asset_id 映射（角色名引用）
    name_to_aid   = {a["name"]: a["id"] for a in assets if a["type"] == "actor"}
    # 演员列表（保持顺序）
    actors = [a for a in assets if a["type"] == "actor"]
    # 场景列表
    scenes = {a["id"]: a["name"] for a in assets if a["type"] == "scene"}

    n = len(shots)
    duration_per_shot = int(total_duration_s * 1000 / n) if n else 8000
    duration_sec      = int(total_duration_s / n) if n else 8

    output_dir = os.path.join(os.path.dirname(__file__), "..",
                              "output", project_id, "videos")
    os.makedirs(output_dir, exist_ok=True)

    video_paths = []

    for i, shot in enumerate(shots):
        shot_text = shot["script_text"]

        # 替换 @角色名 → @A1, @A2 ...
        for name, aid in name_to_aid.items():
            shot_text = shot_text.replace(f"@{name}", f"@{aid}")

        # 替换 @图片N → @A{N}
        def replace_img_n(m):
            idx = int(m.group(1))
            return f"@A{idx}" if idx <= len(actors) else m.group(0)
        shot_text = re.sub(r"@图片(\d+)", replace_img_n, shot_text)

        # 查本镜头涉及的场景（从 asset_refs 里推断，fallback L1）
        scene_id = "L1"
        for s_id in scenes:
            if s_id in shot_text:
                scene_id = s_id
                break

        video_prompt = build_video_prompt(
            scene_id=scene_id,
            role_map={a["name"]: a["id"] for a in assets if a["type"] == "actor"},
            shot_text=shot_text,
            duration_ms=duration_per_shot
        )

        # 找本镜头引用的演员图片作为参考图
        ref_imgs = []
        for aid in name_to_aid.values():
            if f"@{aid}" in shot_text and aid in asset_image_map:
                ref_imgs.append(asset_image_map[aid])

        # 生成视频文件路径
        video_path = os.path.join(output_dir, f"{shot['id']}.mp4")
        try:
            result = call_seedance(
                video_prompt=video_prompt,
                reference_image_paths=ref_imgs,
                output_dir=output_dir,
                duration=duration_sec,
                ratio="16:9"
            )
            video_path = result.get("video_path", video_path)
            print(f"  [OK] {shot['id']} -> {os.path.basename(video_path)}")
        except Exception as e:
            print(f"  [!] Seedance failed for {shot['id']}: {e}")
            video_path = None

        update_storyboard_video(shot["id"], video_prompt, video_path)
        if video_path and os.path.exists(video_path):
            video_paths.append(video_path)

    # ── FFmpeg 拼合 ───────────────────────────────────────
    if len(video_paths) < 2:
        print(f"  [!] 视频片段不足（{len(video_paths)}），跳过拼合")
        return

    concat_list = os.path.join(output_dir, "concat.txt")
    output_mp4  = os.path.join(os.path.dirname(__file__), "..",
                               "output", project_id, f"{project_id}.mp4")

    with open(concat_list, "w") as f:
        for p in video_paths:
            f.write(f"file '{p}'\n")

    ret = os.system(
        f"ffmpeg -y -f concat -safe 0 -i {concat_list} "
        f"-c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p {output_mp4} 2>&1"
    )
    if ret == 0:
        update_project_final_mp4(project_id, output_mp4)
        print(f"\n[OK] Final MP4: {output_mp4}")
    else:
        print(f"  [!] FFmpeg failed (exit {ret}), final MP4 not updated")



# ── 主流程 ─────────────────────────────────────────────────
def run(theme: str, total_duration_s: int):
    project_id = f"proj_{uuid.uuid4().hex[:8]}"
    print(f"=== Manga Pipeline Start | project_id={project_id} ===")

    init_db()
    create_project(project_id, theme, total_duration_s)

    background = phase_research(theme)
    script     = phase_script(theme, total_duration_s)

    # 保存原始脚本
    script_path = os.path.join(os.path.dirname(__file__), "..",
                              "output", project_id, "script.txt")
    os.makedirs(os.path.dirname(script_path), exist_ok=True)
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)
    print(f"[Phase 2] 脚本已存: {script_path}")

    parsed    = phase_parse_assets(script, project_id)
    asset_map = phase_generate_images(project_id, parsed, theme)
    phase_videos_and_concat(project_id, total_duration_s)

    print(f"\n=== Pipeline Done | project_id={project_id} ===")
    return project_id


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python run_pipeline.py <主题> <目标时长(秒)>")
        sys.exit(1)
    run(sys.argv[1], int(sys.argv[2]))
