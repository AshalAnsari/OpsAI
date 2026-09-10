"""
LangGraph support workflow — Day 3 hardened:

  START → classify → run_tools → determine_escalation
        → [create_ticket?] → generate_answer → END

Ticket creation runs *before* the customer-facing answer so TC07 can cite the ticket id.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.guards import (
    CROSS_CUSTOMER_REFUSAL,
    is_ambiguous_cancel_request,
    is_cross_customer_request,
    looks_like_cancellation,
    looks_like_prompt_injection,
    message_confirms_cancel,
)
from app.ai.llm import answer_model_tier, get_chat_model
from app.ai.state import SupportState
from app.ai.tools import HarborTools, parse_order_id
from app.models.role import User

logger = logging.getLogger("harbordock.ai")

CLASSIFY_PROMPT = """
You are Harbor Dock Station support triage.

From the customer message only, classify:
- intent: ORDER_STATUS | ORDER_CANCELLATION | PAYMENT_STATUS | REFUND_REQUEST | POLICY_QUESTION | DELIVERY_ISSUE | ORDER_CHANGE | GENERAL_SUPPORT | UNAUTHORIZED_ACCESS
- risk_level: READ | LOW_RISK_WRITE | HIGH_RISK
- summary: short summary
- order_id: integer if clearly present. Harbor Dock Station display ids are OP-10xxx:
  OP-10015 / #10015 / 10015 → 15; bare #18 → 18. Prefer the numeric DB id in this field.

Guidance:
- "where is my order" / tracking → ORDER_STATUS, READ
- cancel order → ORDER_CANCELLATION, LOW_RISK_WRITE
- payment pending / paid? → PAYMENT_STATUS, READ
- refund / money back → REFUND_REQUEST, HIGH_RISK
- cancellation/refund/shipping policy questions (no specific order action) → POLICY_QUESTION, READ
- delivered but missing → DELIVERY_ISSUE, HIGH_RISK
- change address after ship → ORDER_CHANGE, READ (reject/explain; not automatic ticket)
- warranty / unknown → POLICY_QUESTION or GENERAL_SUPPORT, READ
- asking for another customer's / Ben Harbor's orders → UNAUTHORIZED_ACCESS, READ

Do not answer the customer here; only classify.
"""

ANSWER_PROMPT = """
You are Harbor Dock Station AI Support.

Write a clear, professional reply using ONLY tool_results, ticket_information, and retrieved policy context.
Rules:
- Do not invent order status, location, payment state, policies, warranties, or refunds.
- If authorization_denied is true, refuse clearly: you can only access the logged-in customer's orders. Do not list any orders as belonging to another person.
- If a tool error says order not found, say you could not find that order for this account.
- If policy context says information is unavailable (e.g. lifetime warranty), say so. Do not invent a warranty.
- For REFUND_REQUEST: never claim a refund was processed. Say a human must approve.
- If ticket_information shows a created ticket, tell the customer the ticket display_id was already opened — do NOT ask them to open another ticket.
- For ORDER_CANCELLATION: if cancel was executed (action_taken=cancel), confirm success with the new status. If eligible but not yet cancelled, ask them to confirm by either (1) checking Confirm cancel and sending again, or (2) replying "yes, confirm cancel" / "I confirm cancel" with the same order id — do NOT open a support ticket for a normal eligible cancel. If not eligible (dispatched/delivered), explain why — do not pretend a cancel happened. If no order id is present and tool results only list multiple orders (or ask for id), ask which order to cancel — do not assume a previous order.
- For ORDER_CHANGE on a dispatched order: clearly refuse; do not imply a refund was filed unless a ticket was actually created.
- Prefer display_id (OP-…) when referring to orders.
- Tool results for get_my_orders are ALWAYS the current user's orders only — never rename them as another person's.
- Do not mention LangGraph, RAG, or internal systems.
- Keep the answer concise.
"""


class ClassifyResult(BaseModel):
    intent: Literal[
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
    risk_level: Literal["READ", "LOW_RISK_WRITE", "HIGH_RISK"]
    summary: str = Field(description="Short summary of the customer issue")
    order_id: int | None = Field(default=None, description="Numeric order id if present")


class AnswerResult(BaseModel):
    generated_answer: str


def _cancellable_status(status: str | None) -> bool:
    return (status or "").lower() in {"pending", "confirmed", "processing"}


def build_support_graph(db: Session, customer: User):
    tools = HarborTools(db, customer)
    # Classification is structured and short → cheaper model (cost control).
    classify_model = get_chat_model("cheap")

    def classify(state: SupportState) -> dict[str, Any]:
        user_message = state["user_message"]

        # Deterministic TC09 guard — do not trust the LLM alone.
        if is_cross_customer_request(user_message):
            return {
                "intent": "UNAUTHORIZED_ACCESS",
                "risk_level": "READ",
                "summary": "Request for another customer's order data",
                "order_id": None,
                "authorization_denied": True,
                "tools_called": [],
                "tool_results": [],
                "citations": [],
                "action_taken": "none",
                "error": "cross_customer_denied",
                "retrieved_information": "",
                "needs_escalation": False,
                "requires_approval": False,
                "ticket_information": "",
            }

        result = classify_model.with_structured_output(ClassifyResult).invoke(
            [
                SystemMessage(content=CLASSIFY_PROMPT),
                HumanMessage(content=user_message),
            ]
        )
        parsed = parse_order_id(user_message, result.order_id)
        # Reuse client order_id_hint only when safe (TC02 confirm). Never on ambiguous "cancel it" (BR04).
        if parsed is None and state.get("order_id"):
            if message_confirms_cancel(user_message):
                parsed = state.get("order_id")
            elif is_ambiguous_cancel_request(user_message):
                parsed = None
            elif not looks_like_cancellation(user_message):
                parsed = state.get("order_id")
            # else: cancel wording without id → leave None so tools list orders / ask

        intent = result.intent
        risk = result.risk_level

        # TC03: cancel wording must not collapse into POLICY_QUESTION-only.
        if looks_like_cancellation(user_message) and intent in {
            "POLICY_QUESTION",
            "GENERAL_SUPPORT",
            "ORDER_STATUS",
        }:
            intent = "ORDER_CANCELLATION"
            risk = "LOW_RISK_WRITE"

        # Ambiguous cancel with no id should still be cancellation intent (ask which order).
        if is_ambiguous_cancel_request(user_message):
            intent = "ORDER_CANCELLATION"
            risk = "LOW_RISK_WRITE"

        # TC02: short confirm replies ("yes", "I confirm cancel") are still cancellations.
        if message_confirms_cancel(user_message):
            intent = "ORDER_CANCELLATION"
            risk = "LOW_RISK_WRITE"

        if looks_like_prompt_injection(user_message) and (
            "refund" in user_message.lower() or intent == "REFUND_REQUEST"
        ):
            intent = "REFUND_REQUEST"
            risk = "HIGH_RISK"

        return {
            "intent": intent,
            "risk_level": risk,
            "summary": result.summary,
            "order_id": parsed,
            "authorization_denied": intent == "UNAUTHORIZED_ACCESS",
            "tools_called": [],
            "tool_results": [],
            "citations": [],
            "action_taken": "none",
            "error": "",
            "retrieved_information": "",
            "ticket_information": "",
        }

    def run_tools(state: SupportState) -> dict[str, Any]:
        intent = state.get("intent") or "GENERAL_SUPPORT"
        if state.get("authorization_denied") or intent == "UNAUTHORIZED_ACCESS":
            return {
                "tools_called": [],
                "tool_results": [
                    {
                        "ok": False,
                        "tool": "authorization_guard",
                        "error_code": "UNAUTHORIZED",
                        "error": CROSS_CUSTOMER_REFUSAL,
                    }
                ],
                "retrieved_information": "",
                "citations": [],
                "action_taken": "none",
                "error": "cross_customer_denied",
                "authorization_denied": True,
            }

        order_id = state.get("order_id")
        # Checkbox OR natural-language confirm ("yes", "I confirm cancel", …).
        confirm_cancel = bool(state.get("confirm_cancel")) or message_confirms_cancel(
            state.get("user_message") or ""
        )
        called: list[str] = []
        results: list[dict[str, Any]] = []
        citations: list[str] = []
        action_taken = "none"
        retrieved = ""
        error = ""

        needs_order = intent in {
            "ORDER_STATUS",
            "ORDER_CANCELLATION",
            "PAYMENT_STATUS",
            "REFUND_REQUEST",
            "DELIVERY_ISSUE",
            "ORDER_CHANGE",
        }
        # Policy alone for pure POLICY_QUESTION / GENERAL; cancellation also gets policy after order.
        needs_policy = intent in {
            "POLICY_QUESTION",
            "ORDER_CANCELLATION",
            "REFUND_REQUEST",
            "ORDER_CHANGE",
            "GENERAL_SUPPORT",
            "DELIVERY_ISSUE",
        }

        order_payload: dict[str, Any] | None = None

        if needs_order:
            if order_id is None:
                # TC09-safe: listing is only for the authenticated user, and never when
                # asking about someone else (already blocked above).
                listed = tools.get_my_orders(limit=5)
                called.append("get_my_orders")
                results.append(listed)
                error = "No order id found in the message; listed your recent orders instead."
                # TC03/TC08: if exactly one recent order, use it as hint for cancel/change flows.
                if intent in {"ORDER_CANCELLATION", "ORDER_CHANGE"} and listed.get("ok"):
                    orders = listed.get("orders") or []
                    if len(orders) == 1:
                        order_id = int(orders[0]["id"])
            if order_id is not None:
                got = tools.get_my_order(order_id)
                called.append("get_my_order")
                results.append(got)
                if got.get("ok"):
                    order_payload = got.get("order") or {}
                else:
                    error = str(got.get("error") or "Order lookup failed")

        if intent == "ORDER_CANCELLATION" and order_id is not None and order_payload:
            status = str(order_payload.get("status") or "")
            if confirm_cancel and _cancellable_status(status):
                cancelled = tools.cancel_my_order(order_id)
                called.append("cancel_my_order")
                results.append(cancelled)
                if cancelled.get("ok"):
                    action_taken = "cancel"
                else:
                    error = str(cancelled.get("error") or error)
            elif confirm_cancel and not _cancellable_status(status):
                error = (
                    error
                    or f"Order cannot be cancelled in status '{status}' (already left warehouse or terminal)."
                )

        if needs_policy:
            knowledge = tools.search_knowledge(state["user_message"])
            called.append("search_knowledge")
            results.append(
                {
                    "ok": knowledge.get("ok"),
                    "tool": "search_knowledge",
                    "citations": knowledge.get("citations"),
                    "retrieval_mode": knowledge.get("retrieval_mode"),
                }
            )
            retrieved = str(knowledge.get("text") or "")
            citations = list(knowledge.get("citations") or [])

        return {
            "order_id": order_id,
            "tools_called": called,
            "tool_results": results,
            "retrieved_information": retrieved,
            "citations": citations,
            "action_taken": action_taken,
            "error": error,
        }

    def determine_escalation(state: SupportState) -> dict[str, Any]:
        if state.get("authorization_denied"):
            return {"needs_escalation": False, "requires_approval": False}

        intent = state.get("intent")
        # Refunds and missing-package claims need humans. Address change: reject in-chat (TC08).
        if intent == "REFUND_REQUEST":
            return {"needs_escalation": True, "requires_approval": True}
        if intent == "DELIVERY_ISSUE":
            return {"needs_escalation": True, "requires_approval": True}
        if intent == "ORDER_CHANGE":
            return {"needs_escalation": False, "requires_approval": False}
        if looks_like_prompt_injection(state.get("user_message") or "") and intent == "REFUND_REQUEST":
            return {"needs_escalation": True, "requires_approval": True}
        return {"needs_escalation": False, "requires_approval": False}

    def create_ticket(state: SupportState) -> dict[str, Any]:
        if not state.get("needs_escalation"):
            return {"ticket_information": "No ticket created."}

        subject = f"AI escalation: {state.get('intent')} — {state.get('summary') or 'support'}"
        order_bit = f"Order id: {state.get('order_id')}\n" if state.get("order_id") else ""
        body = (
            f"{order_bit}"
            f"Customer message: {state.get('user_message')}\n\n"
            f"AI summary: {state.get('summary')}\n"
            f"Requires approval: {state.get('requires_approval')}\n"
        )
        created = tools.create_support_ticket(subject=subject[:200], message=body[:5000])
        called = list(state.get("tools_called") or [])
        called.append("create_support_ticket")
        results = list(state.get("tool_results") or [])
        results.append(created)
        action = "ticket_created" if created.get("ok") else state.get("action_taken") or "none"
        return {
            "ticket_information": json.dumps(created, default=str),
            "tools_called": called,
            "tool_results": results,
            "action_taken": action,
        }

    def generate_answer(state: SupportState) -> dict[str, Any]:
        if state.get("authorization_denied"):
            return {"generated_answer": CROSS_CUSTOMER_REFUSAL}

        human_content = f"""Customer message: {state.get("user_message")}
Intent: {state.get("intent")}
Risk level: {state.get("risk_level")}
Summary: {state.get("summary")}
Order id: {state.get("order_id")}
Confirm cancel flag: {state.get("confirm_cancel")}
Action taken: {state.get("action_taken")}
Authorization denied: {state.get("authorization_denied")}
Requires approval: {state.get("requires_approval")}
Needs escalation: {state.get("needs_escalation")}
Tool error note: {state.get("error")}

Ticket information:
{state.get("ticket_information") or "(none)"}

Tool results (JSON):
{json.dumps(state.get("tool_results") or [], default=str)[:12000]}

Policy context:
{state.get("retrieved_information") or "(none)"}
"""
        tier = answer_model_tier(str(state.get("intent") or ""))
        answer_model = get_chat_model(tier)
        result = answer_model.with_structured_output(AnswerResult).invoke(
            [
                SystemMessage(content=ANSWER_PROMPT),
                HumanMessage(content=human_content),
            ]
        )
        return {"generated_answer": result.generated_answer}

    def route_escalation(state: SupportState):
        if state.get("needs_escalation"):
            return "create_ticket"
        return "generate_answer"

    graph = StateGraph(SupportState)
    graph.add_node("classify", classify)
    graph.add_node("run_tools", run_tools)
    graph.add_node("determine_escalation", determine_escalation)
    graph.add_node("create_ticket", create_ticket)
    graph.add_node("generate_answer", generate_answer)

    graph.add_edge(START, "classify")
    graph.add_edge("classify", "run_tools")
    graph.add_edge("run_tools", "determine_escalation")
    graph.add_conditional_edges(
        "determine_escalation",
        route_escalation,
        {"create_ticket": "create_ticket", "generate_answer": "generate_answer"},
    )
    graph.add_edge("create_ticket", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()
