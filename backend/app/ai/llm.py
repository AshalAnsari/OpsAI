"""LLM clients — OpenRouter via langchain_openai with cheap / medium routing (Cost Control).

Although we first do an anlysis of the simplar queries and classify, then decide
what type of queries can be resolved with a cheaper model
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from langchain_openai import ChatOpenAI

from app.core.config import get_settings

ModelTier = Literal["cheap", "medium"]

# Intents that can answer with the cheaper model after tools/RAG return structured facts.
CHEAP_ANSWER_INTENTS = frozenset(
    {
        "ORDER_STATUS",
        "PAYMENT_STATUS",
        "POLICY_QUESTION",
        "UNAUTHORIZED_ACCESS",
    }
)

# Higher-stakes or multi-constraint answers use the medium model.
MEDIUM_ANSWER_INTENTS = frozenset(
    {
        "ORDER_CANCELLATION",
        "REFUND_REQUEST",
        "DELIVERY_ISSUE",
        "ORDER_CHANGE",
        "GENERAL_SUPPORT",
    }
)


def answer_model_tier(intent: str | None) -> ModelTier:
    if (intent or "") in MEDIUM_ANSWER_INTENTS:
        return "medium"
    return "cheap"


@lru_cache
def get_chat_model(tier: ModelTier = "cheap") -> ChatOpenAI:
    settings = get_settings()
    api_key = (settings.openrouter_api_key or settings.openai_api_key or "").strip()
    if not api_key:
        raise RuntimeError(
            "No LLM API key configured. Set OPENROUTER_API_KEY (preferred) or OPENAI_API_KEY in .env."
        )

    if tier == "medium":
        model = (settings.ai_model_medium or settings.ai_model).strip()
    else:
        model = (settings.ai_model_cheap or settings.ai_model).strip()

    if settings.openrouter_api_key.strip():
        return ChatOpenAI(
            model=model,
            api_key=settings.openrouter_api_key.strip(),
            base_url=settings.openrouter_base_url,
            temperature=0,
        )

    # Direct OpenAI: strip provider prefix if present
    plain = model.split("/")[-1] if "/" in model else model
    return ChatOpenAI(model=plain, api_key=api_key, temperature=0) ### Keeping temp 0 for deterministic to-the-point reasoning to the user
