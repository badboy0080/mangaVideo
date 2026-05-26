#!/usr/bin/env python3
"""
Manga Pipeline Demo - 端到端 Mock 验证
跑通全流程，不调用任何真实 API
"""
import sys, os, json, uuid, time

# ── Mock 注入 ──────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mock_api import apply_mocks
apply_mocks()

# ── 现在导入真实模块（已被 Mock patch） ────────────────────
from init_db import (
    init_db, create_project, upsert_asset, upsert_storyboard,
    update_storyboard_video, update_project_final_mp4,
    get_assets, get_storyboard, get_project
)
from deepseek_caller import call_deepseek
from seedream_caller import call_seedream
from video_prompts import parse_storyboard, build_video_prompt

PROMPT_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")

def load_prompt(name: str) -> str:
    with open(os.path.join(PROMPT_DIR, f"{name}.txt"), encoding="utf-8") as f:
        return f.read()

def run(theme: str, total_duration_s: int):
    project_id = f"demo_{uuid.uuid4().hex[:8]}"
    print(f"\n{'='*60}")
    print(f"  MANGA PIPELINE DEMO | project_id={project_id}")
    print(f"  主题: {theme} | 时长: {total_duration_s}s")
    print(f"{'='*60}")

    # ── DB Init ──────────────────────────────────────────────
    init_db()
    create_project(project_id, theme, total_duration_s)
    print("[OK] 数据库初始化")

    # ── Phase 1: 研究（Mock，跳过真实搜索） ──────────────────
    print("\n[Phase 1] 主题研究")
    background = f"围绕主题「{theme}」进行创作，构建程序员失业+超自然元素的故事"
    print(f"  背景信息: {background[:50]}...")

    # ── Phase 2: DeepSeek 生成分镜脚本 ───────────────────────
    print("\n[Phase 2] 生成分镜脚本 (DeepSeek V4 Pro)")
    system_prompt = load_prompt("deepseek_script_system")
    user_prompt = load_prompt("deepseek_script_user").format(
        theme=theme,
        total_duration_s=total_duration_s
    )
    script = call_deepseek(system_prompt, user_prompt)
    print(f"  脚本长度: {len(script)} chars")

    # 保存脚本
    script_path = os.path.join(os.path.dirname(__file__), "..",
                               "output", project_id, "script.txt")
    os.makedirs(os.path.dirname(script_path), exist_ok=True)
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)
    print(f"  脚本已存: {script_path}")

    # ── Phase 3: 解析资产 ───────────────────────────────────
    print("\n[Phase 3] 解析资产 (演员/场景/道具)")
    parsed = parse_storyboard(script)
    print(f"  演员: {list(parsed['actors'].keys())}")
    print(f"  场景: {list(parsed['scenes'].keys())}")
    print(f"  分镜: {[s['id'] for s in parsed['shots']]}")

    # 写入演员
    for name, ref in parsed["actors"].items():
        asset_id = f"A{list(parsed['actors']).index(name)+1}"
        upsert_asset(project_id, asset_id, "actor", name, prompt="（待生成）")

    # 写入场景
    for sid, desc in parsed["scenes"].items():
        upsert_asset(project_id, sid, "scene", desc, prompt="（待生成）")

    # 写入道具（脚本中有的）
    prop_id = 1
    # 简单处理：从脚本里提取 P开头的道具
    import re
    prop_pattern = re.compile(r"(P\d+)=(.+)")
    for match in prop_pattern.finditer(script):
        pid, pdesc = match.group(1), match.group(2).strip().rstrip(",")
        if pdesc:
            upsert_asset(project_id, pid, "prop", pdesc, prompt="（待生成）")
            prop_id += 1

    # 写入分镜
    for shot in parsed["shots"]:
        upsert_storyboard(
            project_id, shot["id"], shot["id"],
            shot["text"], shot["refs"]
        )

    # ── Phase 4: 生成资产图提示词 + 调用 Seedream ────────────
    print("\n[Phase 4] 生成资产图片 (Seedream 4.5)")
    asset_prompt_tpl = load_prompt("asset_prompt_user")
    asset_sys_prompt  = load_prompt("asset_prompt_system")

    assets = get_assets(project_id)
    asset_map = {}  # asset_id -> local_path

    for asset in assets:
        asset_id = asset["id"]
        asset_type = asset["type"]
        name_or_desc = asset["name"]

        # 生成详细生图提示词
        img_prompt = call_deepseek(
            asset_sys_prompt,
            asset_prompt_tpl.format(
                asset_type=asset_type,
                name_or_desc=name_or_desc,
                theme=theme
            )
        )

        # 调用 Seedream 生成
        output_dir = os.path.join(os.path.dirname(__file__), "..",
                                  "output", project_id, "assets")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, asset_id)

        try:
            result = call_seedream(img_prompt, output_path)
            img_path = result.get("image_path", result.get("data", {}).get("image_path"))
        except Exception as e:
            print(f"  [!] {asset_id} Seedream failed: {e}")
            img_path = None

        upsert_asset(project_id, asset_id, asset_type,
                     name_or_desc, img_prompt,
                     image_local_path=img_path)
        if img_path:
            asset_map[asset_id] = img_path
        print(f"  [OK] {asset_id} ({asset_type}): {img_path or 'FAILED'}")

    # ── Phase 5: 生成视频提示词 ─────────────────────────────
    print("\n[Phase 5] 生成视频提示词 (Seedance 2.0)")
    shots = get_storyboard(project_id)
    updated_assets = get_assets(project_id)

    # 建立 name -> asset_id 映射
    name_to_id = {a["name"]: a["id"] for a in updated_assets if a["name"]}
    id_to_path = {a["id"]: a["image_local_path"] for a in updated_assets}

    n = len(shots)
    duration_per_shot = int(total_duration_s * 1000 / n) if n else 0
    print(f"  分镜数: {n} | 每镜时长: {duration_per_shot}ms")

    # 更新角色映射：角色名 -> R1, R2, R3...
    actor_assets = [a for a in updated_assets if a["type"] == "actor"]
    role_name_to_rid = {}
    for i, a in enumerate(actor_assets, 1):
        role_name_to_rid[a["name"]] = f"R{i}"

    # 更新场景：L1, L2... -> R1, R2... (Seedance 用 R 标签指代角色)
    for shot in shots:
        shot_text = shot["script_text"]
        # 替换 @阿强 -> R1 等
        for name, rid in role_name_to_rid.items():
            if name in shot_text:
                shot_text = shot_text.replace(f"@{name}", f"<role>{rid}</role>")

        # 场景映射
        scene_id = "L1"  # 默认取第一个场景
        video_prompt = build_video_prompt(
            scene_id=scene_id,
            role_map=role_name_to_rid,
            shot_text=shot_text,
            duration_ms=duration_per_shot
        )
        update_storyboard_video(shot["id"], video_prompt, None)
        print(f"  [>] {shot['id']} | {len(video_prompt)} chars prompt | {duration_per_shot}ms")

    # ── Phase 6: 模拟生成视频片段 ────────────────────────────
    print("\n[Phase 6] 生成视频片段 (Seedance 2.0 - Mock)")
    from mock_api import mock_generate_video_shot

    shots = get_storyboard(project_id)
    video_dir = os.path.join(os.path.dirname(__file__), "..",
                             "output", project_id, "videos")
    os.makedirs(video_dir, exist_ok=True)

    # 角色引用图片映射: R1 -> A1 的图片路径
    rid_to_path = {}
    for name, rid in role_name_to_rid.items():
        aid = name_to_id.get(name)
        if aid:
            rid_to_path[rid] = id_to_path.get(aid)

    for shot in shots:
        shot_video_dir = os.path.join(video_dir, shot["id"])
        os.makedirs(shot_video_dir, exist_ok=True)
        output_path = os.path.join(shot_video_dir, shot["id"])
        result = mock_generate_video_shot(
            shot_id=shot["id"],
            prompt=shot["video_prompt"],
            output_path=output_path,
            ref_image_paths=rid_to_path
        )
        update_storyboard_video(shot["id"], shot["video_prompt"], result["video_path"])
        print(f"  [OK] {shot['id']} -> {result['video_path']}")

    # ── Phase 7: FFmpeg 拼合 ─────────────────────────────────
    print("\n[Phase 7] FFmpeg 拼合视频")
    shots = get_storyboard(project_id)
    video_list = [s["video_path"] for s in shots if s["video_path"]]

    if not video_list:
        print("  [!] 无视频路径，跳过拼合")
        return project_id

    concat_list = os.path.join(video_dir, "concat.txt")
    output_mp4 = os.path.join(os.path.dirname(__file__), "..",
                              "output", project_id, f"{project_id}.mp4")

    with open(concat_list, "w") as f:
        for p in video_list:
            f.write(f"file '{p}'\n")

    print(f"  concat list: {concat_list}")
    print(f"  输出 MP4: {output_mp4}")
    print("  (Mock 阶段跳过 ffmpeg，输出为占位文件)")

    # Mock: 创建一个占位最终文件
    os.makedirs(os.path.dirname(output_mp4), exist_ok=True)
    with open(output_mp4, "wb") as f:
        f.write(b"\x00\x00\x00\x1c\x66\x74\x79\x70\x69\x73\x6f\x6d\x00\x00\x02\x00\x69\x73\x6f\x6d\x69\x73\x6f\x32\x6d\x70\x34\x31\x00\x00\x00\x08\x6d\x6f\x6f\x76\x00\x00\x00\x00")

    update_project_final_mp4(project_id, output_mp4)
    print(f"  [OK] Final MP4 (mock): {output_mp4}")

    # ── 汇总报告 ─────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  PIPELINE DEMO COMPLETE | project_id={project_id}")
    print(f"{'='*60}")
    print(f"  主题: {theme}")
    print(f"  总时长: {total_duration_s}s")
    print(f"  演员: {list(parsed['actors'].keys())}")
    print(f"  场景: {list(parsed['scenes'].keys())}")
    print(f"  分镜数: {n}")
    print(f"  图片资产: {len(asset_map)}")
    print(f"  视频片段: {len(video_list)}")
    print(f"  最终文件: {output_mp4}")
    print(f"\n  输出目录: {os.path.join(os.path.dirname(__file__), '..', 'output', project_id)}")

    # 打印 DB 内容
    print(f"\n[DB] 项目记录:")
    proj = get_project(project_id)
    print(f"  {proj}")

    return project_id


if __name__ == "__main__":
    # Demo 参数
    THEME = "失业警报：当AI开始抢工作"
    DURATION = 40  # 秒
    run(THEME, DURATION)
