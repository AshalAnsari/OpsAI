"""
Policy knowledge retrieval — Day 4.

Primary: static batch-indexed vector RAG (index-time / offline index).
  - Policies are chunked + embedded once into a local Chroma store.
  - Rebuild with: `python -m scripts.build_knowledge_index`
  - Not a continuous/CDC pipeline — docs do not auto-reindex on every file edit.

Fallback: keyword routing (naive RAG) if the index is missing or embeddings fail.
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import BACKEND_DIR, ROOT_DIR, get_settings

logger = logging.getLogger("harbordock.ai.rag")

POLICY_FILES = {
    "cancellation": "cancellation_policy.md",
    "refund": "refund_policy.md",
    "shipping": "shipping_policy.md",
    "payment": "payment_faq.md",
    "account": "account_policy.md",
}

COLLECTION_NAME = "harbordock_policies"


def _policy_dirs() -> list[Path]:
    candidates = [
        BACKEND_DIR / "knowledge",
        ROOT_DIR / "docs",
    ]
    return [p for p in candidates if p.is_dir()]


def chroma_dir() -> Path:
    return BACKEND_DIR / "knowledge" / "chroma"


def load_policy_text(filename: str) -> str | None:
    for directory in _policy_dirs():
        path = directory / filename
        if path.is_file():
            return path.read_text(encoding="utf-8")
    return None


def list_policy_paths() -> list[Path]:
    paths: list[Path] = []
    seen: set[str] = set()
    for directory in _policy_dirs():
        for filename in POLICY_FILES.values():
            path = directory / filename
            if path.is_file() and filename not in seen:
                seen.add(filename)
                paths.append(path)
    return paths


def _keyword_search(query: str) -> dict:
    """Naive keyword RAG - We will use this only as a FALLBACK."""
    q = (query or "").lower()
    selected: list[str] = []

    if any(w in q for w in ("cancel", "cancellation")):
        selected.append("cancellation")
    if any(w in q for w in ("refund", "money back", "chargeback")):
        selected.append("refund")
    if any(w in q for w in ("ship", "delivery", "tracking", "dispatch", "warehouse", "address")):
        selected.append("shipping")
    if any(w in q for w in ("payment", "stripe", "paid", "pending", "checkout")):
        selected.append("payment")
    if any(w in q for w in ("account", "password", "profile", "login")):
        selected.append("account")
    if any(w in q for w in ("warranty", "lifetime", "guarantee")):
        selected.extend(["cancellation", "refund", "shipping", "account"])

    if not selected:
        selected = ["cancellation", "refund", "shipping", "payment", "account"]

    ordered: list[str] = []
    for key in selected:
        if key not in ordered:
            ordered.append(key)

    chunks: list[str] = []
    citations: list[str] = []
    for key in ordered:
        filename = POLICY_FILES[key]
        text = load_policy_text(filename)
        if text:
            citations.append(filename)
            chunks.append(f"### {filename}\n{text.strip()}")

    if not chunks:
        return {
            "ok": False,
            "text": "No policy documents are available on the server.",
            "citations": [],
            "retrieval_mode": "keyword_fallback",
        }

    joined = "\n\n".join(chunks)
    if "warranty" in q or "lifetime" in q:
        if "warranty" not in joined.lower() and "lifetime" not in joined.lower():
            joined += (
                "\n\n### Note\n"
                "Harbor Dock Station policy files do not describe a lifetime warranty on all products. "
                "Do not invent one. Say it is unavailable and offer to open a support ticket."
            )

    return {
        "ok": True,
        "text": joined,
        "citations": citations,
        "retrieval_mode": "keyword_fallback",
    }


def _embeddings():
    from langchain_openai import OpenAIEmbeddings

    settings = get_settings()
    api_key = (settings.openrouter_api_key or settings.openai_api_key or "").strip()
    if not api_key:
        raise RuntimeError("No API key for embeddings")

    kwargs: dict = {
        "model": settings.ai_embedding_model,
        "api_key": api_key,
    }
    if settings.openrouter_api_key.strip():
        kwargs["base_url"] = settings.openrouter_base_url
    return OpenAIEmbeddings(**kwargs)


def build_static_policy_index(*, force: bool = False) -> dict:
    """
    Batch-build the static Chroma index from markdown policies.
    Call manually after policy edits — does not watch the filesystem.
    """
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    paths = list_policy_paths()
    if not paths:
        raise FileNotFoundError("No policy markdown files found under knowledge/ or docs/")

    persist = chroma_dir()
    persist.mkdir(parents=True, exist_ok=True)
    marker = persist / ".built"

    if marker.exists() and not force and any(persist.iterdir()):
        return {"ok": True, "skipped": True, "path": str(persist), "files": [p.name for p in paths]}

    docs: list[Document] = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for i, chunk in enumerate(splitter.split_text(text)):
            docs.append(
                Document(
                    page_content=chunk,
                    metadata={"source": path.name, "chunk": i},
                )
            )

    # Fresh collection
    import shutil

    if persist.exists() and force:
        shutil.rmtree(persist, ignore_errors=True)
        persist.mkdir(parents=True, exist_ok=True)

    Chroma.from_documents(
        documents=docs,
        embedding=_embeddings(),
        persist_directory=str(persist),
        collection_name=COLLECTION_NAME,
    )
    marker.write_text("static batch index\n", encoding="utf-8")
    logger.info("Built static policy index chunks=%s path=%s", len(docs), persist)
    return {
        "ok": True,
        "skipped": False,
        "chunks": len(docs),
        "path": str(persist),
        "files": [p.name for p in paths],
    }


def _vector_search(query: str, *, k: int = 4) -> dict:
    from langchain_chroma import Chroma

    persist = chroma_dir()
    if not (persist / ".built").exists():
        # One-time batch build on first use (still static — not a live file watcher).
        build_static_policy_index(force=True)

    store = Chroma(
        persist_directory=str(persist),
        embedding_function=_embeddings(),
        collection_name=COLLECTION_NAME,
    )
    hits = store.similarity_search(query, k=k)
    if not hits:
        return {
            "ok": False,
            "text": "No relevant policy chunks found.",
            "citations": [],
            "retrieval_mode": "static_vector",
        }

    citations: list[str] = []
    parts: list[str] = []
    for doc in hits:
        source = str(doc.metadata.get("source") or "policy")
        if source not in citations:
            citations.append(source)
        parts.append(f"### {source}\n{doc.page_content.strip()}")

    joined = "\n\n".join(parts)
    q = (query or "").lower()
    if "warranty" in q or "lifetime" in q:
        if "warranty" not in joined.lower() and "lifetime" not in joined.lower():
            joined += (
                "\n\n### Note\n"
                "Harbor Dock Station policy files do not describe a lifetime warranty on all products. "
                "Do not invent one. Say it is unavailable and offer to open a support ticket."
            )

    return {
        "ok": True,
        "text": joined,
        "citations": citations,
        "retrieval_mode": "static_vector",
    }


def search_company_policy(query: str) -> dict:
    """
    Retrieve company policy context for a customer question.

    Day 4 default: static vector RAG with keyword fallback.
    """
    settings = get_settings()
    mode = (settings.rag_mode or "auto").lower().strip()

    if mode == "keyword":
        return _keyword_search(query)

    if mode in {"auto", "vector", "static"}:
        try:
            return _vector_search(query)
        except Exception as exc:
            logger.warning("Static vector RAG failed (%s); using keyword fallback", exc)
            result = _keyword_search(query)
            result["retrieval_mode"] = "keyword_fallback"
            result["vector_error"] = str(exc)[:200]
            return result

    return _keyword_search(query)
