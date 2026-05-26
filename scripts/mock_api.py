#!/usr/bin/env python3
"""
Mock API Layer - 拦截真实 API 调用，返回模拟数据
用法: from mock_api import apply_mocks; apply_mocks()
"""
import os, sys, json, time, urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MOCK_SCRIPT_PATH = os.path.join(SCRIPT_DIR, "mock_script.txt")

with open(MOCK_SCRIPT_PATH, encoding="utf-8") as f:
    MOCK_SCRIPT = f.read()

MOCK_ASSET_PROMPTS = {
    "A1": "阿强，男性，28岁，中国程序员，面容疲惫但眼神坚定，穿着程序员标配的深色卫衣，办公室昏暗灯光下侧脸特写，失业危机感，写实摄影风格，高清细腻",
    "A2": "主管，男性，40岁，科技公司管理层，深色西装，手持平板，俯身姿态，办公室冷光，写实摄影风格，电影感",
    "A3": "吸血鬼猎手，男性，30岁，动作英雄气质，手持发光剑刃，剑身冷蓝光芒，废弃工厂，月光从破洞屋顶倾泻，电影风格，写实摄影",
    "L1": "深夜科技公司开放式办公区，大面积黑暗，只剩零星台灯与显示器冷光，电脑终端蓝光缓慢脉冲，纪实风格，压抑氛围，高清细腻",
    "L2": "废弃工厂大厅，铁架与生锈机械散落，午夜月光从破洞屋顶倾泻，冷色调，电影感，氛围紧张，写实摄影",
    "L3": "霓虹灯照亮的小巷，潮湿的地面反射霓虹灯光，多个身影分布在屋顶和街道上，电影风格，紧张氛围，写实摄影",
    "P1": "笔记本电脑，商用办公配置，屏幕显示代码界面，办公室场景道具，写实摄影",
    "P2": "剑，发光剑刃，冷蓝色光晕，废弃工厂场景，电影风格道具",
    "P3": "咖啡杯，办公室场景道具，程序员文化符号，写实摄影",
}

MOCK_VIDEO_PROMPTS = [
    {
        "shot_id": "S01",
        "prompt": "画面风格和类型: 真人写实, 电影风格, 冷色调, 男频科幻/游戏\n生成一个由以下1个分镜组成的视频。\n本片段场景设定在: <location>L1</location>\n\n分镜1<duration-ms>8000</duration-ms>:\n焦虑压抑的氛围，冰冷的顶光和显示器反光交织。中景镜头，在22世纪科技公司的开放式工位上，<role>R1</role>坐在屏幕前，面部朝向显示器，眉头紧锁，眼神涣散，额头渗出细汗，显得疲惫不堪但不敢停下。他的双手在键盘上快速敲击，偶尔用单手揉捏酸痛的肩膀。镜头以15度的微小弧度进行弧形环绕，带有轻微的手持呼吸感。背景里的同事们如同僵硬的机器般高速打字，强化了内卷的压迫感。纪实颗粒，轻微孤寂压抑感，禁止跳吓，禁止真实品牌，禁止手机出现可读聊天内容。",
    },
    {
        "shot_id": "S02",
        "prompt": "画面风格和类型: 真人写实, 电影风格, 冷色调, 男频科幻/游戏\n生成一个由以下1个分镜组成的视频。\n本片段场景设定在: <location>L1</location>\n\n分镜2<duration-ms>8000</duration-ms>:\n同一办公区，时间稍后。<role>R2</role>手持平板走来，屏幕上显示AI自动生成率94%。<role>R2</role>俯身看向<role>R1</role>屏幕，表情复杂。<role>R1</role>猛然抬头，眼神从空洞转为警觉。冷光打亮两人侧脸，明暗对比强烈。中景固定镜头加轻微推拉，强化压迫感。纪实风格，压抑克制的情绪张力，禁止品牌标志。",
    },
    {
        "shot_id": "S03",
        "prompt": "画面风格和类型: 真人写实, 电影风格, 冷色调, 男频科幻/游戏\n生成一个由以下1个分镜组成的视频。\n本片段场景设定在: <location>L1</location>\n\n分镜3<duration-ms>8000</duration-ms>:\n<role>R1</role>独自收拾桌面，把个人物品逐一放进纸箱。台灯关闭，只剩走廊应急灯微光。镜头从<role>R1</role>背影缓慢拉远，办公室大面积黑暗。<role>R1</role>抱纸箱走向电梯口，步伐沉重。纪实颗粒，轻微手持呼吸感，压抑孤独，禁止品牌标志，禁止可读文字。",
    },
    {
        "shot_id": "S04",
        "prompt": "画面风格和类型: 真人写实, 电影风格, 冷色调, 男频科幻/游戏\n生成一个由以下1个分镜组成的视频。\n本片段场景设定在: <location>L2</location>\n\n分镜4<duration-ms>8000</duration-ms>:\n废弃工厂大厅，铁架与生锈机械散落，午夜月光从破洞屋顶倾泻。<role>R3</role>站在中央，手持发光剑刃，剑身散发冷蓝色光晕。<role>R3</role>环顾四周，警戒姿态。镜头绕猎手旋转360度，展示环境全貌。冷色调，强调光影对比，电影感，氛围紧张，禁止出现可读文字。",
    },
    {
        "shot_id": "S05",
        "prompt": "画面风格和类型: 真人写实, 电影风格, 冷色调, 男频科幻/游戏\n生成一个由以下1个分镜组成的视频。\n本片段场景设定在: <location>L2</location>\n\n分镜5<duration-ms>8000</duration-ms>:\n同一废弃工厂，<role>R1</role>出现在门口，抱着纸箱，环境与猎手形成对峙。<role>R1</role>放下纸箱，双手颤抖但眼神坚定。猎手收起剑，两人对视。镜头在两人之间缓慢正反打。冷光月光加剑刃蓝光交织。纪实风格，压抑但带有微光希望，禁止跳吓。",
    },
]


def mock_call_deepseek(system_prompt: str, user_prompt: str,
                       temperature: float = 0.7, max_tokens: int = 4096) -> str:
    print("  [MOCK DeepSeek] 返回分镜脚本 ...")
    time.sleep(0.5)
    return MOCK_SCRIPT


def mock_call_seedream(prompt: str, output_path: str,
                      aspect_ratio: str = "16:9",
                      resolution: str = "1280x720") -> dict:
    print(f"  [MOCK Seedream] 生成图片: {output_path}.png ...")
    time.sleep(0.8)
    img_path = output_path + ".png"
    os.makedirs(os.path.dirname(img_path), exist_ok=True)
    try:
        basename = os.path.basename(output_path)
        url = f"https://via.placeholder.com/1280x720/1a1a2e/FFFFFF?text={basename}"
        urllib.request.urlretrieve(url, img_path)
        print(f"  [MOCK Seedream] 已存: {img_path}")
        return {"status": "ok", "image_path": img_path}
    except Exception as e:
        print(f"  [MOCK Seedream] WARN: {e}")
        with open(img_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\nMOCK_IMAGE_PLACEHOLDER")
        return {"status": "ok", "image_path": img_path}


def mock_generate_video_shot(shot_id: str, prompt: str, output_path: str,
                             ref_image_paths: dict = None) -> dict:
    print(f"  [MOCK Seedance] 生成视频片段: {shot_id} ...")
    print(f"    prompt长度: {len(prompt)} chars")
    time.sleep(1.5)
    video_path = output_path + ".mp4"
    os.makedirs(os.path.dirname(video_path), exist_ok=True)
    with open(video_path, "wb") as f:
        f.write(bytes([
            0x00, 0x00, 0x00, 0x20, 0x66, 0x74, 0x79, 0x70,
            0x69, 0x73, 0x6f, 0x6d, 0x00, 0x00, 0x02, 0x00,
            0x69, 0x73, 0x6f, 0x6d, 0x69, 0x73, 0x6f, 0x32,
            0x6d, 0x70, 0x34, 0x31, 0x00, 0x00, 0x00, 0x08,
            0x6d, 0x6f, 0x6f, 0x76, 0x00, 0x00, 0x00, 0x00,
        ]))
    print(f"  [MOCK Seedance] 已存: {video_path}")
    return {"status": "ok", "video_path": video_path, "shot_id": shot_id}


def apply_mocks():
    """将所有真实 API 替换为 Mock 实现"""
    import deepseek_caller
    import seedream_caller
    deepseek_caller.call_deepseek = mock_call_deepseek
    seedream_caller.call_seedream = mock_call_seedream
    print("[Mock API] 所有真实 API 已替换为 Mock 实现")


if __name__ == "__main__":
    apply_mocks()
    print(f"[Mock API] loaded - script {len(MOCK_SCRIPT)} chars")
    print(f"  Assets: {list(MOCK_ASSET_PROMPTS.keys())}")
    print(f"  Shots: {len(MOCK_VIDEO_PROMPTS)}")
