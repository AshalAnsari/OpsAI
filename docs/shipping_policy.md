# OpsPilot Shipping Policy

> OpsPilot is a fictional operational commerce demo. Shipping rules match the fulfillment engine in the product.

**Last updated:** September 6, 2026

---

## Origin warehouse

All orders ship from:

**New York, NY, USA**

Order location labels update as fulfillment advances (for example “New York, NY, USA — packing”, “Left New York, NY, USA”).

## Destination country

At checkout you must select a shipping country. The country code is stored on the order and drives the fulfillment path.

Supported destinations in the demo storefront:

| Code | Country |
| --- | --- |
| US | United States |
| CA | Canada |
| GB | United Kingdom |
| DE | Germany |
| FR | France |
| AU | Australia |
| JP | Japan |
| IN | India |
| BR | Brazil |
| MX | Mexico |

- **Domestic:** `US`
- **International:** any other selected country

## Fulfillment timelines (demo)

Paid orders advance one fulfillment step on a schedule:

- Development: about every **10 minutes**
- Production-style config: about every **60 minutes**

Only orders with `payment_status = paid` advance. Admins can force-advance for demos.

## Domestic route (United States)

```
pending → confirmed → processing → dispatched → out_for_delivery → delivered
```

## International route (non-US)

```
pending → confirmed → processing → dispatched
  → in_transit_international → customs_clearance
  → out_for_delivery → delivered
```

International orders include extra steps for transit and customs clearance before local delivery.

## Tracking

Customers can view:

- Order status timeline
- Current location string (when set)
- In-app notifications when a step advances

Order IDs are shown as `OP-#####` (for example `OP-10015`).

## Shipping fees & customs

This demo does not calculate separate shipping fees, duties, or taxes at checkout. Line totals use product unit prices (USD) snapshotted at purchase. International customs handling is simulated as a status step only.

## Delays & issues

If an order appears stuck, check the timeline and notifications first, then open a **Support** ticket with your order ID. Cancellation after dispatch is not available; see the [Cancellation Policy](./cancellation_policy.md) and [Refund Policy](./refund_policy.md).
