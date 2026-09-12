from typing import Any

from pydantic import BaseModel, Field


class AISupportChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=4000)
    session_id: str | None = Field(
        default=None,
        description="Existing chat session (YYYYMMDD_HHMMSS). Omit to start a new session.",
        max_length=32,
    )
    confirm_cancel: bool = False
    order_id_hint: int | None = Field(default=None, gt=0)


class AISupportChatResponse(BaseModel):
    reply: str
    session_id: str
    intent: str | None = None
    risk_level: str | None = None
    summary: str | None = None
    order_id: int | None = None
    tools_called: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    needs_escalation: bool = False
    action_taken: str = "none"
    ticket_information: str = ""
    trace_id: str
    latency_ms: int
    usage: dict[str, Any] | None = None
