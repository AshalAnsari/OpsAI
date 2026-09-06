import re

from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.audit_repository import AuditRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.utils.exceptions import AppError
from app.utils.pagination import PaginatedResponse, PaginationParams


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "product"


class ProductService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.products = ProductRepository(db)
        self.audit = AuditRepository(db)

    def list_products(
        self,
        pagination: PaginationParams,
        *,
        active_only: bool = False,
        search: str | None = None,
    ) -> PaginatedResponse[ProductResponse]:
        items, total = self.products.list_products(
            offset=pagination.offset,
            limit=pagination.page_size,
            active_only=active_only,
            search=search,
        )
        return PaginatedResponse.create(
            [self._to_response(item) for item in items],
            total,
            pagination.page,
            pagination.page_size,
        )

    def get_product(self, product_id: int, *, active_only: bool = False) -> ProductResponse:
        product = self.products.get_by_id(product_id)
        if not product or (active_only and not product.is_active):
            raise AppError("PRODUCT_NOT_FOUND", "Product not found.", 404)
        return self._to_response(product)

    def create_product(self, payload: ProductCreate, admin_id: int) -> ProductResponse:
        slug = payload.slug or slugify(payload.name)
        if self.products.get_by_slug(slug):
            raise AppError("PRODUCT_SLUG_EXISTS", "A product with this slug already exists.", 409)

        product = Product(
            name=payload.name.strip(),
            slug=slug,
            description=payload.description.strip(),
            price=payload.price,
            stock_quantity=payload.stock_quantity,
            is_active=payload.is_active,
            image_urls=payload.image_urls or [],
            specs=payload.specs or {},
        )
        self.products.create(product)
        self.audit.create(
            user_id=admin_id,
            action="product.created",
            entity_type="product",
            entity_id=str(product.id),
            metadata={"name": product.name, "price": str(product.price)},
        )
        self.db.commit()
        self.db.refresh(product)
        return self._to_response(product)

    def update_product(self, product_id: int, payload: ProductUpdate, admin_id: int) -> ProductResponse:
        product = self.products.get_by_id(product_id)
        if not product:
            raise AppError("PRODUCT_NOT_FOUND", "Product not found.", 404)

        data = payload.model_dump(exclude_unset=True)
        if "slug" in data and data["slug"]:
            existing = self.products.get_by_slug(data["slug"])
            if existing and existing.id != product.id:
                raise AppError("PRODUCT_SLUG_EXISTS", "A product with this slug already exists.", 409)
        if "name" in data and isinstance(data["name"], str):
            data["name"] = data["name"].strip()
        if "description" in data and isinstance(data["description"], str):
            data["description"] = data["description"].strip()

        for key, value in data.items():
            setattr(product, key, value)

        self.products.update(product)
        self.audit.create(
            user_id=admin_id,
            action="product.updated",
            entity_type="product",
            entity_id=str(product.id),
            metadata={k: (str(v) if not isinstance(v, (dict, list)) else v) for k, v in data.items()},
        )
        self.db.commit()
        self.db.refresh(product)
        return self._to_response(product)

    def deactivate_product(self, product_id: int, admin_id: int) -> ProductResponse:
        product = self.products.get_by_id(product_id)
        if not product:
            raise AppError("PRODUCT_NOT_FOUND", "Product not found.", 404)

        product.is_active = False
        self.products.update(product)
        self.audit.create(
            user_id=admin_id,
            action="product.deactivated",
            entity_type="product",
            entity_id=str(product.id),
            metadata={"name": product.name},
        )
        self.db.commit()
        self.db.refresh(product)
        return self._to_response(product)

    @staticmethod
    def _to_response(product: Product) -> ProductResponse:
        return ProductResponse(
            id=product.id,
            name=product.name,
            slug=product.slug,
            description=product.description,
            price=product.price,
            stock_quantity=product.stock_quantity,
            is_active=product.is_active,
            image_urls=list(product.image_urls or []),
            specs=dict(product.specs or {}),
            created_at=product.created_at,
            updated_at=product.updated_at,
        )
