from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.ai.chat_history import (
    append_turn,
    ensure_session,
    get_context_messages,
    last_order_id_from_history,
)
from app.ai.graph import build_support_graph
from app.ai.llm import empty_turn_usage
from app.models.role import User
from app.utils.exceptions import AppError

logger = logging.getLogger("harbordock.ai")


def run_support_turn(
    db: Session,
    customer: User,
    message: str,
    *,
    session_id: str | None = None,
    confirm_cancel: bool = False,
    order_id_hint: int | None = None,
) -> dict[str, Any]:
    text = (message or "").strip()
    if len(text) < 2:
        raise AppError("INVALID_MESSAGE", "Message is too short.", 400)

    try:
        session = ensure_session(customer.id, session_id)
    except ValueError as exc:
        raise AppError("INVALID_SESSION", str(exc), 400) from exc

    sid = str(session["session_id"])
    # Persist the user turn first so the JSON on disk always includes it.
    append_turn(session, role="user", content=text)
    # Full JSON may be long; only the latest CONTEXT_SIZE messages feed the model.
    context_messages = get_context_messages(session)
    prior_messages = context_messages[:-1] if context_messages else []
    hint = order_id_hint or last_order_id_from_history(prior_messages)

    trace_id = str(uuid.uuid4())
    started = time.perf_counter()

    try:
        app = build_support_graph(db, customer)
        initial: dict[str, Any] = {
            "user_message": text,
            "confirm_cancel": confirm_cancel,
            "chat_history": context_messages,
            "order_id": hint,
            "tool_results": [],
            "tools_called": [],
            "citations": [],
            "action_taken": "none",
            "retrieved_information": "",
            "error": "",
            "llm_usage": empty_turn_usage(),
        }
        result = app.invoke(initial)
    except RuntimeError as exc:
        # Missing API key, etc.
        raise AppError("AI_NOT_CONFIGURED", str(exc), 503) from exc
    except Exception as exc:
        logger.exception("AI support turn failed trace_id=%s session=%s", trace_id, sid)
        raise AppError(
            "AI_TURN_FAILED",
            "The AI support workflow failed. Please try again or open a normal support ticket.",
            500,
            details={"trace_id": trace_id, "session_id": sid, "reason": str(exc)[:300]},
        ) from exc

    latency_ms = int((time.perf_counter() - started) * 1000)
    reply = result.get("generated_answer") or "I could not generate a reply."
    usage = result.get("llm_usage") or empty_turn_usage()
    meta = {
        "intent": result.get("intent"),
        "tools_called": result.get("tools_called") or [],
        "citations": result.get("citations") or [],
        "requires_approval": bool(result.get("requires_approval")),
        "needs_escalation": bool(result.get("needs_escalation")),
        "action_taken": result.get("action_taken") or "none",
        "order_id": result.get("order_id"),
        "latency_ms": latency_ms,
        "trace_id": trace_id,
        "usage": usage,
    }
    append_turn(session, role="assistant", content=reply, meta=meta)

    logger.info(
        "AI turn trace_id=%s session=%s intent=%s tools=%s latency_ms=%s "
        "prompt_tokens=%s completion_tokens=%s total_tokens=%s llm_calls=%s customer_id=%s",
        trace_id,
        sid,
        result.get("intent"),
        result.get("tools_called"),
        latency_ms,
        usage.get("prompt_tokens"),
        usage.get("completion_tokens"),
        usage.get("total_tokens"),
        usage.get("llm_calls"),
        customer.id,
    )

    return {
        "reply": reply,
        "session_id": sid,
        "intent": result.get("intent"),
        "risk_level": result.get("risk_level"),
        "summary": result.get("summary"),
        "order_id": result.get("order_id"),
        "tools_called": result.get("tools_called") or [],
        "citations": result.get("citations") or [],
        "requires_approval": bool(result.get("requires_approval")),
        "needs_escalation": bool(result.get("needs_escalation")),
        "action_taken": result.get("action_taken") or "none",
        "ticket_information": result.get("ticket_information") or "",
        "trace_id": trace_id,
        "latency_ms": latency_ms,
        "usage": usage,
    }
