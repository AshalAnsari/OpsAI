# OpsPilot Refund Policy

> OpsPilot is a fictional operational commerce demo. This policy describes how refunds relate to platform payment and order states.

**Last updated:** September 6, 2026

---

## Overview

OpsPilot charges through **Stripe Checkout** (sandbox / test mode) or a **local demo checkout** when Stripe keys are placeholders. Payment confirmation is always event-driven via webhooks — the frontend alone cannot mark an order as paid.

Supported payment statuses:

| Status | Meaning |
| --- | --- |
| `unpaid` / `pending` | Checkout not completed |
| `paid` | Payment confirmed |
| `failed` | Checkout expired, declined, or abandoned |
| `refunded` | Reserved status for completed refunds |

## When money was never captured

No refund is needed if:

- Stripe Checkout was cancelled or declined
- The checkout session expired
- You abandoned unpaid checkout

In those cases the order is cancelled, payment is `failed`, and stock is restored. Nothing was successfully charged for a completed order.

## When a paid order is cancelled before dispatch

If a **paid** order is cancelled while still at the warehouse (`pending`, `confirmed`, or `processing`):

- The order becomes `cancelled`
- Stock is restored
- Fulfillment stops

Automated Stripe refund issuance is **not** performed by the order cancel endpoint today. For paid cancellations, open a **Support** ticket so operations can process a refund and mark payment as `refunded` when applicable.

## After the order has shipped

Once status is `dispatched` or later, self-service cancel is unavailable. Refund or return requests must go through **Support**. Typical demo guidance:

| Situation | Guidance |
| --- | --- |
| Wrong / damaged item | Open a support ticket with order ID (`OP-#####`) and details |
| Never delivered | Contact support after checking the order timeline / location |
| Changed mind after dispatch | Not eligible for self-service cancel; support reviews case-by-case |

## Demo / sandbox notes

- With `sk_test_placeholder`, demo checkout simulates payment success; no real card is charged.
- With real Stripe **test** keys, use Stripe test cards only. Do not use live keys or real personal payment data.
- Refund timelines in a real Stripe Dashboard may differ from this fictional policy.

## How to request a refund

1. Sign in to your customer account.
2. Open **Support** and create a ticket.
3. Include your order display ID (for example `OP-10042`), reason, and any photos if relevant.
4. Ops staff will reply in the ticket thread (and may email when SMTP is configured).

## Related policies

- [Cancellation Policy](./cancellation_policy.md)
- [Payment FAQ](./payment_faq.md)
