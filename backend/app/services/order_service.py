from decimal import Decimal

import stripe
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.order_item import OrderItem
from app.models.role import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.order import (
    OrderCreateRequest,
    OrderCreateResponse,
    OrderItemResponse,
    OrderResponse,
)
from app.services.fulfillment_service import (
    ALLOWED_STATUS_TRANSITIONS,
    CANCELLABLE_STATUSES,
    apply_status_side_effects,
)
from app.utils.exceptions import AppError
from app.utils.pagination import PaginatedResponse, PaginationParams

settings = get_settings()
stripe.api_key = settings.stripe_secret_key

# Re-export for admin / tests that import from order_service.
__all__ = [
    "ALLOWED_STATUS_TRANSITIONS",
    "CANCELLABLE_STATUSES",
    "OrderService",
]


class OrderService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.orders = OrderRepository(db)
        self.products = ProductRepository(db)
        self.audit = AuditRepository(db)

    def create_order(self, customer: User, payload: OrderCreateRequest) -> OrderCreateResponse:
        if not payload.items:
            raise AppError("EMPTY_ORDER", "Order must contain at least one item.", 400)

        # Collapse duplicate product lines
        merged: dict[int, int] = {}
        for item in payload.items:
            if item.quantity <= 0:
                raise AppError("INVALID_QUANTITY", "Quantity must be greater than zero.", 400)
            merged[item.product_id] = merged.get(item.product_id, 0) + item.quantity

        line_items: list[OrderItem] = []
        total = Decimal("0.00")
        product_snapshot: list[dict] = []

        try:
            for product_id, quantity in merged.items():
                product = self.products.get_for_update(product_id)
                if not product or not product.is_active:
                    raise AppError(
                        "PRODUCT_UNAVAILABLE",
                        f"Product {product_id} is unavailable.",
                        400,
                    )
                if product.stock_quantity < quantity:
                    raise AppError(
                        "INSUFFICIENT_STOCK",
                        f"Not enough stock for '{product.name}'. Available: {product.stock_quantity}.",
                        400,
                    )

                unit_price = Decimal(product.price)
                subtotal = unit_price * quantity
                total += subtotal
                product.stock_quantity -= quantity
                self.products.update(product)

                line_items.append(
                    OrderItem(
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=unit_price,
                        subtotal=subtotal,
                    )
                )
                product_snapshot.append(
                    {
                        "product_id": product.id,
                        "name": product.name,
                        "quantity": quantity,
                        "unit_price": str(unit_price),
                    }
                )

            order = Order(
                customer_id=customer.id,
                status=OrderStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                total_amount=total,
                shipping_country=payload.shipping_country,
                shipping_country_name=payload.shipping_country_name,
                current_location=None,
                items=line_items,
            )
            self.orders.create(order)
            self.db.flush()

            checkout_url = self._create_stripe_checkout(order, product_snapshot, customer.email)
            self.orders.update(order)

            self.audit.create(
                user_id=customer.id,
                action="order.created",
                entity_type="order",
                entity_id=str(order.id),
                metadata={
                    "total_amount": str(total),
                    "item_count": len(line_items),
                    "payment_status": order.payment_status.value,
                    "shipping_country": order.shipping_country,
                },
            )
            self.db.commit()
        except AppError:
            self.db.rollback()
            raise
        except Exception as exc:
            self.db.rollback()
            raise AppError("ORDER_CREATE_FAILED", "Unable to create order. Please try again.", 500) from exc

        refreshed = self.orders.get_by_id(order.id)
        assert refreshed is not None
        return OrderCreateResponse(
            order=self._to_response(refreshed, checkout_url=checkout_url),
            checkout_url=checkout_url,
            message=(
                "Checkout started. Your order is reserved as unpaid until Stripe confirms payment. "
                "Cancelled or declined checkouts will not keep the order active."
            ),
        )

    def _create_stripe_checkout(self, order: Order, products: list[dict], customer_email: str) -> str:
        """Create a Stripe Checkout Session in sandbox/test mode.

        When STRIPE_SECRET_KEY is still a placeholder, Harbor Dock Station uses a local demo
        checkout URL so the platform can be exercised without real Stripe credentials.
        """
        if settings.stripe_secret_key.startswith("sk_test_placeholder"):
            session_id = f"cs_test_demo_{order.id}"
            order.stripe_checkout_session_id = session_id
            return (
                f"{settings.frontend_url}/orders/{order.id}"
                f"?payment=demo&session_id={session_id}"
            )

        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                customer_email=customer_email,
                success_url=f"{settings.frontend_url}/orders/{order.id}?payment=success",
                cancel_url=f"{settings.frontend_url}/orders/{order.id}?payment=cancelled",
                line_items=[
                    {
                        "price_data": {
                            "currency": settings.stripe_currency,
                            "unit_amount": int(Decimal(p["unit_price"]) * 100),
                            "product_data": {"name": p["name"]},
                        },
                        "quantity": p["quantity"],
                    }
                    for p in products
                ],
                metadata={
                    "order_id": str(order.id),
                    "display_id": order.display_id,
                    "customer_id": str(order.customer_id),
                    "shipping_country": order.shipping_country,
                },
                payment_intent_data={
                    "metadata": {
                        "order_id": str(order.id),
                        "display_id": order.display_id,
                    }
                },
            )
        except stripe.StripeError as exc:
            raise AppError(
                "STRIPE_CHECKOUT_FAILED",
                f"Unable to create Stripe checkout session: {exc.user_message or str(exc)}",
                502,
            ) from exc

        order.stripe_checkout_session_id = session.id
        return session.url or ""

    def list_customer_orders(
        self,
        customer: User,
        pagination: PaginationParams,
        status: OrderStatus | None = None,
    ) -> PaginatedResponse[OrderResponse]:
        items, total = self.orders.list_for_customer(
            customer.id,
            offset=pagination.offset,
            limit=pagination.page_size,
            status=status,
        )
        return PaginatedResponse.create(
            [self._to_response(o) for o in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    def get_customer_order(self, customer: User, order_id: int) -> OrderResponse:
        order = self.orders.get_by_id(order_id)
        if not order or order.customer_id != customer.id:
            # Prevent IDOR: do not reveal whether the order exists for another customer.
            raise AppError("ORDER_NOT_FOUND", "Order not found.", 404)
        return self._to_response(order)

    def cancel_customer_order(self, customer: User, order_id: int) -> OrderResponse:
        order = self.orders.get_by_id(order_id)
        if not order or order.customer_id != customer.id:
            raise AppError("ORDER_NOT_FOUND", "Order not found.", 404)

        if order.status not in CANCELLABLE_STATUSES:
            raise AppError(
                "ORDER_NOT_CANCELLABLE",
                "This order cannot be cancelled because it has already left the warehouse "
                f"(current status: {order.status.value}).",
                400,
            )

        self._restore_stock(order)
        previous = order.status
        apply_status_side_effects(order, OrderStatus.CANCELLED)
        if order.payment_status in {PaymentStatus.PENDING, PaymentStatus.UNPAID}:
            order.payment_status = PaymentStatus.FAILED
        self.orders.update(order)
        self.audit.create(
            user_id=customer.id,
            action="order.cancelled",
            entity_type="order",
            entity_id=str(order.id),
            metadata={"previous_status": previous.value, "cancelled_by": "customer"},
        )
        self.db.commit()
        refreshed = self.orders.get_by_id(order.id)
        assert refreshed is not None
        return self._to_response(refreshed)

    def abandon_unpaid_checkout(self, customer: User, order_id: int) -> OrderResponse:
        """Cancel an unpaid checkout after Stripe cancel/decline redirect."""
        order = self.orders.get_by_id(order_id)
        if not order or order.customer_id != customer.id:
            raise AppError("ORDER_NOT_FOUND", "Order not found.", 404)

        if order.payment_status == PaymentStatus.PAID:
            raise AppError(
                "ORDER_ALREADY_PAID",
                "This order is already paid and cannot be abandoned.",
                400,
            )
        if order.status == OrderStatus.CANCELLED:
            return self._to_response(order)

        if order.status not in CANCELLABLE_STATUSES:
            raise AppError(
                "ORDER_NOT_CANCELLABLE",
                "This order can no longer be abandoned.",
                400,
            )

        self._restore_stock(order)
        apply_status_side_effects(order, OrderStatus.CANCELLED)
        order.payment_status = PaymentStatus.FAILED
        self.orders.update(order)
        self.audit.create(
            user_id=customer.id,
            action="order.checkout_abandoned",
            entity_type="order",
            entity_id=str(order.id),
            metadata={"source": "frontend_cancel_redirect"},
        )
        self.db.commit()
        refreshed = self.orders.get_by_id(order.id)
        assert refreshed is not None
        return self._to_response(refreshed)

    def _restore_stock(self, order: Order) -> None:
        for item in order.items:
            product = self.products.get_for_update(item.product_id)
            if product:
                product.stock_quantity += item.quantity
                self.products.update(product)

    def _to_response(self, order: Order, checkout_url: str | None = None) -> OrderResponse:
        items = [
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name if item.product else None,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
            )
            for item in order.items
        ]
        return OrderResponse(
            id=order.id,
            display_id=order.display_id,
            customer_id=order.customer_id,
            status=order.status,
            payment_status=order.payment_status,
            total_amount=order.total_amount,
            shipping_country=order.shipping_country,
            shipping_country_name=order.shipping_country_name,
            current_location=order.current_location,
            status_changed_at=order.status_changed_at,
            stripe_checkout_session_id=order.stripe_checkout_session_id,
            checkout_url=checkout_url,
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=items,
        )
