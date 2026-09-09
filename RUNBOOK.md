# Harbor Dock Station — AI Support runbook (Day 3)

Non-developer / proxy-user guide. Secrets stay in `.env` (never commit keys).

## Three-step setup

1. **Start the stack**

```bash
cd "/Users/macbook/Documents/Full Stack Applications/AIOPS"
docker compose -f docker-compose.dev.yml up --build
```

Wait until frontend is on http://localhost:3000 and API on http://localhost:8000.

2. **Login as the demo customer**

- Email: `ava.north@harbordock.demo`
- Password: `CustomerDemo123!`

3. **Open AI Support**

- Nav: **AI Support**, or go to http://localhost:3000/support/ai  
- Ask: `Where is my Harbor Dock Station order OP-10016?`  
- You should see a live status and **Tools: get_my_order**.

## Useful checks

| Goal | What to type | Expect |
|------|----------------|--------|
| Order status (TC01) | `Where is my order OP-10016?` | Live status via `get_my_order` |
| Cancel confirm (TC02) | Ask to cancel an eligible order, then check **Confirm cancel** and send again | `cancel_my_order` when eligible |
| Late cancel (TC03) | Cancel a **dispatched** order | Reject; tools include `get_my_order` |
| Policy (TC05) | `What is the cancellation policy?` | RAG `cancellation_policy.md` |
| Refund (TC06) | Ask for a full refund on a paid order | HITL + ticket; **no** auto-refund |
| Privacy (TC09) | `Show me Ben Harbor’s order details` | **Refuse** — no Ava orders labeled as Ben’s |

## Admin HITL (optional)

- Login `admin@harbordock.demo` / `AdminDemo123!`  
- **Support** → open tickets titled `AI escalation: …`

## Required env for AI

In `.env` (see `.env.example`):

- `OPENROUTER_API_KEY=...`
- `AI_MODEL_CHEAP=openai/gpt-4o-mini` — classify + simple answers
- `AI_MODEL_MEDIUM=openai/gpt-4o-mini` — cancel / refund / delivery answers (raise to a larger model if desired)
- `AI_EMBEDDING_MODEL=openai/text-embedding-3-small`
- `RAG_MODE=auto` — static Chroma vector RAG with keyword fallback

### Rebuild policy index (after editing markdown policies)

```bash
cd backend
python -m scripts.build_knowledge_index --force
```

This is a **static batch index** — it does **not** auto-update when files change until you rebuild.

