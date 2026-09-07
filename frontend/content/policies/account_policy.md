# Harbor Dock Station Account Policy

> Harbor Dock Station is a fictional operational commerce demo. This policy describes account registration, access, and profile rules enforced by the platform.

**Last updated:** September 6, 2026

---

## Account types

| Role | Access |
| --- | --- |
| `customer` | Browse products, cart/checkout, own orders, profile, support tickets, notifications |
| `admin` | Operations console: products, customers, orders, fulfillment, support, audit logs |

Self-registration always creates a **customer** account. Admin accounts are provisioned separately (seed / ops).

## Registration

To register you must provide:

- Valid email (unique; stored lowercased)
- First name and last name (required, non-empty)
- Password meeting strength rules

Password requirements:

- 8–128 characters
- At least one letter and one number
- Cannot be blank or whitespace-only

Duplicate emails return `EMAIL_ALREADY_REGISTERED`.

On success you receive a JWT access token and can use the storefront immediately.

## Sign-in

- Login with email + password returns a JWT bearer token.
- Invalid credentials return a generic failure (no email enumeration detail beyond invalid credentials).
- Deactivated accounts (`is_active = false`) cannot sign in (`ACCOUNT_DISABLED`).

Default token lifetime: **24 hours** (`access_token_expire_minutes`).

## Profile

Customers may view and update:

- First name
- Last name

Email and role are not self-service editable in the current product. Profile also shows order activity stats (order counts, spend summaries) for customer accounts.

## Privacy & data access

- Customers may only access **their own** orders and support tickets.
- Attempting to open another customer’s order ID returns **404** (does not reveal existence).
- Authorization is enforced on the API; frontend route guards are convenience only.
- Significant account and order actions write **audit log** entries for operations review.

## Support

Customers can open support tickets, reply in-thread, and track status (`open`, `in_progress`, `resolved`, `closed`). Staff replies may trigger in-app notifications and optional email when SMTP is configured.

## Acceptable use (demo)

Harbor Dock Station is a **synthetic portfolio demo**:

- Do not enter real personal data beyond what you need for local testing.
- Do not use production Stripe live keys.
- Seeded demo accounts and passwords are for interview / local use only.
- Treat all catalog, customers, and orders as fictional.

## Account deactivation

Inactive accounts cannot authenticate. Reactivation, password reset self-service, and account deletion flows are not exposed as customer self-service endpoints in the current phase; contact an admin or use Support for demo assistance.

## Related policies

- [Cancellation Policy](./cancellation_policy.md)
- [Refund Policy](./refund_policy.md)
- [Shipping Policy](./shipping_policy.md)
- [Payment FAQ](./payment_faq.md)
