from typing import Any, Literal

from typing_extensions import TypedDict


Intent = Literal[
    "ORDER_STATUS",
    "ORDER_CANCELLATION",
    "PAYMENT_STATUS",
    "REFUND_REQUEST",
    "POLICY_QUESTION",
    "DELIVERY_ISSUE",
    "ORDER_CHANGE",
    "GENERAL_SUPPORT",
    "UNAUTHORIZED_ACCESS",
]

RiskLevel = Literal["READ", "LOW_RISK_WRITE", "HIGH_RISK"]


class SupportState(TypedDict, total=False):
    """LangGraph state — Harbor Dock Station AI Support."""

    user_message: str
    confirm_cancel: bool
    intent: str
    risk_level: str
    summary: str
    order_id: int | None
    retrieved_information: str
    tool_results: list[dict[str, Any]]
    tools_called: list[str]
    citations: list[str]
    generated_answer: str
    needs_escalation: bool
    requires_approval: bool
    ticket_information: str
    action_taken: str
    error: str
    authorization_denied: bool
