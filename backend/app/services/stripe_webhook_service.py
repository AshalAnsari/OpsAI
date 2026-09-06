"""
Stripe Webhook Service

Separated from order placement so payment confirmation is event-driven.
OpsPilot never trusts the frontend alone to mark an order as paid.

Handled events:
- checkout.session.completed  → mark paid + confirm order
- checkout.session.expired    → cancel unpaid order + restore stock
- payment_intent.payment_failed → cancel unpaid order + restore stock
"""

from typing import Any

import stripe
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.order import Order, OrderStatus, PaymentStatus
from app.repositories.audit_repository import AuditRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.services.fulfillment_service import apply_status_side_effects
from app.services.notification_service import NotificationService
from app.utils.exceptions import AppError

settings = get_settings()
stripe.api_key = settings.stripe_secret_key


class StripeWebhookService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.orders = OrderRepository(db)
        self.products = ProductRepository(db)
        self.audit = AuditRepository(db)
        self.notifications = NotificationService(db)

    def construct_event(self, payload: bytes, signature: str) -> stripe.Event:
        try:
            return stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=settings.stripe_webhook_secret,
            )
        except ValueError as exc:
            raise AppError("STRIPE_INVALID_PAYLOAD", "Invalid Stripe webhook payload.", 400) from exc
        except stripe.SignatureVerificationError as exc:
            raise AppError("STRIPE_INVALID_SIGNATURE", "Invalid Stripe webhook signature.", 400) from exc

    def handle_event(self, event: stripe.Event) -> dict[str, Any]:
        event_type = event["type"]
        data_object = event["data"]["object"]

        if event_type == "checkout.session.completed":
            return self._on_checkout_completed(data_object)
        if event_type == "checkout.session.expired":
            return self._on_checkout_expired(data_object)
        if event_type == "payment_intent.payment_failed":
            return self._on_payment_failed(data_object)

        return {"handled": False, "event_type": event_type}

    def _on_checkout_completed(self, session: dict[str, Any]) -> dict[str, Any]:
        order = self._find_order_from_session(session)
        if not order:
            raise AppError("ORDER_NOT_FOUND", "No order found for Stripe checkout session.", 404)

        if order.payment_status == PaymentStatus.PAID:
            return {"handled": True, "duplicate": True, "order_id": order.id}

        if order.status == OrderStatus.CANCELLED:
            raise AppError(
                "ORDER_ALREADY_CANCELLED",
                "Cannot mark a cancelled order as paid.",
                409,
            )

        order.payment_status = PaymentStatus.PAID
        order.stripe_payment_intent_id = session.get("payment_intent")
        if order.status == OrderStatus.PENDING:
            apply_status_side_effects(order, OrderStatus.CONFIRMED)

        self.orders.update(order)
        self.audit.create(
            user_id=order.customer_id,
            action="order.payment_completed",
            entity_type="order",
            entity_id=str(order.id),
            metadata={
                "stripe_session_id": session.get("id"),
                "payment_intent": session.get("payment_intent"),
                "amount_total": session.get("amount_total"),
            },
        )
        self.notifications.notify(
            user_id=order.customer_id,
            title="Payment confirmed",
            body=f"Payment for {order.display_id} was successful. Your order is confirmed.",
            link=f"/orders/{order.id}",
        )
        self.db.commit()
        return {"handled": True, "order_id": order.id, "status": order.status.value}

    def _on_checkout_expired(self, session: dict[str, Any]) -> dict[str, Any]:
        order = self._find_order_from_session(session)
        if not order:
            return {"handled": False, "reason": "order_not_found"}
        return self._fail_unpaid_order(order, reason="checkout_expired", session_id=session.get("id"))

    def _on_payment_failed(self, payment_intent: dict[str, Any]) -> dict[str, Any]:
        metadata = payment_intent.get("metadata") or {}
        order_id = metadata.get("order_id")
        order = None
        if order_id:
            order = self.orders.get_by_id(int(order_id))
        if not order:
            return {"handled": False, "reason": "order_not_found"}
        return self._fail_unpaid_order(
            order,
            reason="payment_declined",
            payment_intent=payment_intent.get("id"),
        )

    def _fail_unpaid_order(
        self,
        order: Order,
        *,
        reason: str,
        session_id: str | None = None,
        payment_intent: str | None = None,
    ) -> dict[str, Any]:
        if order.payment_status == PaymentStatus.PAID:
            return {"handled": True, "skipped": True, "order_id": order.id}

        if order.status != OrderStatus.CANCELLED:
            for item in order.items:
                product = self.products.get_for_update(item.product_id)
                if product:
                    product.stock_quantity += item.quantity
                    self.products.update(product)
            previous = order.status
            apply_status_side_effects(order, OrderStatus.CANCELLED)
        else:
            previous = order.status

        order.payment_status = PaymentStatus.FAILED
        self.orders.update(order)
        self.audit.create(
            user_id=order.customer_id,
            action=f"order.{reason}",
            entity_type="order",
            entity_id=str(order.id),
            metadata={
                "previous_status": previous.value,
                "stripe_session_id": session_id,
                "payment_intent": payment_intent,
            },
        )
        self.notifications.notify(
            user_id=order.customer_id,
            title="Checkout did not complete",
            body=(
                f"Payment for {order.display_id} was cancelled or declined. "
                "The order was not placed and stock has been released."
            ),
            link=f"/orders/{order.id}",
        )
        self.db.commit()
        return {"handled": True, "order_id": order.id, "status": "cancelled", "reason": reason}

    def _find_order_from_session(self, session: dict[str, Any]) -> Order | None:
        session_id = session.get("id")
        order = self.orders.get_by_stripe_session(session_id) if session_id else None
        if order:
            return order
        order_id = (session.get("metadata") or {}).get("order_id")
        if order_id:
            return self.orders.get_by_id(int(order_id))
        return None
