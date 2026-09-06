from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.rbac import require_admin
from app.models.order import OrderStatus
from app.models.role import User
from app.schemas.order import OrderStatusUpdate
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.admin_service import AdminService
from app.services.product_service import ProductService
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", summary="Operational dashboard metrics", tags=["Admin"])
def dashboard(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    data = AdminService(db).get_dashboard()
    return {"success": True, "data": data}


@router.get("/customers", summary="List customers")
def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    pagination = PaginationParams(page=page, page_size=page_size)
    data = AdminService(db).list_customers(pagination, search)
    return {"success": True, "data": data}


@router.get("/customers/{customer_id}", summary="Get customer details")
def get_customer(
    customer_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    data = AdminService(db).get_customer(customer_id)
    return {"success": True, "data": data}


@router.get("/products", summary="List all products (including inactive)")
def list_admin_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    pagination = PaginationParams(page=page, page_size=page_size)
    data = ProductService(db).list_products(pagination, active_only=False, search=search)
    return {"success": True, "data": data}


@router.post("/products", summary="Create product")
def create_product(
    payload: ProductCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    data = ProductService(db).create_product(payload, current_user.id)
    return {"success": True, "data": data}


@router.put("/products/{product_id}", summary="Update product")
def update_product(
    product_id: int,
    payload: ProductUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    data = ProductService(db).update_product(product_id, payload, current_user.id)
    return {"success": True, "data": data}


@router.delete("/products/{product_id}", summary="Soft-delete / deactivate product")
def delete_product(
    product_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    data = ProductService(db).deactivate_product(product_id, current_user.id)
    return {"success": True, "data": data}


@router.get("/orders", summary="List all orders")
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: OrderStatus | None = Query(None),
    search: str | None = Query(None),
    customer_id: int | None = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    pagination = PaginationParams(page=page, page_size=page_size)
    data = AdminService(db).list_orders(
        pagination, status=status, search=search, customer_id=customer_id
    )
    return {"success": True, "data": data}


@router.get("/orders/{order_id}", summary="Get order details")
def get_order(
    order_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    data = AdminService(db).get_order(order_id)
    return {"success": True, "data": data}


@router.patch("/orders/{order_id}/status", summary="Update order status with validated transitions")
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    data = AdminService(db).update_order_status(order_id, payload, current_user.id)
    return {"success": True, "data": data}


@router.post("/fulfillment/advance-day", summary="Force-advance all paid orders by one fulfillment step")
def advance_fulfillment_day(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    data = AdminService(db).advance_fulfillment_day(current_user.id)
    return {"success": True, "data": data}


@router.get("/audit-logs", summary="List audit logs", tags=["Audit"])
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: str | None = Query(None),
    entity_type: str | None = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    pagination = PaginationParams(page=page, page_size=page_size)
    data = AdminService(db).list_audit_logs(pagination, action=action, entity_type=entity_type)
    return {"success": True, "data": data}
