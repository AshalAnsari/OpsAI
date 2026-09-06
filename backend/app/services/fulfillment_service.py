from datetime import date, datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.fulfillment import FulfillmentJobRun
from app.models.order import WAREHOUSE_LOCATION, Order, OrderStatus, PaymentStatus
from app.models.order_item import OrderItem
from app.repositories.audit_repository import AuditRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.order import FulfillmentAdvanceResponse
from app.services.notification_service import NotificationService

settings = get_settings()

# Customers may cancel only before the package leaves the warehouse.
CANCELLABLE_STATUSES = {
    OrderStatus.PENDING,
    OrderStatus.CONFIRMED,
    OrderStatus.PROCESSING,
}

# Admin / system adjacency graph. Domestic vs international branching is enforced
# dynamically in allowed_transitions() / next_status().
ALLOWED_STATUS_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
    OrderStatus.PROCESSING: {OrderStatus.DISPATCHED, OrderStatus.CANCELLED},
    OrderStatus.DISPATCHED: {
        OrderStatus.OUT_FOR_DELIVERY,
        OrderStatus.IN_TRANSIT_INTERNATIONAL,
    },
    OrderStatus.IN_TRANSIT_INTERNATIONAL: {OrderStatus.CUSTOMS_CLEARANCE},
    OrderStatus.CUSTOMS_CLEARANCE: {OrderStatus.OUT_FOR_DELIVERY},
    OrderStatus.OUT_FOR_DELIVERY: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}

ADVANCEABLE_STATUSES = {
    OrderStatus.CONFIRMED,
    OrderStatus.PROCESSING,
    OrderStatus.DISPATCHED,
    OrderStatus.IN_TRANSIT_INTERNATIONAL,
    OrderStatus.CUSTOMS_CLEARANCE,
    OrderStatus.OUT_FOR_DELIVERY,
}

DOMESTIC_FLOW = [
    OrderStatus.PENDING,
    OrderStatus.CONFIRMED,
    OrderStatus.PROCESSING,
    OrderStatus.DISPATCHED,
    OrderStatus.OUT_FOR_DELIVERY,
    OrderStatus.DELIVERED,
]

INTERNATIONAL_FLOW = [
    OrderStatus.PENDING,
    OrderStatus.CONFIRMED,
    OrderStatus.PROCESSING,
    OrderStatus.DISPATCHED,
    OrderStatus.IN_TRANSIT_INTERNATIONAL,
    OrderStatus.CUSTOMS_CLEARANCE,
    OrderStatus.OUT_FOR_DELIVERY,
    OrderStatus.DELIVERED,
]


def is_domestic_country(shipping_country: str | None) -> bool:
    return (shipping_country or "US").upper() == "US"


def destination_label(order: Order) -> str:
    name = (order.shipping_country_name or "").strip()
    code = (order.shipping_country or "US").upper()
    if name:
        return f"{name} ({code})"
    return code


def location_for_status(order: Order, status: OrderStatus) -> str | None:
    dest = destination_label(order)
    mapping = {
        OrderStatus.PENDING: None,
        OrderStatus.CONFIRMED: WAREHOUSE_LOCATION,
        OrderStatus.PROCESSING: f"{WAREHOUSE_LOCATION} — packing",
        OrderStatus.DISPATCHED: f"Left {WAREHOUSE_LOCATION}",
        OrderStatus.IN_TRANSIT_INTERNATIONAL: f"In international transit to {dest}",
        OrderStatus.CUSTOMS_CLEARANCE: f"Customs clearance — {dest}",
        OrderStatus.OUT_FOR_DELIVERY: f"Out for delivery — {dest}",
        OrderStatus.DELIVERED: f"Delivered — {dest}",
        OrderStatus.CANCELLED: order.current_location,
    }
    return mapping.get(status)


def next_status(order: Order) -> OrderStatus | None:
    status = order.status
    if status == OrderStatus.CONFIRMED:
        return OrderStatus.PROCESSING
    if status == OrderStatus.PROCESSING:
        return OrderStatus.DISPATCHED
    if status == OrderStatus.DISPATCHED:
        return (
            OrderStatus.OUT_FOR_DELIVERY
            if is_domestic_country(order.shipping_country)
            else OrderStatus.IN_TRANSIT_INTERNATIONAL
        )
    if status == OrderStatus.IN_TRANSIT_INTERNATIONAL:
        return OrderStatus.CUSTOMS_CLEARANCE
    if status == OrderStatus.CUSTOMS_CLEARANCE:
        return OrderStatus.OUT_FOR_DELIVERY
    if status == OrderStatus.OUT_FOR_DELIVERY:
        return OrderStatus.DELIVERED
    return None


def allowed_transitions(order: Order) -> set[OrderStatus]:
    base = set(ALLOWED_STATUS_TRANSITIONS.get(order.status, set()))
    if order.status == OrderStatus.DISPATCHED:
        if is_domestic_country(order.shipping_country):
            return {OrderStatus.OUT_FOR_DELIVERY}
        return {OrderStatus.IN_TRANSIT_INTERNATIONAL}
    return base


def apply_status_side_effects(order: Order, new_status: OrderStatus, *, now: datetime | None = None) -> None:
    stamp = now or datetime.now(timezone.utc)
    order.status = new_status
    order.status_changed_at = stamp
    loc = location_for_status(order, new_status)
    if loc is not None:
        order.current_location = loc


class FulfillmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.orders = OrderRepository(db)
        self.audit = AuditRepository(db)
        self.notifications = NotificationService(db)

    def advance_day(
        self,
        *,
        triggered_by: str = "cron",
        force: bool = False,
        actor_user_id: int | None = None,
    ) -> FulfillmentAdvanceResponse:
        """Advance eligible paid orders by one fulfillment step.

        Cron: at most once per configured interval (dev 10m / prod 60m).
        Admin force: ignores interval guards for demos.
        """
        now = datetime.now(timezone.utc)
        today = now.date()
        interval = timedelta(minutes=settings.fulfillment_interval_minutes)

        if triggered_by == "cron" and not force:
            last_cron = self.db.scalar(
                select(FulfillmentJobRun)
                .where(FulfillmentJobRun.triggered_by == "cron")
                .order_by(desc(FulfillmentJobRun.created_at), desc(FulfillmentJobRun.id))
                .limit(1)
            )
            if last_cron and last_cron.created_at:
                last_at = last_cron.created_at
                if last_at.tzinfo is None:
                    last_at = last_at.replace(tzinfo=timezone.utc)
                if now - last_at < interval:
                    return FulfillmentAdvanceResponse(
                        advanced_count=0,
                        run_date=today.isoformat(),
                        triggered_by=triggered_by,
                        skipped=True,
                        message=(
                            f"Fulfillment cron already ran within the last "
                            f"{settings.fulfillment_interval_minutes} minute(s)."
                        ),
                    )

        candidates = list(
            self.db.scalars(
                select(Order)
                .options(selectinload(Order.items).selectinload(OrderItem.product))
                .where(
                    Order.payment_status == PaymentStatus.PAID,
                    Order.status.in_(ADVANCEABLE_STATUSES),
                )
                .order_by(Order.id.asc())
            )
        )

        advanced = 0
        for order in candidates:
            if not force and not self._eligible_for_interval(order, now, interval):
                continue
            nxt = next_status(order)
            if not nxt:
                continue
            previous = order.status
            apply_status_side_effects(order, nxt, now=now)
            self.orders.update(order)
            self.audit.create(
                user_id=actor_user_id or order.customer_id,
                action="order.fulfillment_advanced",
                entity_type="order",
                entity_id=str(order.id),
                metadata={
                    "previous_status": previous.value,
                    "new_status": nxt.value,
                    "triggered_by": triggered_by,
                    "current_location": order.current_location,
                    "shipping_country": order.shipping_country,
                    "interval_minutes": settings.fulfillment_interval_minutes,
                },
            )
            self.notifications.notify(
                user_id=order.customer_id,
                title=f"Order {order.display_id} update",
                body=(
                    f"Your order is now {nxt.value.replace('_', ' ')}. "
                    f"Current location: {order.current_location or 'updating'}."
                ),
                link=f"/orders/{order.id}",
            )
            advanced += 1

        run = FulfillmentJobRun(
            run_date=today,
            triggered_by=triggered_by,
            advanced_count=advanced,
        )
        self.db.add(run)
        self.db.commit()

        return FulfillmentAdvanceResponse(
            advanced_count=advanced,
            run_date=today.isoformat(),
            triggered_by=triggered_by,
            skipped=False,
            message=f"Advanced {advanced} order(s) one fulfillment step.",
        )

    @staticmethod
    def _eligible_for_interval(order: Order, now: datetime, interval: timedelta) -> bool:
        if order.status_changed_at is None:
            return True
        changed = order.status_changed_at
        if changed.tzinfo is None:
            changed = changed.replace(tzinfo=timezone.utc)
        else:
            changed = changed.astimezone(timezone.utc)
        return (now - changed) >= interval
