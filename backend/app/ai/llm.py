"""LLM clients — OpenRouter via langchain_openai with cheap / medium routing (Cost Control).

Classify uses the cheap tier; answers route by intent. Soft max_tokens caps limit
completion cost. Token usage is extracted from provider metadata when available.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal, TypeVar

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.core.config import get_settings

ModelTier = Literal["cheap", "medium"]
CallName = Literal["classify", "answer"]

T = TypeVar("T", bound=BaseModel)

# Soft completion caps (structured-output JSON needs a little headroom).
MAX_TOKENS_CLASSIFY = 256
MAX_TOKENS_ANSWER_CHEAP = 600
MAX_TOKENS_ANSWER_MEDIUM = 1000

# Intents that can answer with the cheaper model after tools/RAG return structured facts.
CHEAP_ANSWER_INTENTS = frozenset(
    {
        "ORDER_STATUS",
        "PAYMENT_STATUS",
        "POLICY_QUESTION",
        "UNAUTHORIZED_ACCESS",
        "OFF_TOPIC",
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


def answer_max_tokens(tier: ModelTier) -> int:
    if tier == "medium":
        return MAX_TOKENS_ANSWER_MEDIUM
    return MAX_TOKENS_ANSWER_CHEAP


def empty_turn_usage() -> dict[str, Any]:
    return {
        "classify": None,
        "answer": None,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "llm_calls": 0,
    }


def _model_name_for_tier(tier: ModelTier) -> str:
    settings = get_settings()
    if tier == "medium":
        return (settings.ai_model_medium or settings.ai_model).strip()
    return (settings.ai_model_cheap or settings.ai_model).strip()


def extract_token_usage(raw_message: Any) -> dict[str, int]:
    """Pull prompt/completion counts from a LangChain AIMessage (best-effort)."""
    prompt = completion = total = 0

    usage_meta = getattr(raw_message, "usage_metadata", None) or {}
    if isinstance(usage_meta, dict) and usage_meta:
        prompt = int(usage_meta.get("input_tokens") or usage_meta.get("prompt_tokens") or 0)
        completion = int(usage_meta.get("output_tokens") or usage_meta.get("completion_tokens") or 0)
        total = int(usage_meta.get("total_tokens") or (prompt + completion))
        return {
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "total_tokens": total,
        }

    resp = getattr(raw_message, "response_metadata", None) or {}
    if not isinstance(resp, dict):
        resp = {}
    tu = resp.get("token_usage") or resp.get("usage") or {}
    if isinstance(tu, dict) and tu:
        prompt = int(tu.get("prompt_tokens") or tu.get("input_tokens") or 0)
        completion = int(tu.get("completion_tokens") or tu.get("output_tokens") or 0)
        total = int(tu.get("total_tokens") or (prompt + completion))

    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
    }


def record_call_usage(
    usage: dict[str, Any] | None,
    call: CallName,
    *,
    tier: ModelTier,
    raw_message: Any = None,
    counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Attach one LLM call's usage and recompute turn totals."""
    out = dict(usage or empty_turn_usage())
    if counts is None:
        counts = extract_token_usage(raw_message) if raw_message is not None else {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
    out[call] = {
        "model": _model_name_for_tier(tier),
        "prompt_tokens": int(counts.get("prompt_tokens") or 0),
        "completion_tokens": int(counts.get("completion_tokens") or 0),
        "total_tokens": int(counts.get("total_tokens") or 0),
    }

    prompt = completion = 0
    calls = 0
    for key in ("classify", "answer"):
        block = out.get(key)
        if not isinstance(block, dict):
            continue
        calls += 1
        prompt += int(block.get("prompt_tokens") or 0)
        completion += int(block.get("completion_tokens") or 0)
    out["prompt_tokens"] = prompt
    out["completion_tokens"] = completion
    out["total_tokens"] = prompt + completion
    out["llm_calls"] = calls
    return out


@lru_cache
def get_chat_model(tier: ModelTier = "cheap", max_tokens: int = 600) -> ChatOpenAI:
    settings = get_settings()
    api_key = (settings.openrouter_api_key or settings.openai_api_key or "").strip()
    if not api_key:
        raise RuntimeError(
            "No LLM API key configured. Set OPENROUTER_API_KEY (preferred) or OPENAI_API_KEY in .env."
        )

    model = _model_name_for_tier(tier)
    common: dict[str, Any] = {
        "model": model,
        "temperature": 0,
        "max_tokens": max(1, int(max_tokens)),
    }

    if settings.openrouter_api_key.strip():
        return ChatOpenAI(
            api_key=settings.openrouter_api_key.strip(),
            base_url=settings.openrouter_base_url,
            **common,
        )

    # Direct OpenAI: strip provider prefix if present
    plain = model.split("/")[-1] if "/" in model else model
    return ChatOpenAI(model=plain, api_key=api_key, temperature=0, max_tokens=max(1, int(max_tokens)))


def invoke_structured(
    model: ChatOpenAI,
    schema: type[T],
    messages: list[BaseMessage],
    *,
    tier: ModelTier,
    call: CallName,
    prior_usage: dict[str, Any] | None = None,
) -> tuple[T, dict[str, Any]]:
    """Invoke structured output and return (parsed, updated turn usage)."""
    raw_out = model.with_structured_output(schema, include_raw=True).invoke(messages)
    if not isinstance(raw_out, dict):
        raise RuntimeError("Structured LLM call did not return include_raw payload")

    parsed = raw_out.get("parsed")
    if parsed is None:
        err = raw_out.get("parsing_error")
        raise RuntimeError(f"Structured LLM parse failed: {err!r}")

    usage = record_call_usage(
        prior_usage,
        call,
        tier=tier,
        raw_message=raw_out.get("raw"),
    )
    return parsed, usage  # type: ignore[return-value]
