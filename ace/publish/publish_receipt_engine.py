import sqlite3
import uuid
import datetime
import os

DB_PATH = os.getenv("ACE_DB_PATH", "ace.db")


def _get_conn():
    return sqlite3.connect(DB_PATH)


def init_publish_receipt_table():
    conn = _get_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS publish_receipts (
        id TEXT PRIMARY KEY,
        episode_id TEXT,
        trend TEXT,
        format TEXT,
        media_path TEXT,
        media_url TEXT,
        container_id TEXT,
        publish_id TEXT,
        status TEXT,
        error_raw TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()


def create_attempt_receipt(episode_id, trend, format_, media_path):
    attempt_id = str(uuid.uuid4())
    conn = _get_conn()
    c = conn.cursor()
    c.execute("""
    INSERT INTO publish_receipts (
        id, episode_id, trend, format,
        media_path, status, created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        attempt_id,
        episode_id,
        trend,
        format_,
        media_path,
        "STARTED",
        datetime.datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()
    return attempt_id


def finalize_attempt_receipt(attempt_id, status,
                             publish_id=None,
                             container_id=None,
                             media_url=None,
                             error_raw=None):
    conn = _get_conn()
    c = conn.cursor()
    c.execute("""
    UPDATE publish_receipts
    SET status = ?,
        publish_id = ?,
        container_id = ?,
        media_url = ?,
        error_raw = ?
    WHERE id = ?
    """, (
        status,
        publish_id,
        container_id,
        media_url,
        error_raw,
        attempt_id
    ))
    conn.commit()
    conn.close()
