from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.ai.graph import build_support_graph
from app.models.role import User
from app.utils.exceptions import AppError

logger = logging.getLogger("harbordock.ai")


def run_support_turn(
    db: Session,
    customer: User,
    message: str,
    *,
    confirm_cancel: bool = False,
    order_id_hint: int | None = None,
) -> dict[str, Any]:
    text = (message or "").strip()
    if len(text) < 2:
        raise AppError("INVALID_MESSAGE", "Message is too short.", 400)

    trace_id = str(uuid.uuid4())
    started = time.perf_counter()

    try:
        app = build_support_graph(db, customer)
        initial: dict[str, Any] = {
            "user_message": text,
            "confirm_cancel": confirm_cancel,
            "order_id": order_id_hint,
            "tool_results": [],
            "tools_called": [],
            "citations": [],
            "action_taken": "none",
            "retrieved_information": "",
            "error": "",
        }
        result = app.invoke(initial)
    except RuntimeError as exc:
        # Missing API key, etc.
        raise AppError("AI_NOT_CONFIGURED", str(exc), 503) from exc
    except Exception as exc:
        logger.exception("AI support turn failed trace_id=%s", trace_id)
        raise AppError(
            "AI_TURN_FAILED",
            "The AI support workflow failed. Please try again or open a normal support ticket.",
            500,
            details={"trace_id": trace_id, "reason": str(exc)[:300]},
        ) from exc

    latency_ms = int((time.perf_counter() - started) * 1000)
    logger.info(
        "AI turn trace_id=%s intent=%s tools=%s latency_ms=%s customer_id=%s",
        trace_id,
        result.get("intent"),
        result.get("tools_called"),
        latency_ms,
        customer.id,
    )

    return {
        "reply": result.get("generated_answer") or "I could not generate a reply.",
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
    }
