from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.role import Role, User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.scalar(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(
            select(User).options(selectinload(User.roles)).where(User.email == email)
        )

    def get_role_by_name(self, name: str) -> Role | None:
        return self.db.scalar(select(Role).where(Role.name == name))

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    def update(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    def list_customers(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        search: str | None = None,
    ) -> tuple[list[User], int]:
        query = (
            select(User)
            .options(selectinload(User.roles), selectinload(User.orders))
            .join(User.roles)
            .where(Role.name == "customer")
        )
        if search:
            pattern = f"%{search}%"
            query = query.where(
                (User.email.like(pattern))
                | (User.first_name.like(pattern))
                | (User.last_name.like(pattern))
            )

        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        users = list(
            self.db.scalars(query.order_by(User.created_at.desc()).offset(offset).limit(limit)).unique()
        )
        return users, total

    def count_customers(self) -> int:
        return (
            self.db.scalar(
                select(func.count(User.id)).join(User.roles).where(Role.name == "customer")
            )
            or 0
        )

    def recent_customers(self, limit: int = 5) -> list[User]:
        return list(
            self.db.scalars(
                select(User)
                .options(selectinload(User.roles), selectinload(User.orders))
                .join(User.roles)
                .where(Role.name == "customer")
                .order_by(User.created_at.desc())
                .limit(limit)
            ).unique()
        )

    def customer_order_stats(self, user_id: int) -> tuple[int, float]:
        order_count = (
            self.db.scalar(select(func.count(Order.id)).where(Order.customer_id == user_id)) or 0
        )
        total_spent = (
            self.db.scalar(
                select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                    Order.customer_id == user_id,
                    Order.payment_status == PaymentStatus.PAID,
                    Order.status != OrderStatus.CANCELLED,
                )
            )
            or 0
        )
        return order_count, float(total_spent)

    def customer_profile_stats(self, user_id: int) -> dict[str, float | int]:
        order_count = (
            self.db.scalar(select(func.count(Order.id)).where(Order.customer_id == user_id)) or 0
        )
        paid_order_count = (
            self.db.scalar(
                select(func.count(Order.id)).where(
                    Order.customer_id == user_id,
                    Order.payment_status == PaymentStatus.PAID,
                    Order.status != OrderStatus.CANCELLED,
                )
            )
            or 0
        )
        pending_orders = (
            self.db.scalar(
                select(func.count(Order.id)).where(
                    Order.customer_id == user_id,
                    Order.status == OrderStatus.PENDING,
                )
            )
            or 0
        )
        delivered_orders = (
            self.db.scalar(
                select(func.count(Order.id)).where(
                    Order.customer_id == user_id,
                    Order.status == OrderStatus.DELIVERED,
                )
            )
            or 0
        )
        cancelled_orders = (
            self.db.scalar(
                select(func.count(Order.id)).where(
                    Order.customer_id == user_id,
                    Order.status == OrderStatus.CANCELLED,
                )
            )
            or 0
        )
        total_spent = float(
            self.db.scalar(
                select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                    Order.customer_id == user_id,
                    Order.payment_status == PaymentStatus.PAID,
                    Order.status != OrderStatus.CANCELLED,
                )
            )
            or 0
        )
        average_order_value = round(total_spent / paid_order_count, 2) if paid_order_count else 0.0
        return {
            "order_count": order_count,
            "paid_order_count": paid_order_count,
            "pending_orders": pending_orders,
            "delivered_orders": delivered_orders,
            "cancelled_orders": cancelled_orders,
            "total_spent": total_spent,
            "average_order_value": average_order_value,
        }
