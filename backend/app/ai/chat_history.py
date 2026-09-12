"""Filesystem chat history for AI Support.

Layout: ``chat_history/{user_id}/{date_time}.json``

Full conversation JSON may grow; only the latest ``CONTEXT_SIZE`` messages
are returned for model context.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import BACKEND_DIR

logger = logging.getLogger("harbordock.ai")

CONTEXT_SIZE = 10
CHAT_HISTORY_ROOT = BACKEND_DIR / "chat_history"

# Session folder/file names: 20260912_130945
_SESSION_ID_RE = re.compile(r"^\d{8}_\d{6}$")


def new_session_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _validate_session_id(session_id: str) -> str:
    sid = (session_id or "").strip()
    if not _SESSION_ID_RE.match(sid):
        raise ValueError("Invalid session_id; expected YYYYMMDD_HHMMSS")
    return sid


def session_path(user_id: int, session_id: str) -> Path:
    sid = _validate_session_id(session_id)
    return CHAT_HISTORY_ROOT / str(int(user_id)) / f"{sid}.json"


def _empty_session(user_id: int, session_id: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "user_id": int(user_id),
        "session_id": session_id,
        "created_at": now,
        "updated_at": now,
        "messages": [],
    }


def load_session(user_id: int, session_id: str) -> dict[str, Any] | None:
    path = session_path(user_id, session_id)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to load chat history %s: %s", path, exc)
        return None
    if not isinstance(data, dict):
        return None
    messages = data.get("messages")
    if not isinstance(messages, list):
        data["messages"] = []
    return data


def ensure_session(user_id: int, session_id: str | None = None) -> dict[str, Any]:
    """Load an existing session or create a new one under user_id/date_time."""
    if session_id:
        existing = load_session(user_id, session_id)
        if existing is not None:
            return existing
        # Client sent an unknown id — still bind to that path so the thread continues.
        sid = _validate_session_id(session_id)
    else:
        sid = new_session_id()

    data = _empty_session(user_id, sid)
    save_session(data)
    return data


def save_session(data: dict[str, Any]) -> Path:
    user_id = int(data["user_id"])
    session_id = _validate_session_id(str(data["session_id"]))
    path = session_path(user_id, session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return path


def append_turn(
    data: dict[str, Any],
    *,
    role: str,
    content: str,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    messages = list(data.get("messages") or [])
    entry: dict[str, Any] = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if meta:
        entry["meta"] = meta
    messages.append(entry)
    data["messages"] = messages
    save_session(data)
    return data


def get_context_messages(
    data: dict[str, Any],
    *,
    limit: int = CONTEXT_SIZE,
) -> list[dict[str, Any]]:
    """Return the latest ``limit`` messages for model context (chronological)."""
    messages = list(data.get("messages") or [])
    if limit <= 0:
        return []
    return messages[-limit:]


def format_context_for_prompt(messages: list[dict[str, Any]]) -> str:
    if not messages:
        return "(no prior messages)"
    lines: list[str] = []
    for msg in messages:
        role = str(msg.get("role") or "unknown")
        label = "Customer" if role == "user" else "Assistant" if role == "assistant" else role
        content = str(msg.get("content") or "").strip()
        if content:
            lines.append(f"{label}: {content}")
    return "\n".join(lines) if lines else "(no prior messages)"


def last_order_id_from_history(messages: list[dict[str, Any]]) -> int | None:
    for msg in reversed(messages):
        if msg.get("role") != "assistant":
            continue
        meta = msg.get("meta") or {}
        oid = meta.get("order_id")
        if isinstance(oid, int) and oid > 0:
            return oid
    return None
