# Harbor Dock Station Cancellation Policy

> Harbor Dock Station is a fictional operational commerce demo. This policy mirrors the platform’s enforced business rules.

**Last updated:** September 6, 2026

---

## Overview

Customers may cancel an order **only while the package is still at the warehouse** — before it has been dispatched.

## When you can cancel

Cancellation is allowed when the order status is one of:

| Status | Meaning |
| --- | --- |
| `pending` | Checkout started; payment not confirmed |
| `confirmed` | Payment received; order at New York, NY, USA warehouse |
| `processing` | Warehouse is packing the order |

Self-service cancel: use **Cancel order** on the order detail page, or `POST /api/v1/orders/{id}/cancel`.

## When you cannot cancel

Cancellation is **blocked** once the order has left the warehouse:

- `dispatched`
- `in_transit_international`
- `customs_clearance`
- `out_for_delivery`
- `delivered`
- `cancelled` (already cancelled)

The API returns `ORDER_NOT_CANCELLABLE` with a message that the order has already left the warehouse.

## What happens on cancel

1. Order status becomes `cancelled`.
2. Reserved stock for each line item is restored.
3. If payment was still `pending` or `unpaid`, payment status becomes `failed`.
4. An audit event (`order.cancelled`) is recorded.
5. Fulfillment stops; the order timeline shows cancelled.

## Abandoned / declined checkout

If you leave Stripe Checkout, decline the card, or the session expires:

- The order is cancelled automatically (or via abandon checkout).
- Payment status becomes `failed`.
- Stock is released.
- The cart is not treated as a completed purchase.

Local demo mode uses a simulated webhook instead of live Stripe; the same cancel/stock rules apply.

## Admin cancellations

Operations staff may cancel an order through validated admin status transitions while the order is still in a cancellable warehouse stage (`pending`, `confirmed`, or `processing`). After `dispatched`, cancel is not a valid transition.

## Need help after dispatch?

If the package has already shipped, open a **Support** ticket. Cancellation is no longer available in-app; support can advise on next steps under the [Refund Policy](./refund_policy.md).
