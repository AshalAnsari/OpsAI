from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.order_item import OrderItem


class OrderRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, order_id: int) -> Order | None:
        return self.db.scalar(
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.customer),
            )
            .where(Order.id == order_id)
        )

    def get_by_stripe_session(self, session_id: str) -> Order | None:
        return self.db.scalar(
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .where(Order.stripe_checkout_session_id == session_id)
        )

    def list_for_customer(
        self,
        customer_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
        status: OrderStatus | None = None,
    ) -> tuple[list[Order], int]:
        query = (
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .where(Order.customer_id == customer_id)
        )
        if status:
            query = query.where(Order.status == status)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        orders = list(
            self.db.scalars(query.order_by(Order.created_at.desc()).offset(offset).limit(limit))
        )
        return orders, total

    def list_all(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        status: OrderStatus | None = None,
        search: str | None = None,
        customer_id: int | None = None,
    ) -> tuple[list[Order], int]:
        query = select(Order).options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.customer),
        )
        if status:
            query = query.where(Order.status == status)
        if customer_id:
            query = query.where(Order.customer_id == customer_id)
        if search:
            if search.upper().startswith("OP-"):
                try:
                    order_num = int(search.split("-", 1)[1])
                    query = query.where(Order.id == order_num - 10000)
                except ValueError:
                    pass
            elif search.isdigit():
                query = query.where(Order.id == int(search))
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        orders = list(
            self.db.scalars(query.order_by(Order.created_at.desc()).offset(offset).limit(limit))
        )
        return orders, total

    def create(self, order: Order) -> Order:
        self.db.add(order)
        self.db.flush()
        self.db.refresh(order)
        return order

    def update(self, order: Order) -> Order:
        self.db.add(order)
        self.db.flush()
        self.db.refresh(order)
        return order

    def count_by_status(self, status: OrderStatus) -> int:
        return self.db.scalar(select(func.count(Order.id)).where(Order.status == status)) or 0

    def count_all(self) -> int:
        return self.db.scalar(select(func.count(Order.id))) or 0

    def total_revenue(self) -> Decimal:
        result = self.db.scalar(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.payment_status == PaymentStatus.PAID,
                Order.status != OrderStatus.CANCELLED,
            )
        )
        return Decimal(result or 0)

    def recent(self, limit: int = 5) -> list[Order]:
        return list(
            self.db.scalars(
                select(Order)
                .options(
                    selectinload(Order.items).selectinload(OrderItem.product),
                    selectinload(Order.customer),
                )
                .order_by(Order.created_at.desc())
                .limit(limit)
            )
        )
