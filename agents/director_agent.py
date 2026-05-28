"""创意总监 Agent：全局统筹与创意指导。

在流水线开始前先分析用户需求，为下游 Agent 生成创意指导，
确保整个流水线的风格、节奏、视觉方向保持一致。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from agentscope.agent import Agent

from agents.tools import create_deepseek_model


DIRECTOR_SYSTEM_PROMPT = """你是资深创意总监，负责为视频制作流水线提供全局创意指导。

## 你的任务
分析用户输入的主题、风格和时长，输出一份简短的《创意指导纲要》，供下游 Agent（剧本、分镜、美术、视频）参考。

## 输出格式
只输出 JSON，不要 Markdown 代码块。

{
  "tone": "整体基调，例如：温暖治愈、紧张悬疑、热血燃、冷酷科幻",
  "visual_style": "视觉风格方向，例如：赛博朋克霓虹、日系清新、暗黑电影感",
  "color_palette": "主色调建议，例如：冷蓝+橙红对比、暖黄+墨绿、黑白+金色点缀",
  "pacing": "节奏建议，例如：前缓后急、全程紧凑、慢节奏情绪流",
  "key_themes": ["核心主题1", "核心主题2"],
  "character_note": "角色塑造建议，一句话",
  "story_constraints": ["剧本必须遵守的约束1", "约束2"],
  "shot_advice": "分镜建议，例如：多用特写、长镜头为主、快速剪辑",
  "audio_direction": "音频方向建议，例如：氛围电子、交响史诗、极简钢琴"
}

## 注意
- 所有建议必须贴合用户指定的风格类型（电影短片/品牌广告/动画叙事/游戏CG/MV/科幻短片/纪录片风格）
- 建议要具体可执行，不要空洞形容词堆砌
- 时长越短，故事越要精简，不要建议塞入过多元素
"""


class DirectorAgent:
    """创意总监 Agent。

    在流水线启动时最先运行，分析用户需求后输出创意指导，
    传递给下游所有 Agent 确保风格统一。
    """

    def __init__(self) -> None:
        self._model = create_deepseek_model(stream=True)
        self._agent = Agent(
            name="创意总监",
            system_prompt=DIRECTOR_SYSTEM_PROMPT,
            model=self._model,
        )

    @property
    def name(self) -> str:
        return self._agent.name

    def analyze(self, topic: str, style: str, duration: int) -> dict[str, Any]:
        """分析用户需求，输出创意指导纲要。"""
        from steps.deepseek_chat import chat

        user_prompt = (
            f"主题：{topic}\n"
            f"风格类型：{style}\n"
            f"目标时长（秒）：{duration}\n\n"
            f"请为这个项目输出创意指导纲要。"
        )

        print(f"  [创意总监] 分析用户需求（{style} · {duration}s）...")
        raw = chat(DIRECTOR_SYSTEM_PROMPT, user_prompt, temperature=0.5, max_tokens=1500, timeout=60)

        if not raw:
            print("  [创意总监] DeepSeek 未返回结果，使用默认指导")
            return self._default_guidance(style)

        try:
            s = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.S | re.I)
            guidance = json.loads(s)
            if isinstance(guidance, dict) and guidance.get("tone"):
                print(f"  [创意总监] 指导生成完成：基调={guidance.get('tone', '')}")
                return guidance
        except (json.JSONDecodeError, KeyError):
            pass

        print("  [创意总监] 返回格式异常，使用默认指导")
        return self._default_guidance(style)

    @staticmethod
    def _default_guidance(style: str) -> dict[str, Any]:
        """风格默认指导（API 不可用时的兜底）。"""
        defaults: dict[str, dict[str, Any]] = {
            "电影短片": {
                "tone": "情感真挚、有戏剧张力",
                "visual_style": "电影感画面、自然光影",
                "color_palette": "暖色调为主、暗部保留细节",
                "pacing": "前缓后急、情绪逐步推进",
                "key_themes": ["人性抉择", "情感共鸣"],
                "character_note": "主角要有明确的欲望和困境",
                "story_constraints": ["必须有明确冲突和转折"],
                "shot_advice": "多用中近景、关键情绪用特写",
                "audio_direction": "氛围配乐、关键时刻留白",
            },
            "品牌广告": {
                "tone": "精致高级、有记忆点",
                "visual_style": "干净构图、产品突出",
                "color_palette": "品牌色为主、高对比",
                "pacing": "快节奏、信息密度高",
                "key_themes": ["产品价值", "用户痛点"],
                "character_note": "用户画像清晰、代入感强",
                "story_constraints": ["必须聚焦单一核心卖点"],
                "shot_advice": "产品特写、使用场景展示",
                "audio_direction": "轻快节奏、品牌音效",
            },
            "动画叙事": {
                "tone": "生动有趣、想象力丰富",
                "visual_style": "色彩鲜明、造型夸张",
                "color_palette": "高饱和、活泼配色",
                "pacing": "节奏明快、转折干脆",
                "key_themes": ["成长冒险", "友情羁绊"],
                "character_note": "角色动作和表情要夸张可读",
                "story_constraints": ["画面必须有叙事功能"],
                "shot_advice": "动态镜头、夸张透视",
                "audio_direction": "活泼配乐、音效丰富",
            },
            "游戏CG": {
                "tone": "震撼、有史诗感",
                "visual_style": "宏大场景、光影戏剧化",
                "color_palette": "冷暖对比强烈",
                "pacing": "起承转合、高潮集中",
                "key_themes": ["力量展示", "世界构建"],
                "character_note": "角色要有高光时刻和能力展示",
                "story_constraints": ["必须有视觉高潮和悬念"],
                "shot_advice": "大景别建立世界观、动作特写",
                "audio_direction": "交响史诗、打击乐驱动",
            },
            "MV": {
                "tone": "情绪主导、视觉先行",
                "visual_style": "风格化画面、节奏剪辑",
                "color_palette": "根据音乐情绪定调",
                "pacing": "跟随音乐节奏起伏",
                "key_themes": ["情绪母题", "视觉符号"],
                "character_note": "表演者情绪贯穿始终",
                "story_constraints": ["必须有视觉高潮段落"],
                "shot_advice": "节奏剪辑、动态运镜",
                "audio_direction": "以歌曲本身为主",
            },
            "科幻短片": {
                "tone": "冷静、有思想深度",
                "visual_style": "未来感、科技美学",
                "color_palette": "冷色调、霓虹点缀",
                "pacing": "先建立世界观、再展开冲突",
                "key_themes": ["科技与人性的关系", "未来想象"],
                "character_note": "角色要面对科技带来的道德困境",
                "story_constraints": ["科幻设定必须自洽"],
                "shot_advice": "大景别展现未来世界、特写表现人性",
                "audio_direction": "电子氛围、合成器音色",
            },
            "纪录片风格": {
                "tone": "真实、克制、有温度",
                "visual_style": "自然光、手持感",
                "color_palette": "低饱和、自然色",
                "pacing": "事实线+情感线并进",
                "key_themes": ["真实故事", "人性观察"],
                "character_note": "保持客观、让事实说话",
                "story_constraints": ["不可虚构事实"],
                "shot_advice": "观察视角、跟拍感",
                "audio_direction": "简约配乐、环境音为主",
            },
        }
        return defaults.get(style, defaults["电影短片"])
