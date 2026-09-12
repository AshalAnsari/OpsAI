# Case Study — Harbor Dock Station AI OS Mini

**Sprint:** 5-Day Remote AI OS Sprint  
**Domain:** Customer support / operations  
**Product:** Harbor Dock Station (fictional operational commerce SaaS; synthetic data)  
**Date:** September 2026  

---

## 1. User and problem

**Primary user:** Support operator / admin (proxy: `admin@harbordock.demo`) handling recurring customer requests about orders, payments, cancellations, refunds, delivery issues, and policies.

**Secondary user:** Customer (proxy: `ava.north@harbordock.demo`) who asks those questions in chat.

**Job-to-be-done:** Resolve routine support intents correctly using **live order state** and **company policy**, without hunting multiple screens or inventing answers — while keeping humans in the loop for money and exceptions.

**Bottleneck:** Looking up orders, payment status, fulfillment rules, and policies is repetitive; risky actions (refunds, missing packages) need judgment that must not be auto-executed by a model.

**Assumptions:** Real production tenants were not available; Harbor Dock Station is a synthetic but realistic mirror of e-commerce support ops so the workflow is measurable.

---

## 2. Existing workflow and bottleneck

| Stage | Manual process |
|-------|----------------|
| Trigger | Customer ask (UI / ticket) |
| Input | Order id, identity, free text |
| Judgment | Cancel allowed? Paid vs pending? Other customer? In policy? |
| Tools | Orders UI/API, policies, admin tickets, Stripe (out of band) |
| Approval | Self-serve cancel when warehouse-stage; tickets for refund/delivery |
| Pain | Context switching; policy alignment **10 min–1 hour**; refunds up to **~48 hours** |

**Baselines (Day 1):**

- Manual through the product: correct but slow on judgment paths (`evaluation/manual-ui-scoresheet.md`).
- Pure LLM (GPT 5.6 LUNA, no tools): **1 / 10** — blind or ungrounded (`evaluation/PURE-LLM-BASELINE.md`).

---

## 3. Scope decisions and non-goals

**In scope (v1):** AI Support chat; LangGraph workflow; FastAPI tools for orders/tickets; static vector RAG over five policies; cheap/medium model routing; guardrails (privacy, confirm cancel, injection sniff); HITL via support tickets for refunds/delivery.

**Non-goals:** Email/Slack channels; auto Stripe refunds; continuous/streaming RAG; multi-tenant productization; replacing the admin console; direct LLM→MySQL.

---

## 4. Architecture and major trade-offs

```
Ava → /support/ai → POST /api/v1/ai/support/chat (JWT)
     → LangGraph: classify → tools → [ticket?] → answer
          ├─ Tools → FastAPI → MySQL
          ├─ Static Chroma RAG (batch rebuild)
          └─ Deterministic guards
     → Cheap model (simple) / Medium model (complex)
```

| Trade-off | Choice | Why |
|-----------|--------|-----|
| Agent style | Controlled LangGraph, not fully free agent | Evaluable, safer |
| Live data | Tools → API, not DB | Reuse RBAC/business rules |
| Policies | Static batch-indexed vector RAG + keyword fallback | Small stable corpus; not CDC |
| Cost | Cheap vs medium by intent | Day 4 cost control |
| Refunds | Ticket + human approval flag | Never auto money movement |

---

## 5. Work delegated to AI vs retained by humans

| AI / system | Humans |
|-------------|--------|
| Order/payment status | Refund approval / Stripe money movement |
| Policy summaries (RAG) | Ambiguous fraud / goodwill exceptions |
| Eligible cancel after confirm | Missing-package investigation |
| Refuse cross-customer access | Final ops judgment on escalations |
| Open escalation tickets | Admin reply/resolve in `/admin/support` |

---

## 6. Failures, changes, results

| Finding | Change | Outcome |
|---------|--------|---------|
| Day 2 TC09: Ava’s orders labeled as Ben’s | Deterministic unauthorized guard | Day 3/4: PASS (~12 ms) |
| Day 2 TC02: confirm loop, no cancel | Checkbox + confirm language + hint | Day 3/4: PASS |
| Day 2 TC03/TC08: weak routing / over-ticket | Order-first cancel; address-change no auto-ticket | PASS |
| Day 4 BR04: `cancel it` used last order | Ignore hint on ambiguous cancel (Day 5 harden) | Fix shipped; re-test recommended |

**Headline results:**

| System | TC01–TC10 |
|--------|-----------|
| Pure LLM | **1 / 10** |
| AI OS Day 2 | **6 / 10** |
| AI OS Day 3–4 | **10 / 10** |
| Day 4 breaks | **4 PASS / 1 PARTIAL** (BR04 before harden) |

See `evaluation/BASELINE-COMPARISON.md` and `evaluation/FAILURE-RCA.md`.

---

## 7. Limitations

- Policy index is **static** — rebuild after doc edits (`python -m scripts.build_knowledge_index --force`).
- No long-term multi-turn memory (confirm uses checkbox / short phrases).
- Cancel ≠ refund; paid-charge edge cases still need HITL (documented).
- Synthetic demo data; adoption metrics below are a **plan**, not live production telemetry.

---

## 8. First two weeks after deployment (plan)

**Assumptions:** Demo / internal pilot with proxy users; measure in eval sheet + ticket counts.

| Metric | Target |
|--------|--------|
| Weekly smoke of TC01–TC10 | ≥ 9 / 10 |
| Cross-customer leaks | **0** |
| Auto-refunds | **0** |
| Median AI latency (status/policy) | Track vs Day 4 baselines |
| AI-created tickets reviewed by admin | 100% within SLA you choose |

**Instrumentation (lightweight):** log `trace_id`, intent, tools, latency (already); weekly copy into a simple spreadsheet.

---

## 9. Next iteration plan (two weeks)

1. Confirm BR04 fix with a fresh-chat `cancel it` re-test.  
2. If `payment_status=paid` on cancel → also open refund escalation ticket.  
3. Admin Approve/Reject HITL UI (beyond ticket-only).  
4. Smoke cost report: cheap vs medium token usage.  
5. Only consider continuous RAG if policies change frequently.

---

## 10. How to run (handoff)

See **`RUNBOOK.md`** (three steps), **`./setup-docker.sh`**, and **`DEMO-ACCOUNTS.md`**.  
AI Support: http://localhost:3000/support/ai after `./setup-docker.sh` (use `--reset` for fresh Ava orders OP-10001…OP-10005).  
Admin baseline UI: http://localhost:3000/admin/evaluation (login `admin@harbordock.demo` — mirrors `evaluation/BASELINE-COMPARISON.md`).  
TC & BR case list (direct URL, not in admin nav): http://localhost:3000/evaluation/cases — prompts, expected behavior, and Day 4 observed responses for TC01–TC10 and BR01–BR05.
