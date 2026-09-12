# Harbor Dock Station — Operational SaaS Demo Platform

Harbor Dock Station is a **fictional** operational commerce SaaS: customers browse products, place demo orders, and track fulfillment; admins run catalog, orders, support, audit, and **AI evaluation** from an operations console.

The platform exposes REST APIs that an AI assistant layer can call as controlled tools — never the database directly.

All branding, customers, products, and credentials are synthetic.

## Quick start (after clone)

```bash
./setup-docker.sh
# fresh deterministic Ava orders OP-10001…OP-10005:
./setup-docker.sh --reset
```

- App: http://localhost:3000 · AI Support: http://localhost:3000/support/ai  
- Admin evaluation (baseline): http://localhost:3000/admin/evaluation *(admin login required)*  
- Admin TC & BR case list: http://localhost:3000/evaluation/cases *(admin login; direct URL only — not in admin nav)*  
- Accounts & orders: **`DEMO-ACCOUNTS.md`** · Non-dev steps: **`RUNBOOK.md`**  
- Add `OPENROUTER_API_KEY` to `.env` for AI Support (script creates `.env` from `.env.example` if missing).

---

## 1. Project overview

Customers can register, browse products, place demo orders (Stripe sandbox / local demo checkout), and track order status.

Admins can manage products, inspect customers/orders, update fulfillment status, review audit logs, and open the **AI baseline comparison** (`/admin/evaluation`) from an operations console. The full **TC01–TC10 + BR01–BR05** case list (prompts, expected behavior, observed responses) is at `/evaluation/cases` — admin login required, direct URL only (not in the admin navbar).

---

## 2. Architecture

```
Frontend (Next.js)
        ↓ REST + JWT
Backend (FastAPI Controllers)
        ↓
Services (business rules)
        ↓
Repositories (SQLAlchemy)
        ↓
MySQL

Stripe Checkout  →  Stripe Webhook Service  →  Order payment confirmation
```

Layering:

- Controllers: HTTP only
- Services: business logic, transactions, audit events
- Repositories: persistence
- Dependencies: auth + reusable RBAC

---

## 3. Tech stack

| Layer | Stack |
| --- | --- |
| Frontend | Next.js (App Router), TypeScript, Tailwind, React Hook Form, Zod |
| Backend | FastAPI, SQLAlchemy 2.x, Alembic, Pydantic Settings, JWT, bcrypt |
| Payments | Stripe Checkout (sandbox) + dedicated webhook service |
| Data | MySQL 8 |
| Runtime | Docker Compose |

---

## 4. Folder structure

```
AIOPS/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── controllers/
│   │   ├── core/
│   │   ├── dependencies/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/          # includes stripe_webhook_service.py
│   │   └── utils/
│   ├── alembic/
│   ├── scripts/seed.py
│   └── tests/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   └── lib/
├── docker-compose.yml
├── docker-compose.dev.yml
├── setup-docker.sh          # one-command clone setup + seed
├── DEMO-ACCOUNTS.md         # demo logins + Ava OP-10001…OP-10005
├── RUNBOOK.md
├── .env.example
└── README.md
```

---

## 5. Environment variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Important variables:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `FRONTEND_URL` / `CORS_ORIGINS`
- `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` / `STRIPE_WEBHOOK_SECRET`
- `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` / `SEED_CUSTOMER_PASSWORD`
- `NEXT_PUBLIC_API_URL`

If Stripe keys remain placeholders (`sk_test_placeholder`), Harbor Dock Station uses **local demo checkout** and `POST /api/v1/webhooks/stripe/demo-complete` to simulate payment success.

---

## 6. Database setup

MySQL is started by Docker Compose.

Schema is managed with Alembic migrations (not ad-hoc SQL).

---

## 7. Alembic migrations

From `backend/`:

```bash
alembic upgrade head
```

Initial migration: `alembic/versions/001_initial.py`

---

## 8. Seed data

```bash
python -m scripts.seed
```

Creates (deterministic):

- 1 admin + 8 customers
- 15 products
- Ava scenario orders **OP-10001…OP-10005** (cancel / dispatched / delivered / refund / status)
- Extra orders for other customers (privacy / catalog demos)
- audit log entries

Docker startup runs migrations + seed automatically. See `DEMO-ACCOUNTS.md`.

---

## 9. Running locally

### Option A — Docker Compose DEV (recommended now)

```bash
./setup-docker.sh
# wipe DB and reseed Ava OP-10001…OP-10005:
./setup-docker.sh --reset
```

Or manually:

```bash
cp .env.example .env
docker compose -f docker-compose.dev.yml up --build
```

`./setup-docker.sh` creates `.env` if missing, starts the stack, waits for health, builds the **Chroma vector DB** for policy RAG when `OPENROUTER_API_KEY` / `OPENAI_API_KEY` is set (otherwise keyword fallback), and prints demo accounts (`DEMO-ACCOUNTS.md`). Backend CMD already runs Alembic + deterministic seed.

This builds **`Dockerfile.dev`** for backend and frontend, starts MySQL + API + UI, and bind-mounts source for live reload.

| File | Purpose |
| --- | --- |
| `docker-compose.dev.yml` | Local development (use this now) |
| `docker-compose.yml` | Production-style deploy (later) |
| `backend/Dockerfile.dev` / `frontend/Dockerfile.dev` | Dev images |
| `backend/Dockerfile` / `frontend/Dockerfile` | Prod images |

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger: http://localhost:8000/docs

| Service | Bind mount | Reload |
| --- | --- | --- |
| `backend` | `./backend` → `/app` | Uvicorn `--reload` |
| `frontend` | `./frontend` → `/app` | Next.js `npm run dev` (HMR) |

Named volumes keep `node_modules` and `.next` inside the container. Rebuild only when dependencies change.

### Option A2 — Docker Compose PROD (later)

```bash
docker compose -f docker-compose.yml up --build -d
```

### Option B — Local processes

1. Start MySQL (or `docker compose up mysql -d`)
2. Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload --port 8000
```

3. Frontend:

```bash
cd frontend
npm install
npm run dev
```

### Backend tests

```bash
cd backend
pytest -q
```

---

## 10. Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@harbordock.demo` | `AdminDemo123!` |
| Customer | `ava.north@harbordock.demo` | `CustomerDemo123!` |

Other seeded customers use the same customer password.

---

## 10b. AI Support (Day 3 core)

LangGraph AI OS Mini for support ops: live order tools + policy RAG + HITL tickets.

- UI: http://localhost:3000/support/ai  
- API: `POST /api/v1/ai/support/chat`  
- Non-developer steps: see **`RUNBOOK.md`** (three-step setup)  
- Requires `OPENROUTER_API_KEY` in `.env` (see `.env.example`)

### Admin: evaluation UIs

**Baseline comparison** — Manual vs Pure LLM vs AI OS scores and capability matrix (from `evaluation/BASELINE-COMPARISON.md`).

- URL: http://localhost:3000/admin/evaluation  
- Access: **admin role only** (`RequireAuth` — guests go to login; customers redirect to `/dashboard`)  
- Also: admin nav **Evaluation**, or Overview → **Open baseline**  
- Login: `admin@harbordock.demo` / `AdminDemo123!` (see **`DEMO-ACCOUNTS.md`**)

**TC & BR case list** — prompts, expected bullets, observed responses, tools, and latency for TC01–TC10 and Day 4 break cases BR01–BR05 (from `evaluation/test_case.txt`, `BREAK-CASES-DAY4.md`, `results-ai-os-day4.json`).

- URL: http://localhost:3000/evaluation/cases  
- Access: **admin role only** (same as baseline)  
- **Not** in the admin navbar — type the URL, or use **Open TC & BR case list** on the baseline page  
- Source data lives in `frontend/lib/evaluation-cases.ts`

---

## 11. API documentation

Interactive OpenAPI docs: http://localhost:8000/docs

Tags:

- Authentication
- Customer
- Products
- Orders
- Admin
- Audit
- Webhooks

Consistent error shape:

```json
{
  "success": false,
  "error": {
    "code": "ORDER_NOT_CANCELLABLE",
    "message": "This order cannot be cancelled because it has already progressed past confirmation (current status: shipped)."
  }
}
```

---

## 12. RBAC explanation

Roles: `admin`, `customer` (many-to-many via `user_roles`).

Reusable dependencies:

- `get_current_user`
- `require_customer`
- `require_admin`

Authorization is enforced on the server. Frontend route guards are convenience only.

Customers cannot call admin APIs. Customers can only access their own orders (IDOR-safe 404).

---

## 13. Business rules

### Orders

1. Validate auth, products, availability, quantity
2. Snapshot `unit_price` at purchase time
3. Decrease stock in a transaction
4. Create Stripe Checkout Session (or demo checkout URL)
5. Write audit log

### Cancellation (customer)

Allowed only for `pending` and `confirmed`.

On cancel: restore stock + audit log.

### Admin status transitions

```
pending → confirmed | cancelled
confirmed → processing | cancelled
processing → shipped | cancelled
shipped → delivered
```

Arbitrary jumps are rejected.

### Stripe webhook service

Separated from order placement:

- `checkout.session.completed` → mark paid + confirm
- `checkout.session.expired` → cancel unpaid + restore stock
- `payment_intent.payment_failed` → mark payment failed

Webhook endpoint: `POST /api/v1/webhooks/stripe`

---

## 14. AI assistant architecture (planned)

The AI layer should:

- Authenticate with scoped credentials
- Call these REST endpoints as tools
- Never open a MySQL connection
- Rely on service-layer business rules + audit logs

Intended tools include: search products, get order details, cancel eligible orders, inspect audit activity, and escalate to human ops.

---

## Quality checks covered by tests

- Unauthenticated access blocked
- Customer blocked from admin APIs
- IDOR blocked on orders
- Invalid/overstock/inactive product orders rejected
- Stock decremented and restored on cancel
- Admin status transition validation
- Audit log creation

---

## License / disclaimer

Synthetic demo only. Not a real storefront. Do not use real personal data or production Stripe live keys.
