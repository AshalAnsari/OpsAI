"""
AI tools that call Harbor Dock Station services (LLM should never MySQL directly).

Same idea as my other project having toolcall.ipynb / MCP tools — but wired to real OrderService
and SupportService with the authenticated customer.
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.ai.knowledge import search_company_policy
from app.models.role import User
from app.schemas.support import TicketCreate
from app.services.order_service import OrderService
from app.services.support_service import SupportService
from app.utils.exceptions import AppError


def _to_internal_order_id(raw: int) -> int:
    """Map customer-facing numbers to DB ids.

    Harbor Dock Station display ids are ``OP-{10000 + id}`` (e.g. OP-10015 → 15).
    Customers often type ``#10015`` or ``10015`` without the ``OP-`` prefix — treat
    values >= 10000 as display numbers, not raw primary keys.
    """
    if raw >= 10000:
        return raw - 10000
    return raw


def parse_order_id(text: str, hint: int | None = None) -> int | None:
    if hint is not None and hint > 0:
        return _to_internal_order_id(hint)
    if not text:
        return None

    display = re.search(r"\bOP-(\d+)\b", text, flags=re.IGNORECASE)
    if display:
        return _to_internal_order_id(int(display.group(1)))

    hashed = re.search(r"#\s*(\d+)\b", text)
    if hashed:
        return _to_internal_order_id(int(hashed.group(1)))

    order_word = re.search(r"\border\s+#?\s*(\d+)\b", text, flags=re.IGNORECASE)
    if order_word:
        return _to_internal_order_id(int(order_word.group(1)))

    return None


class HarborTools:
    def __init__(self, db: Session, customer: User) -> None:
        self.db = db
        self.customer = customer
        self.orders = OrderService(db)
        self.support = SupportService(db)

    def get_my_order(self, order_id: int) -> dict[str, Any]:
        """Return the authenticated customer's order (ownership enforced)."""
        try:
            order = self.orders.get_customer_order(self.customer, order_id)
            payload = order.model_dump(mode="json")
            return {"ok": True, "tool": "get_my_order", "order": payload}
        except AppError as exc:
            return {
                "ok": False,
                "tool": "get_my_order",
                "error_code": exc.code,
                "error": exc.message,
            }

    def get_my_orders(self, limit: int = 5) -> dict[str, Any]:
        from app.utils.pagination import PaginationParams

        try:
            page = self.orders.list_customer_orders(
                self.customer,
                PaginationParams(page=1, page_size=limit),
                status=None,
            )
            items = [o.model_dump(mode="json") for o in page.items]
            return {"ok": True, "tool": "get_my_orders", "orders": items, "total": page.total}
        except AppError as exc:
            return {
                "ok": False,
                "tool": "get_my_orders",
                "error_code": exc.code,
                "error": exc.message,
            }

    def cancel_my_order(self, order_id: int) -> dict[str, Any]:
        try:
            order = self.orders.cancel_customer_order(self.customer, order_id)
            return {
                "ok": True,
                "tool": "cancel_my_order",
                "order": order.model_dump(mode="json"),
                "action_taken": "cancel",
            }
        except AppError as exc:
            return {
                "ok": False,
                "tool": "cancel_my_order",
                "error_code": exc.code,
                "error": exc.message,
            }

    def create_support_ticket(self, subject: str, message: str) -> dict[str, Any]:
        try:
            ticket = self.support.create_ticket(
                self.customer,
                TicketCreate(subject=subject[:200], message=message[:5000]),
            )
            return {
                "ok": True,
                "tool": "create_support_ticket",
                "ticket": ticket.model_dump(mode="json"),
                "action_taken": "ticket_created",
            }
        except AppError as exc:
            return {
                "ok": False,
                "tool": "create_support_ticket",
                "error_code": exc.code,
                "error": exc.message,
            }

    def search_knowledge(self, query: str) -> dict[str, Any]:
        result = search_company_policy(query)
        return {
            "ok": result["ok"],
            "tool": "search_knowledge",
            "text": result["text"],
            "citations": result["citations"],
        }
