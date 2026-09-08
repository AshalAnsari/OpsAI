"""Simple policy retrieval — keyword routing over markdown docs (v0 RAG)."""

from pathlib import Path

from app.core.config import BACKEND_DIR, ROOT_DIR

POLICY_FILES = {
    "cancellation": "cancellation_policy.md",
    "refund": "refund_policy.md",
    "shipping": "shipping_policy.md",
    "payment": "payment_faq.md",
    "account": "account_policy.md",
}


def _policy_dirs() -> list[Path]:
    candidates = [
        BACKEND_DIR / "knowledge",
        ROOT_DIR / "docs",
    ]
    return [p for p in candidates if p.is_dir()]


def load_policy_text(filename: str) -> str | None:
    for directory in _policy_dirs():
        path = directory / filename
        if path.is_file():
            return path.read_text(encoding="utf-8")
    return None


def search_company_policy(query: str) -> dict:
    """
    Retrieve company policy text for a customer question.

    Prefer the most relevant policy file; fall back to a short index of all policies.
    """
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
        # Explicitly probe cancellation/refund/shipping so we can say "not in KB"
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
        }

    # Warranty / unknown: if nothing mentions warranty, say so clearly for the model.
    joined = "\n\n".join(chunks)
    if "warranty" in q or "lifetime" in q:
        if "warranty" not in joined.lower() and "lifetime" not in joined.lower():
            joined += (
                "\n\n### Note\n"
                "Harbor Dock Station policy files do not describe a lifetime warranty on all products. "
                "Do not invent one. Say it is unavailable and offer to open a support ticket."
            )

    return {"ok": True, "text": joined, "citations": citations}
