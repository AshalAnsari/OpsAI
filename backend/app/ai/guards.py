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


CROSS_CUSTOMER_REFUSAL = (
    "I can’t show another customer’s order details. "
    "For privacy, I can only access orders on your own Harbor Dock Station account. "
    "If you need help with one of your orders, send the order number (for example OP-10016)."
)
