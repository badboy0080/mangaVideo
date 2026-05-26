"""
SQLite 数据库初始化 + 工具函数
"""
import sqlite3, json, os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "manga.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # 项目表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS project (
            id TEXT PRIMARY KEY,
            theme TEXT NOT NULL,
            total_duration_s INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            final_mp4 TEXT
        )
    """)

    # 资产表：演员/场景/道具
    cur.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('actor','scene','prop')),
            name TEXT NOT NULL,
            prompt TEXT NOT NULL,
            image_url TEXT,
            image_local_path TEXT,
            metadata TEXT,
            FOREIGN KEY (project_id) REFERENCES project(id)
        )
    """)

    # 分镜脚本表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS storyboard (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            shot_num TEXT NOT NULL,
            script_text TEXT NOT NULL,
            asset_refs TEXT,
            video_prompt TEXT,
            video_path TEXT,
            duration_ms INTEGER,
            FOREIGN KEY (project_id) REFERENCES project(id)
        )
    """)

    conn.commit()
    conn.close()
    print(f"[DB] Initialized at {DB_PATH}")

# ── CRUD helpers ──────────────────────────────────────────

def create_project(project_id: str, theme: str, total_duration_s: int):
    conn = get_conn()
    conn.execute(
        "INSERT INTO project (id, theme, total_duration_s) VALUES (?,?,?)",
        (project_id, theme, total_duration_s)
    )
    conn.commit()
    conn.close()

def upsert_asset(project_id: str, asset_id: str, asset_type: str,
                 name: str, prompt: str,
                 image_local_path: str = None, metadata: dict = None):
    conn = get_conn()
    conn.execute("""
        INSERT INTO assets (project_id,id,type,name,prompt,image_local_path,metadata)
        VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            prompt=excluded.prompt,
            image_local_path=excluded.image_local_path,
            metadata=excluded.metadata
    """, (project_id, asset_id, asset_type, name, prompt,
          image_local_path, json.dumps(metadata) if metadata else None))
    conn.commit()
    conn.close()

def upsert_storyboard(project_id: str, shot_id: str, shot_num: str,
                      script_text: str, asset_refs: list,
                      duration_ms: int = None):
    conn = get_conn()
    conn.execute("""
        INSERT INTO storyboard (project_id,id,shot_num,script_text,asset_refs,duration_ms)
        VALUES (?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            script_text=excluded.script_text,
            asset_refs=excluded.asset_refs,
            duration_ms=excluded.duration_ms
    """, (project_id, shot_id, shot_num, script_text,
          json.dumps(asset_refs), duration_ms))
    conn.commit()
    conn.close()

def update_storyboard_video(shot_id: str, video_prompt: str, video_path: str):
    conn = get_conn()
    conn.execute("""
        UPDATE storyboard SET video_prompt=?, video_path=? WHERE id=?
    """, (video_prompt, video_path, shot_id))
    conn.commit()
    conn.close()

def update_project_final_mp4(project_id: str, mp4_path: str):
    conn = get_conn()
    conn.execute("UPDATE project SET final_mp4=? WHERE id=?", (mp4_path, project_id))
    conn.commit()
    conn.close()

def get_project(project_id: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM project WHERE id=?", (project_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_assets(project_id: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM assets WHERE project_id=?", (project_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_storyboard(project_id: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM storyboard WHERE project_id=? ORDER BY shot_num",
        (project_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

if __name__ == "__main__":
    init_db()
