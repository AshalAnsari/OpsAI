from sqlalchemy.orm import Session

from app.models.order import OrderStatus
from app.repositories.audit_repository import AuditRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin import (
    AdminOrderDetailResponse,
    AuditLogResponse,
    DashboardMetrics,
)
from app.schemas.order import OrderResponse, OrderStatusUpdate
from app.schemas.user import AdminCustomerResponse
from app.services.fulfillment_service import (
    FulfillmentService,
    allowed_transitions,
    apply_status_side_effects,
)
from app.services.order_service import OrderService
from app.utils.exceptions import AppError
from app.utils.pagination import PaginatedResponse, PaginationParams


class AdminService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.orders = OrderRepository(db)
        self.audit = AuditRepository(db)
        self.order_service = OrderService(db)

    def get_dashboard(self) -> DashboardMetrics:
        recent_orders = [self.order_service._to_response(o) for o in self.orders.recent(8)]
        recent_customers = [self._customer_response(u) for u in self.users.recent_customers(5)]
        recent_logs = [self._audit_response(log) for log in self.audit.recent(10)]

        return DashboardMetrics(
            total_customers=self.users.count_customers(),
            total_orders=self.orders.count_all(),
            pending_orders=self.orders.count_by_status(OrderStatus.PENDING),
            processing_orders=self.orders.count_by_status(OrderStatus.PROCESSING),
            delivered_orders=self.orders.count_by_status(OrderStatus.DELIVERED),
            cancelled_orders=self.orders.count_by_status(OrderStatus.CANCELLED),
            total_revenue=self.orders.total_revenue(),
            recent_orders=recent_orders,
            recent_customers=recent_customers,
            recent_audit_logs=recent_logs,
        )

    def list_customers(
        self,
        pagination: PaginationParams,
        search: str | None = None,
    ) -> PaginatedResponse[AdminCustomerResponse]:
        users, total = self.users.list_customers(
            offset=pagination.offset,
            limit=pagination.page_size,
            search=search,
        )
        return PaginatedResponse.create(
            [self._customer_response(u) for u in users],
            total,
            pagination.page,
            pagination.page_size,
        )

    def get_customer(self, customer_id: int) -> AdminCustomerResponse:
        user = self.users.get_by_id(customer_id)
        if not user or not user.has_role("customer"):
            raise AppError("CUSTOMER_NOT_FOUND", "Customer not found.", 404)
        return self._customer_response(user)

    def list_orders(
        self,
        pagination: PaginationParams,
        *,
        status: OrderStatus | None = None,
        search: str | None = None,
        customer_id: int | None = None,
    ) -> PaginatedResponse[OrderResponse]:
        items, total = self.orders.list_all(
            offset=pagination.offset,
            limit=pagination.page_size,
            status=status,
            search=search,
            customer_id=customer_id,
        )
        return PaginatedResponse.create(
            [self.order_service._to_response(o) for o in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    def get_order(self, order_id: int) -> AdminOrderDetailResponse:
        order = self.orders.get_by_id(order_id)
        if not order:
            raise AppError("ORDER_NOT_FOUND", "Order not found.", 404)

        base = self.order_service._to_response(order)
        return AdminOrderDetailResponse(
            **base.model_dump(),
            customer_email=order.customer.email if order.customer else None,
            customer_name=(
                f"{order.customer.first_name} {order.customer.last_name}" if order.customer else None
            ),
        )

    def update_order_status(self, order_id: int, payload: OrderStatusUpdate, admin_id: int) -> OrderResponse:
        order = self.orders.get_by_id(order_id)
        if not order:
            raise AppError("ORDER_NOT_FOUND", "Order not found.", 404)

        new_status = payload.status
        if new_status == order.status:
            return self.order_service._to_response(order)

        allowed = allowed_transitions(order)
        if new_status not in allowed:
            raise AppError(
                "INVALID_STATUS_TRANSITION",
                f"Cannot transition order from '{order.status.value}' to '{new_status.value}'.",
                400,
                details={
                    "current_status": order.status.value,
                    "requested_status": new_status.value,
                    "allowed": [s.value for s in allowed],
                },
            )

        previous = order.status
        if new_status == OrderStatus.CANCELLED:
            self.order_service._restore_stock(order)

        apply_status_side_effects(order, new_status)
        self.orders.update(order)
        self.audit.create(
            user_id=admin_id,
            action="order.status_changed",
            entity_type="order",
            entity_id=str(order.id),
            metadata={
                "previous_status": previous.value,
                "new_status": new_status.value,
                "changed_by": "admin",
                "current_location": order.current_location,
            },
        )
        self.db.commit()
        refreshed = self.orders.get_by_id(order.id)
        assert refreshed is not None
        return self.order_service._to_response(refreshed)

    def advance_fulfillment_day(self, admin_id: int):
        return FulfillmentService(self.db).advance_day(
            triggered_by="admin",
            force=True,
            actor_user_id=admin_id,
        )

    def list_audit_logs(
        self,
        pagination: PaginationParams,
        *,
        action: str | None = None,
        entity_type: str | None = None,
    ) -> PaginatedResponse[AuditLogResponse]:
        logs, total = self.audit.list_logs(
            offset=pagination.offset,
            limit=pagination.page_size,
            action=action,
            entity_type=entity_type,
        )
        return PaginatedResponse.create(
            [self._audit_response(log) for log in logs],
            total,
            pagination.page,
            pagination.page_size,
        )

    def _customer_response(self, user) -> AdminCustomerResponse:
        order_count, total_spent = self.users.customer_order_stats(user.id)
        return AdminCustomerResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            created_at=user.created_at,
            order_count=order_count,
            total_spent=total_spent,
        )

    @staticmethod
    def _audit_response(log) -> AuditLogResponse:
        return AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_email=log.user.email if log.user else None,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            metadata=log.metadata_json,
            created_at=log.created_at,
        )
