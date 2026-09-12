# AI Collaboration Note — Harbor Dock Station AI OS Mini

**Sprint:** 5-Day Remote AI OS Sprint  
**Candidate:** Muhammad Ashal Ansari 
**Date:** 11th September 2026  

---

## 1. AI tools used and role of each

| Tool | Role |
|------|------|
| **Cursor (Composer / Agent)** | Pair-programming for LangGraph AI layer, guardrails, RAG upgrade, evaluation docs |
| **OpenRouter-hosted chat models** (e.g. `openai/gpt-4o-mini` via app config) | Runtime classify + answer models inside the AI OS; cheap/medium routing |
| **OpenRouter / OpenAI embeddings** | Build static Chroma policy index |
| **GPT 5.6 LUNA** (browser chat) | Day 1 **Pure LLM baseline only** — no OpsPilot/HDS tools or policy paste |
| **AI Roadmap notebooks** (personal prior work) | Style reference for LangGraph StateGraph, structured classify, tool calling — not copied as production code |

---

## 2. Work delegated to AI

- Scaffolding LangGraph graph, tool wrappers over existing FastAPI services  
- Keyword → static vector RAG migration and index build script  
- Guardrail helpers (cross-customer, confirm cancel, ambiguous cancel)  
- Frontend `/support/ai` UX copy and confirm-cancel behavior  
- Drafting DAY*.md, evaluation reports from tester notes, case study structure  

---

## 3. How AI-generated results were verified

- Ran TC01–TC10 and Day 4 break cases in the live UI as Ava / Admin  
- Compared outputs to `evaluation/test_case.txt` expected bullets (also browsable at `/evaluation/cases` for admins)  
- Unit tests for guards / parsing / model-tier routing (`backend/tests/test_ai_guards.py`)  
- Confirmed RBAC: tools use customer JWT; cross-customer asks refuse  
- Confirmed refunds open tickets and never claim Stripe success  
- Checked admin ticket list for AI escalation subjects  

---

## 4. Important results rejected or manually corrected

- **Rejected** treating Pure LLM “helpful” inventing as success — scored **1/10** honestly  
- **Rejected** Day 2 TC09 reply that listed Ava’s orders as Ben’s — marked FAIL; required deterministic guard, not prompt-only trust  
- **Corrected** cancel flow: eligible cancel must confirm then API-cancel — not open a ticket by default  
- **Corrected** ORDER_CHANGE over-escalation (ticket/HITL on every address change)  
- **Corrected** BR04: do not apply last-order hint on ambiguous `cancel it`  
- **Rejected** continuous/streaming RAG for five static policies — chose **static batch index** instead  

---

## 5. Core decisions personally owned

1. Problem choice: recurring support ops on Harbor Dock Station (synthetic but realistic).  
2. Success metrics and non-goals (no auto Stripe refund; no email channel).  
3. Evaluation design: Manual vs Pure LLM vs AI OS; 10 cases + Day 4 breaks.  
4. Safety boundary: HITL/tickets for refund and delivery; privacy refuse for other customers.  
5. Architecture boundary: LLM → tools → FastAPI → MySQL (never direct DB).  
6. Day 4 cost strategy: cheap vs medium model by intent; static vector RAG with keyword fallback.  
7. Honest scoring of partials/failures (Day 2 TC09, Day 4 BR04) instead of demo-only happy paths.  

---

## 6. Note for graders

Runtime AI answers are produced by configured OpenRouter models with tools and RAG. Baseline Pure LLM answers were produced separately in GPT 5.6 LUNA without system access. Human judgment owned problem framing, pass/fail scoring, and all safety non-goals.
