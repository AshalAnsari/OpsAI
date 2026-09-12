"""Unit tests for AI Support filesystem chat history."""

from pathlib import Path

import pytest

from app.ai import chat_history as ch


@pytest.fixture(autouse=True)
def _tmp_history_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(ch, "CHAT_HISTORY_ROOT", tmp_path / "chat_history")
    yield


def test_session_path_layout():
    path = ch.session_path(42, "20260912_130945")
    assert path == ch.CHAT_HISTORY_ROOT / "42" / "20260912_130945.json"


def test_invalid_session_id():
    with pytest.raises(ValueError):
        ch.session_path(1, "../evil")
    with pytest.raises(ValueError):
        ch.ensure_session(1, "not-a-session")


def test_append_and_context_window():
    session = ch.ensure_session(7)
    sid = session["session_id"]
    assert ch._SESSION_ID_RE.match(sid)

    for i in range(15):
        ch.append_turn(session, role="user", content=f"u{i}")
        ch.append_turn(session, role="assistant", content=f"a{i}", meta={"order_id": i if i == 14 else None})

    loaded = ch.load_session(7, sid)
    assert loaded is not None
    assert len(loaded["messages"]) == 30

    ctx = ch.get_context_messages(loaded, limit=10)
    assert len(ctx) == 10
    assert ctx[0]["content"] == "u10"
    assert ctx[-1]["content"] == "a14"
    assert ch.last_order_id_from_history(ctx) == 14


def test_format_context():
    text = ch.format_context_for_prompt(
        [
            {"role": "user", "content": "Cancel OP-10015"},
            {"role": "assistant", "content": "Please confirm cancel"},
        ]
    )
    assert "Customer: Cancel OP-10015" in text
    assert "Assistant: Please confirm cancel" in text


def test_usage_totals_on_assistant_meta():
    session = ch.ensure_session(3)
    assert session["usage_totals"]["total_tokens"] == 0

    ch.append_turn(session, role="user", content="Where is my order?")
    ch.append_turn(
        session,
        role="assistant",
        content="Pending",
        meta={
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "total_tokens": 120,
                "llm_calls": 2,
            }
        },
    )
    ch.append_turn(
        session,
        role="assistant",
        content="Still pending",
        meta={
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 10,
                "total_tokens": 60,
                "llm_calls": 1,
            }
        },
    )

    loaded = ch.load_session(3, session["session_id"])
    assert loaded is not None
    assert loaded["usage_totals"] == {
        "prompt_tokens": 150,
        "completion_tokens": 30,
        "total_tokens": 180,
        "llm_calls": 3,
    }
    assert loaded["messages"][-1]["meta"]["usage"]["total_tokens"] == 60
