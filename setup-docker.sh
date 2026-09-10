#!/usr/bin/env bash
# Harbor Dock Station — one-command Docker setup for clones / graders.
#
# What this does:
#   1. Ensures .env exists (from .env.example)
#   2. Starts MySQL + API + UI via docker-compose.dev.yml
#   3. Waits until the API is healthy (migrations + deterministic seed run in backend CMD)
#   4. Best-effort: rebuilds the static policy RAG index inside the backend container
#   5. Prints demo accounts + Ava's seeded order IDs for AI Support testing
#
# Usage:
#   ./setup-docker.sh                 # build, start detached, verify seed
#   ./setup-docker.sh --foreground    # attach logs (Ctrl+C stops stack)
#   ./setup-docker.sh --reset         # wipe MySQL volume then start (fresh OP-10001…)
#   ./setup-docker.sh --help
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

COMPOSE_FILE="docker-compose.dev.yml"
FOREGROUND=0
RESET=0
NO_BUILD=0

usage() {
  cat <<'EOF'
Harbor Dock Station — Docker setup

Usage:
  ./setup-docker.sh [options]

Options:
  --foreground, -f   Start attached (logs in terminal; Ctrl+C stops)
  --reset            Wipe DB volume then start — fresh deterministic seed
  --no-build         Skip --build (faster restart)
  -h, --help         Show this help

Default: starts in the background (--detach), waits for health, prints credentials.

After startup:
  Frontend   http://localhost:3000
  API        http://localhost:8000
  AI Support http://localhost:3000/support/ai
  Swagger    http://localhost:8000/docs

Demo accounts: DEMO-ACCOUNTS.md
Put OPENROUTER_API_KEY in .env before testing AI Support.
EOF
}

print_credentials() {
  cat <<'EOF'

-------- Demo accounts --------
  Admin:    admin@harbordock.demo / AdminDemo123!
  Customer: ava.north@harbordock.demo / CustomerDemo123!

-------- Ava orders (fresh DB / --reset) --------
  OP-10001  pending / payment pending   — cancel + payment questions
  OP-10002  dispatched / paid           — late cancel / address change
  OP-10003  delivered / paid            — missing package
  OP-10004  confirmed / paid            — refund HITL
  OP-10005  out_for_delivery / paid     — live status

  AI Support: http://localhost:3000/support/ai
  Details:    DEMO-ACCOUNTS.md
--------------------------------
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --foreground|-f) FOREGROUND=1; shift ;;
    --detach|-d)
      # default behavior; accepted for compatibility
      FOREGROUND=0
      shift
      ;;
    --reset) RESET=1; shift ;;
    --no-build) NO_BUILD=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is not installed or not on PATH." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Error: Docker Compose v2 is required (docker compose)." >&2
  exit 1
fi

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Error: $COMPOSE_FILE not found in $ROOT" >&2
  exit 1
fi

# --- .env ---
if [[ ! -f .env ]]; then
  if [[ ! -f .env.example ]]; then
    echo "Error: .env.example missing; cannot create .env" >&2
    exit 1
  fi
  cp .env.example .env
  echo "Created .env from .env.example"
else
  echo "Using existing .env"
fi

if ! grep -qE '^OPENROUTER_API_KEY=.+' .env 2>/dev/null || grep -qE '^OPENROUTER_API_KEY=\s*$' .env 2>/dev/null; then
  echo ""
  echo "NOTE: OPENROUTER_API_KEY is empty in .env."
  echo "      Login / catalog / orders work without it."
  echo "      AI Support needs a key — add it, then: docker compose -f $COMPOSE_FILE restart backend"
  echo ""
fi

# --- optional wipe ---
if [[ "$RESET" -eq 1 ]]; then
  echo "Resetting volumes (fresh MySQL + deterministic seed)…"
  docker compose -f "$COMPOSE_FILE" down -v
fi

UP_ARGS=(-f "$COMPOSE_FILE" up)
if [[ "$NO_BUILD" -eq 0 ]]; then
  UP_ARGS+=(--build)
fi

print_credentials

if [[ "$FOREGROUND" -eq 1 ]]; then
  echo "Starting stack in foreground (migrations + seed run on backend boot)…"
  echo "Tip: Ctrl+C stops containers."
  exec docker compose "${UP_ARGS[@]}"
fi

echo "Starting stack in background…"
docker compose "${UP_ARGS[@]}" -d

wait_for_api() {
  local max_attempts="${1:-90}"
  local i=1
  echo "Waiting for API health at http://localhost:8000/health …"
  while [[ $i -le $max_attempts ]]; do
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
      echo "API is healthy."
      return 0
    fi
    sleep 2
    i=$((i + 1))
  done
  echo "Warning: API did not become healthy in time." >&2
  echo "  Check: docker compose -f $COMPOSE_FILE logs backend" >&2
  return 1
}

wait_for_api || true

# Static vector RAG (Chroma under backend/knowledge/chroma/). Needs an embedding API key.
has_embed_key=0
if grep -qE '^(OPENROUTER_API_KEY|OPENAI_API_KEY)=.+' .env 2>/dev/null \
  && ! grep -qE '^(OPENROUTER_API_KEY|OPENAI_API_KEY)=\s*$' .env 2>/dev/null; then
  # Treat as present if either key line has a non-empty value
  if grep -qE '^OPENROUTER_API_KEY=[^[:space:]]+' .env 2>/dev/null \
    || grep -qE '^OPENAI_API_KEY=[^[:space:]]+' .env 2>/dev/null; then
    has_embed_key=1
  fi
fi

echo ""
echo "Building vector RAG index (Chroma)…"
if [[ "$has_embed_key" -eq 0 ]]; then
  echo "Skipped: no OPENROUTER_API_KEY / OPENAI_API_KEY in .env."
  echo "  App still runs with keyword RAG fallback (RAG_MODE=auto)."
  echo "  After adding a key: docker compose -f $COMPOSE_FILE exec backend python -m scripts.build_knowledge_index --force"
else
  if docker compose -f "$COMPOSE_FILE" exec -T backend \
    python -m scripts.build_knowledge_index --force >/tmp/hds-rag-build.log 2>&1; then
    echo "Vector DB ready: backend/knowledge/chroma/ (static batch index)."
  else
    echo "Vector index build FAILED — keyword RAG fallback still works."
    echo "  Log: /tmp/hds-rag-build.log"
    tail -20 /tmp/hds-rag-build.log 2>/dev/null || true
  fi
fi

echo ""
echo "======== Harbor Dock Station ready ========"
echo "Frontend:   http://localhost:3000"
echo "API:        http://localhost:8000"
echo "AI Support: http://localhost:3000/support/ai"
echo ""
echo "Backend seed lines:"
docker compose -f "$COMPOSE_FILE" logs backend 2>/dev/null \
  | grep -E 'Seed complete|Ava North|OP-10|already seeded|Admin:|Customer:' \
  | tail -40 || true
print_credentials
echo "Stop later: docker compose -f $COMPOSE_FILE down"
echo "Fresh seed: ./setup-docker.sh --reset"
echo "==========================================="
