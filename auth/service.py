from __future__ import annotations
import re
from datetime import datetime, timezone
from typing import Optional, Tuple

import bcrypt
import streamlit as st

from .db import init_db, fetch_one, fetch_all, execute


USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")


def ensure_auth_state() -> None:
    init_db()
    st.session_state.setdefault("auth.logged_in", False)
    st.session_state.setdefault("auth.user_id", None)
    st.session_state.setdefault("auth.username", "")
    st.session_state.setdefault("auth.role", "")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def register_user(username: str, email: str, password: str) -> Tuple[bool, str]:
    username = (username or "").strip()
    email = (email or "").strip().lower()
    password = password or ""

    if not USERNAME_RE.match(username):
        return False, "用户名建议 3-20 位，仅包含字母/数字/下划线"
    if "@" not in email or "." not in email:
        return False, "邮箱格式不正确"
    if len(password) < 6:
        return False, "密码至少 6 位"


    if fetch_one("SELECT id FROM users WHERE username = ?", (username,)):
        return False, "用户名已存在"
    if fetch_one("SELECT id FROM users WHERE email = ?", (email,)):
        return False, "邮箱已被注册"

    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    execute(
        "INSERT INTO users(username, email, password_hash, role, created_at) VALUES(?,?,?,?,?)",
        (username, email, pw_hash, "user", _now_iso()),
    )
    return True, "注册成功，请登录"


def login_user(identifier: str, password: str) -> Tuple[bool, str]:
    identifier = (identifier or "").strip()
    password = password or ""
    if not identifier or not password:
        return False, "请输入账号与密码"


    user = fetch_one(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (identifier, identifier.lower()),
    )
    if not user:
        return False, "账号不存在"

    pw_hash = user["password_hash"]
    if isinstance(pw_hash, str):
        pw_hash = pw_hash.encode("utf-8")

    ok = bcrypt.checkpw(password.encode("utf-8"), pw_hash)
    if not ok:
        return False, "密码错误"

    st.session_state["auth.logged_in"] = True
    st.session_state["auth.user_id"] = user["id"]
    st.session_state["auth.username"] = user["username"]
    st.session_state["auth.role"] = user["role"]
    return True, "登录成功"


def logout_user() -> None:
    st.session_state["auth.logged_in"] = False
    st.session_state["auth.user_id"] = None
    st.session_state["auth.username"] = ""
    st.session_state["auth.role"] = ""


def current_user() -> Optional[dict]:
    uid = st.session_state.get("auth.user_id")
    if not uid:
        return None
    return fetch_one("SELECT id, username, email, role, created_at FROM users WHERE id = ?", (uid,))


def list_users() -> list[dict]:
    return fetch_all("SELECT id, username, email, role, created_at FROM users ORDER BY id DESC")


def update_user_role(user_id: int, role: str) -> None:
    role = role if role in ("user", "admin") else "user"
    execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))


def update_user_email(user_id: int, email: str) -> Tuple[bool, str]:
    email = (email or "").strip().lower()
    if "@" not in email or "." not in email:
        return False, "邮箱格式不正确"

    exists = fetch_one("SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id))
    if exists:
        return False, "该邮箱已被占用"

    execute("UPDATE users SET email = ? WHERE id = ?", (email, user_id))
    return True, "邮箱已更新"


def reset_user_password(user_id: int, new_password: str) -> Tuple[bool, str]:
    new_password = new_password or ""
    if len(new_password) < 6:
        return False, "新密码至少 6 位"
    pw_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
    execute("UPDATE users SET password_hash = ? WHERE id = ?", (pw_hash, user_id))
    return True, "密码已重置"
