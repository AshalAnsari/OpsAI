"""LLM client — OpenRouter via langchain_openai (Using the same method as my previous project)."""

from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.core.config import get_settings


@lru_cache
def get_chat_model() -> ChatOpenAI:
    settings = get_settings()
    api_key = (settings.openrouter_api_key or settings.openai_api_key or "").strip()
    if not api_key:
        raise RuntimeError(
            "No LLM API key configured. Set OPENROUTER_API_KEY (preferred) or OPENAI_API_KEY in .env."
        )

    # Prefer OpenRouter when that key is set (matches AI Roadmap notebooks).
    if settings.openrouter_api_key.strip():
        return ChatOpenAI(
            model=settings.ai_model,
            api_key=settings.openrouter_api_key.strip(),
            base_url=settings.openrouter_base_url,
            temperature=0,
        )

    return ChatOpenAI(
        model=settings.ai_model if "/" not in settings.ai_model else "gpt-4o-mini",
        api_key=api_key,
        temperature=0, ### Keeping it highlighly deterministic for to-the-point reasoning to the users
    )
