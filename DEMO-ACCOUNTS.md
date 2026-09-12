# Harbor Dock Station — demo accounts & seeded orders

Synthetic credentials for local / grader testing. Safe to share in the repo.

## Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@harbordock.demo` | `AdminDemo123!` |
| Customer (primary) | `ava.north@harbordock.demo` | `CustomerDemo123!` |
| Customer (privacy TC09) | `ben.harbor@harbordock.demo` | `CustomerDemo123!` |

Other seeded customers (`cora.quill@…` … `hugo.lumen@…`) use the same customer password.

### Admin console URLs

| Page | URL | In admin nav? |
|------|-----|---------------|
| Overview | http://localhost:3000/admin | Yes |
| Support tickets (HITL) | http://localhost:3000/admin/support | Yes |
| **AI evaluation baseline** | http://localhost:3000/admin/evaluation | Yes (**Evaluation**) |
| **TC & BR case list** | http://localhost:3000/evaluation/cases | **No** — direct URL only |

Both evaluation pages are **admin-only** (login required). Customers and guests cannot open them. From the baseline page you can also open **Open TC & BR case list**.

## Ava North orders (fresh database)

Created by `python -m scripts.seed` on first backend boot (or after `./setup-docker.sh --reset`):

| Display ID | Status | Payment | Use for |
|------------|--------|---------|---------|
| **OP-10001** | pending | pending | Cancel (confirm) · “why is payment pending?” |
| **OP-10002** | dispatched | paid | Late cancel · address change |
| **OP-10003** | delivered | paid | Missing package / escalate |
| **OP-10004** | confirmed | paid | Refund (HITL ticket, no auto-refund) |
| **OP-10005** | out_for_delivery | paid | “Where is my order?” |

Order display format: `OP-{10000 + id}`.

## Quick start

```bash
./setup-docker.sh
# wipe DB and reseed Ava OP-10001…OP-10005:
./setup-docker.sh --reset
```

`./setup-docker.sh` also builds the **static Chroma vector RAG** index (`backend/knowledge/chroma/`) when `OPENROUTER_API_KEY` or `OPENAI_API_KEY` is set in `.env`. Without a key, policy answers fall back to keyword RAG.

Then open http://localhost:3000/support/ai as Ava.

## Stripe (optional local checkout)

If you exercise checkout UI (not required for AI Support):

- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`

Placeholder Stripe keys in `.env` use **local demo checkout** instead of live Stripe.
