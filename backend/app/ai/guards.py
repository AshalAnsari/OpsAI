"""Deterministic Day 3 guardrails (We cannot rely on LLM Alone)."""

from __future__ import annotations

import re

# Known demo customers / third-party phrasing for TC09.
_OTHER_CUSTOMER_PATTERNS = [
    re.compile(r"\bben\s+harbou?r\b", re.I),
    re.compile(r"\banother\s+customer('s)?\b", re.I),
    re.compile(r"\bsomeone\s+else('s)?\b", re.I),
    re.compile(r"\bother\s+customer('s)?\b", re.I),
    re.compile(r"\bnot\s+my\s+order\b", re.I),
    re.compile(r"\b(his|her|their)\s+order\b", re.I),
]

_CANCEL_PATTERNS = [
    re.compile(r"\bcancel(l?ing|led)?\b", re.I),
]

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.I),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above)", re.I),
    re.compile(r"you\s+are\s+now\s+", re.I),
]


def is_cross_customer_request(message: str) -> bool:
    """True when the user asks about another person's orders (TC09)."""
    text = message or ""
    return any(p.search(text) for p in _OTHER_CUSTOMER_PATTERNS)


def looks_like_cancellation(message: str) -> bool:
    text = message or ""
    return any(p.search(text) for p in _CANCEL_PATTERNS)


def looks_like_prompt_injection(message: str) -> bool:
    text = message or ""
    return any(p.search(text) for p in _INJECTION_PATTERNS)


_CONFIRM_CANCEL_PATTERNS = [
    re.compile(r"\bi\s+confirm\b", re.I),
    re.compile(r"\bconfirm(\s+cancel|\s+cancellation)?\b", re.I),
    re.compile(r"\byes[,.]?\s*(please\s+)?(cancel|do\s+it|proceed)\b", re.I),
    re.compile(r"\b(go\s+ahead|please\s+proceed|do\s+it)\b", re.I),
    re.compile(r"^\s*yes\s*[.!?]?\s*$", re.I),
    re.compile(r"^\s*confirm\s*[.!?]?\s*$", re.I),
]


def message_confirms_cancel(message: str) -> bool:
    """True when the user explicitly confirms cancel in natural language (TC02)."""
    text = (message or "").strip()
    if not text:
        return False
    return any(p.search(text) for p in _CONFIRM_CANCEL_PATTERNS)


_AMBIGUOUS_CANCEL_PATTERNS = [
    re.compile(r"^\s*(please\s+)?cancel(\s+it)?\s*[!.?]?\s*$", re.I),
    re.compile(r"^\s*(please\s+)?cancel\s+my\s+order\s*[!.?]?\s*$", re.I),
]


def _message_has_order_ref(text: str) -> bool:
    if re.search(r"\bOP-\d+\b", text, flags=re.IGNORECASE):
        return True
    if re.search(r"#\s*\d+\b", text):
        return True
    if re.search(r"\border\s+#?\s*\d+\b", text, flags=re.IGNORECASE):
        return True
    return False


def is_ambiguous_cancel_request(message: str) -> bool:
    """True when cancel is requested with no order id (BR04) — do not reuse last-order hint."""
    text = (message or "").strip()
    if not text:
        return False
    if _message_has_order_ref(text):
        return False
    if message_confirms_cancel(text):
        return False
    return any(p.match(text) for p in _AMBIGUOUS_CANCEL_PATTERNS)


CROSS_CUSTOMER_REFUSAL = (
    "I can’t show another customer’s order details. "
    "For privacy, I can only access orders on your own Harbor Dock Station account. "
    "If you need help with one of your orders, send the order number (for example OP-10016)."
)

# Obvious non-support asks (math, trivia, entertainment). Support keywords win.
_SUPPORT_HINT_PATTERNS = [
    re.compile(
        r"\b(order|orders|cancel|cancellation|refund|shipping|shipped|delivery|delivered|"
        r"payment|paid|pending|policy|policies|ticket|account|password|login|warranty|"
        r"return|address|tracking|fulfillment|invoice|checkout|cart|product|products)\b",
        re.I,
    ),
    re.compile(r"\bOP-\d+\b", re.I),
    re.compile(r"\bharbor\s+dock\b", re.I),
]

_OFF_TOPIC_PATTERNS = [
    re.compile(r"\b\d+\s*[+\-×x*/÷]\s*\d+\b", re.I),
    re.compile(r"\bwhat\s+is\s+\d+\s*[+\-×x*/÷]", re.I),
    re.compile(r"\b(calculate|solve|math|equation)\b", re.I),
    re.compile(r"\b(tell\s+me\s+a\s+joke|write\s+(me\s+)?a\s+(poem|story|song))\b", re.I),
    re.compile(r"\b(weather|forecast|stock\s+price|bitcoin|capital\s+of)\b", re.I),
    re.compile(r"\bwho\s+(won|is\s+the\s+president|invented)\b", re.I),
    re.compile(r"\b(translate\s+this|code\s+a|write\s+python)\b", re.I),
]


def looks_like_support_related(message: str) -> bool:
    text = message or ""
    return any(p.search(text) for p in _SUPPORT_HINT_PATTERNS)


def is_off_topic_request(message: str) -> bool:
    """True for clear non-support asks (e.g. math). Support wording always wins."""
    text = (message or "").strip()
    if not text:
        return False
    if looks_like_support_related(text):
        return False
    return any(p.search(text) for p in _OFF_TOPIC_PATTERNS)


OFF_TOPIC_REFUSAL = (
    "I’m Harbor Dock Station AI Support — I only help with your orders, payments, "
    "shipping, cancellations, refunds, and company policies. "
    "I can’t answer general questions (for example math or trivia). "
    "Send an order id like OP-10016, ask about a policy, or open a classic support ticket for a human."
)
