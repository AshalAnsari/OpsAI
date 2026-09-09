"""
Batch-build the static policy vector index.

This is offline / index-time RAG — not a continuous update pipeline.
Re-run after editing files in backend/knowledge/*.md

  cd backend
  python -m scripts.build_knowledge_index
  python -m scripts.build_knowledge_index --force
"""

from __future__ import annotations

import argparse
import json
import sys

from app.ai.knowledge import build_static_policy_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Build static Harbor Dock Station policy Chroma index")
    parser.add_argument("--force", action="store_true", help="Rebuild even if an index already exists")
    args = parser.parse_args()
    try:
        result = build_static_policy_index(force=args.force)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
