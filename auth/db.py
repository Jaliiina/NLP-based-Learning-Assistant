from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional, List

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"


def _ensure_db_dir() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    _ensure_db_dir()
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE NOT NULL,
              email TEXT UNIQUE NOT NULL,
              password_hash BLOB NOT NULL,
              role TEXT NOT NULL DEFAULT 'user',
              created_at TEXT NOT NULL
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    try:
        cur = conn.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        cur = conn.execute(query, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def execute(query: str, params: tuple[Any, ...] = ()) -> None:
    conn = get_conn()
    try:
        conn.execute(query, params)
        conn.commit()
    finally:
        conn.close()
