from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.product_service import ProductService
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", summary="List active products")
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    pagination = PaginationParams(page=page, page_size=page_size)
    result = ProductService(db).list_products(pagination, active_only=True, search=search)
    return {"success": True, "data": result}


@router.get("/{product_id}", summary="Get product details")
def get_product(product_id: int, db: Session = Depends(get_db)) -> dict:
    product = ProductService(db).get_product(product_id, active_only=True)
    return {"success": True, "data": product}
