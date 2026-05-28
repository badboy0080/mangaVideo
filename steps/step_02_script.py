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

    # 仅作为上下文提示，具体输出格式交给 SYSTEM_PROMPT 控制。
    min_shots_for_seedance = max(4, (target_duration + 14) // 15)
    est_shots = min(24, max(min_shots_for_seedance, target_duration // 10))
    acts = 2 if target_duration >= 60 else 1  # 60s以上分两幕

    user_prompt = f"""主题：{topic}

风格类型：{style_label}

目标总时长：{target_duration} 秒
建议镜头数：约 {est_shots} 个
建议段落数：{acts} 段

{reference_block}

请根据 SYSTEM_PROMPT 生成故事板正文。保留自动化最低约束：
- 分镜标题使用「分镜 N｜X 秒｜标题」。
- 角色、场景、道具使用稳定的 `@名称`。
- 每镜保留可读取的「图生视频（I2V）— 整段复制」正文。
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
