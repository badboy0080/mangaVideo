"""
数据库模块 - SQLite 图片资产管理
"""
import sqlite3, json, uuid, os
from pathlib import Path
from datetime import datetime

DB_PATH = None  # 运行时动态设置

def init(db_path: str):
    global DB_PATH
    DB_PATH = db_path
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id TEXT PRIMARY KEY,
            tag   TEXT NOT NULL,        -- 标签：character/scene/prop
            name  TEXT NOT NULL,        -- 资产名称：主角/小巷/血族长剑
            prompt TEXT NOT NULL,        -- 原始提示词
            path  TEXT,                  -- 生成后本地路径
            status TEXT DEFAULT 'pending',-- pending/generated/failed
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS video_clips (
            id TEXT PRIMARY KEY,
            shot_id TEXT NOT NULL,      -- 分镜编号：shot_01
            prompt TEXT NOT NULL,       -- 视频生成提示词
            image_refs TEXT,             -- JSON: {"图片1": "img_id", ...}
            path TEXT,                   -- 生成后本地视频路径
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            topic TEXT,
            script TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def insert_image(conn, tag: str, name: str, prompt: str) -> str:
    img_id = f"img_{uuid.uuid4().hex[:8]}"
    conn.execute(
        "INSERT INTO images (id, tag, name, prompt) VALUES (?, ?, ?, ?)",
        (img_id, tag, name, prompt)
    )
    conn.commit()
    return img_id


def ensure_image_row(conn, img_id: str, tag: str, name: str, prompt: str) -> None:
    """固定 id（如 图片1）占位，供 Step 5 生成后 update_image_path。"""
    conn.execute(
        "INSERT OR IGNORE INTO images (id, tag, name, prompt, status) VALUES (?, ?, ?, ?, 'pending')",
        (img_id, tag, name, prompt),
    )
    conn.commit()

def update_image_path(conn, img_id: str, path: str, status: str = "generated"):
    conn.execute(
        "UPDATE images SET path = ?, status = ? WHERE id = ?",
        (path, status, img_id)
    )
    conn.commit()

def get_pending_images(conn, tag: str = None):
    cur = conn.execute(
        "SELECT id, tag, name, prompt FROM images WHERE status = 'pending'"
        + (" AND tag = ?" if tag else ""),
        (tag,) if tag else ()
    )
    return cur.fetchall()

def get_image_by_name(conn, name: str):
    cur = conn.execute(
        "SELECT id, path, tag FROM images WHERE name = ? LIMIT 1",
        (name,)
    )
    return cur.fetchone()

def insert_video_clip(conn, shot_id: str, prompt: str, image_refs: dict) -> str:
    clip_id = f"clip_{uuid.uuid4().hex[:8]}"
    conn.execute(
        "INSERT INTO video_clips (id, shot_id, prompt, image_refs) VALUES (?, ?, ?, ?)",
        (clip_id, shot_id, prompt, json.dumps(image_refs, ensure_ascii=False))
    )
    conn.commit()
    return clip_id

def update_clip_path(conn, shot_id: str, path: str, status: str = "generated"):
    conn.execute(
        "UPDATE video_clips SET path = ?, status = ? WHERE shot_id = ?",
        (path, status, shot_id)
    )
    conn.commit()

def get_all_clip_paths(conn):
    cur = conn.execute(
        "SELECT path FROM video_clips WHERE status = 'generated' AND path IS NOT NULL ORDER BY shot_id"
    )
    return [r[0] for r in cur.fetchall()]

def save_run(conn, run_id: str, topic: str, script: str):
    conn.execute(
        "INSERT OR REPLACE INTO runs (id, topic, script) VALUES (?, ?, ?)",
        (run_id, topic, script)
    )
    conn.commit()
