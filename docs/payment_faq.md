# Harbor Dock Station Payment FAQ

> Harbor Dock Station is a fictional operational commerce demo. Answers reflect how checkout and webhooks work in this project.

**Last updated:** September 6, 2026

---

## How do I pay?

1. Add products to your cart (signed-in customer).
2. Choose a shipping country.
3. Place the order.
4. Complete payment via **Stripe Checkout**, or via **local demo checkout** when Stripe keys are still placeholders.

Orders start as unpaid reservations. Stock is held until payment succeeds or the checkout fails/expires/is abandoned.

## What currency is used?

Payments use **USD** (`stripe_currency` defaults to `usd`). Amounts in the UI are formatted as US dollars.

## When is my order considered paid?

Only after a trusted payment event:

| Event | Result |
| --- | --- |
| `checkout.session.completed` | Payment → `paid`, order → `confirmed` (from `pending`) |
| Demo complete webhook (local only) | Same as successful checkout |

The frontend success page alone does **not** mark an order paid.

## What if I cancel or leave Stripe Checkout?

- Cancel / decline / session expiry → order cancelled, payment `failed`, stock restored.
- You may also abandon unpaid checkout from the app after a cancel redirect.

## What payment statuses exist?

| Status | Meaning |
| --- | --- |
| `unpaid` | Not paid |
| `pending` | Checkout in progress / awaiting confirmation |
| `paid` | Payment confirmed |
| `failed` | Declined, expired, or abandoned |
| `refunded` | Refund completed (support/ops process) |

## Demo mode vs Stripe test mode

| Mode | When | Behavior |
| --- | --- | --- |
| Local demo | `STRIPE_SECRET_KEY` starts with `sk_test_placeholder` | Checkout URL points back to the order page; `POST /api/v1/webhooks/stripe/demo-complete` simulates success |
| Stripe sandbox | Real `sk_test_…` / `pk_test_…` keys | Redirect to Stripe Checkout; webhooks to `POST /api/v1/webhooks/stripe` |

Never use live Stripe keys or real personal card data with this demo.

## Why was my payment marked failed?

Common causes:

- Checkout session expired
- Card declined (`payment_intent.payment_failed`)
- You cancelled Stripe Checkout
- You abandoned an unpaid order in the app

## Can I retry payment on the same order?

Failed or cancelled unpaid orders are closed. Place a new order from the cart if you still want the items (stock must be available).

## Are my card details stored by Harbor Dock Station?

No. Card entry happens on Stripe Checkout (when configured). Harbor Dock Station stores Stripe session / payment intent IDs on the order for correlation, not full card numbers.

## How do refunds work?

See the [Refund Policy](./refund_policy.md). Paid cancellations before dispatch restore stock; refund processing for paid orders is handled through Support.

## Who can see my orders?

Only you (the owning customer) and Harbor Dock Station admins. Other customers receive a generic “not found” response for your order IDs (IDOR-safe).
