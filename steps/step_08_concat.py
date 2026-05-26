"""
Step 8: 视频拼接
使用 ffmpeg concat demuxer 将所有视频片段合并为最终 MP4
"""
import subprocess, os

def run(conn, out_dir: str) -> str:
    """
    从数据库读取所有生成的视频片段，按 shot_id 顺序拼接
    返回最终 MP4 路径
    """
    from db import get_all_clip_paths
    clip_paths = get_all_clip_paths(conn)

    if not clip_paths:
        note = f"{out_dir}/NO_VIDEO_TO_CONCAT.txt"
        with open(note, "w", encoding="utf-8") as f:
            f.write(
                "没有可用的视频片段，已跳过 ffmpeg 拼接。\n"
                "常见原因：未安装或未配置 mmx（MiniMax CLI）、Step7 全部失败、或首帧图片路径无效。\n"
            )
        print(f"  [跳过拼接] 说明已写入: {note}")
        return note

    # 检查文件（统一转绝对路径，避免 ffmpeg concat 把相对路径相对到 concat.txt 目录导致路径重复）
    valid_paths = []
    for p in clip_paths:
        ap = os.path.abspath(os.path.normpath(p))
        if os.path.isfile(ap) and os.path.getsize(ap) > 1000:
            valid_paths.append(ap)
        else:
            print(f"  [跳过] 无效文件: {p}")

    if not valid_paths:
        note = f"{out_dir}/NO_VIDEO_TO_CONCAT.txt"
        with open(note, "w", encoding="utf-8") as f:
            f.write(
                "数据库中有视频记录但本地文件无效或已丢失，已跳过拼接。\n"
            )
        print(f"  [跳过拼接] 说明已写入: {note}")
        return note

    print(f"  拼接 {len(valid_paths)} 个视频片段...")

    concat_file = os.path.abspath(os.path.normpath(f"{out_dir}/concat.txt"))
    with open(concat_file, "w", encoding="utf-8") as f:
        for p in valid_paths:
            # 使用绝对路径 + 正斜杠，避免 Windows 下相对路径/盘符被 concat 误解析
            safe = p.replace("\\", "/")
            f.write(f"file '{safe}'\n")

    output_mp4 = os.path.abspath(os.path.normpath(f"{out_dir}/final.mp4"))

    # 执行拼接
    result = subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_mp4,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 拼接失败: {result.stderr}")

    # 清理临时文件
    try:
        os.remove(concat_file)
    except:
        pass

    size_mb = os.path.getsize(output_mp4) / 1024 / 1024
    print(f"  最终视频: {output_mp4} ({size_mb:.1f} MB)")
    return output_mp4
