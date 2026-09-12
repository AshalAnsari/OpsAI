"""Unit tests for LLM cost helpers (no live API calls)."""

from types import SimpleNamespace

from app.ai.llm import (
    MAX_TOKENS_ANSWER_CHEAP,
    MAX_TOKENS_ANSWER_MEDIUM,
    MAX_TOKENS_CLASSIFY,
    answer_max_tokens,
    answer_model_tier,
    empty_turn_usage,
    extract_token_usage,
    record_call_usage,
)


def test_answer_tier_routing():
    assert answer_model_tier("ORDER_STATUS") == "cheap"
    assert answer_model_tier("ORDER_CANCELLATION") == "medium"
    assert answer_max_tokens("cheap") == MAX_TOKENS_ANSWER_CHEAP
    assert answer_max_tokens("medium") == MAX_TOKENS_ANSWER_MEDIUM
    assert MAX_TOKENS_CLASSIFY < MAX_TOKENS_ANSWER_CHEAP


def test_extract_usage_from_usage_metadata():
    msg = SimpleNamespace(
        usage_metadata={"input_tokens": 100, "output_tokens": 40, "total_tokens": 140},
        response_metadata={},
    )
    assert extract_token_usage(msg) == {
        "prompt_tokens": 100,
        "completion_tokens": 40,
        "total_tokens": 140,
    }


def test_extract_usage_from_response_metadata():
    msg = SimpleNamespace(
        usage_metadata=None,
        response_metadata={"token_usage": {"prompt_tokens": 50, "completion_tokens": 10}},
    )
    assert extract_token_usage(msg) == {
        "prompt_tokens": 50,
        "completion_tokens": 10,
        "total_tokens": 60,
    }


def test_record_call_usage_totals():
    usage = empty_turn_usage()
    usage = record_call_usage(
        usage,
        "classify",
        tier="cheap",
        counts={"prompt_tokens": 200, "completion_tokens": 30, "total_tokens": 230},
    )
    usage = record_call_usage(
        usage,
        "answer",
        tier="cheap",
        counts={"prompt_tokens": 800, "completion_tokens": 120, "total_tokens": 920},
    )
    assert usage["llm_calls"] == 2
    assert usage["prompt_tokens"] == 1000
    assert usage["completion_tokens"] == 150
    assert usage["total_tokens"] == 1150
    assert usage["classify"]["prompt_tokens"] == 200
    assert usage["answer"]["completion_tokens"] == 120
