"""
Step 2: 生成分镜脚本（DeepSeek）

产出约定：返回的 `script` 与写入 `script.md` 的内容 **仅**为模型正文，不拼接本地标题、不用占位分镜兜底。
见 `steps.step_output_policy`。
"""

from pathlib import Path

from steps.deepseek_chat import chat as deepseek_chat
from steps.prompt_config import load_registered_system_prompt

SYSTEM_PROMPT = load_registered_system_prompt("step_02_storyboard.system")

def run(topic: str, research: dict, out_dir: str, target_duration: int = 90) -> dict:
    """
    target_duration: 目标总时长（秒）
    """
    style_label = (research.get("style") or "电影").strip() or "电影"
    brief = (research.get("creative_brief") or "").strip()

    if brief:
        reference_block = f"【Step 1 剧本纲要】（必须以此为剧情与节奏依据）\n{brief}\n"
    else:
        findings_text = ""
        for i, f in enumerate(research.get("findings", [])[:5], 1):
            findings_text += f"[{i}] {f['title']}\n{f['content']}\n\n"
        reference_block = (
            "（未找到 structured 纲要，仅用下列摘录）\n【参考摘录】\n"
            f"{findings_text if findings_text else '（无）'}\n"
        )

    # Seedance 单段 4～15s：总时长需要足够条数才能覆盖，至少 ceil(总秒/15)
    min_shots_for_seedance = max(4, (target_duration + 14) // 15)
    est_shots = min(24, max(min_shots_for_seedance, target_duration // 10))
    acts = 2 if target_duration >= 60 else 1  # 60s以上分两幕

    user_prompt = f"""主题：{topic}

风格类型：{style_label}

目标总时长：{target_duration} 秒
估算分镜数：约 {est_shots} 个
分幕数：{acts} 幕

{reference_block}

请生成一份专业级分镜脚本，严格按照上面的格式要求：
1. 标题醒目
2. 分{acts}幕，每幕有幕名
3. 每个分镜包含：分镜编号、时长、场景简述、表格元数据（推荐模态/首帧建议/参考绑定/台词/音效建议）、T2V中文提示词、I2V中文提示词
4. 角色名用 @角色名 格式（如@阿强、@张主管、@同事A）
5. 场景名用 @场景名 格式（如@办公区全景、@阿强工位）
6. 推荐模态优先 I2V（有利于角色一致性；单段成片由 Seedance 生成）
7. 【重要】每一条分镜标题必须是「分镜 N｜X 秒｜…」，其中 X 为满足 **4≤X≤15 的整数**，且与该镜信息量匹配；高潮、长对白镜倾向 10～15 秒；过场、快闪倾向 4～8 秒。总时长由各镜 X **相加**逼近 {target_duration} 秒，镜数不够就**加镜**，禁止单镜超过 15 秒。
8. 各镜 I2V 段落只描写**该 X 秒内**可完成的运动与镜头，不要写超长一镜到低。
"""

    print(f"  [DeepSeek] 生成分镜脚本（{style_label} · 目标 {target_duration}s，{est_shots}镜，{acts}幕）...")
    script = (deepseek_chat(SYSTEM_PROMPT, user_prompt, temperature=0.8, max_tokens=8000, timeout=180) or "").strip()
    if not script:
        print(
            "  [警告] DeepSeek 未返回分镜正文（检查 DEEPSEEK_API_KEY / 网络）；"
            "script 保持为空，不写本地占位分镜。"
        )

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    script_path = str((out_path / "script.md").resolve())
    (out_path / "script.md").write_text(script, encoding="utf-8")

    # 用已有解析器笮确统计（P2 修复：不再用 script.count("分镜 ") 匹配字符串）
    from steps.script_split import split_shots_standard
    shot_count = len(split_shots_standard(script))
    print(f"  解析出 {shot_count} 个有效分镜块，{acts} 幕")

    return {"script": script, "script_path": script_path, "shots": shot_count}
