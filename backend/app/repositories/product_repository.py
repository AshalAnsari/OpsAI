from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.product import Product


class ProductRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, product_id: int) -> Product | None:
        return self.db.get(Product, product_id)

    def get_by_slug(self, slug: str) -> Product | None:
        return self.db.scalar(select(Product).where(Product.slug == slug))

    def list_products(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        active_only: bool = False,
        search: str | None = None,
    ) -> tuple[list[Product], int]:
        query = select(Product)
        if active_only:
            query = query.where(Product.is_active.is_(True))
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(Product.name.like(pattern), Product.description.like(pattern), Product.slug.like(pattern))
            )
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        products = list(
            self.db.scalars(query.order_by(Product.created_at.desc()).offset(offset).limit(limit))
        )
        return products, total

    def create(self, product: Product) -> Product:
        self.db.add(product)
        self.db.flush()
        self.db.refresh(product)
        return product

    def update(self, product: Product) -> Product:
        self.db.add(product)
        self.db.flush()
        self.db.refresh(product)
        return product

    def get_for_update(self, product_id: int) -> Product | None:
        return self.db.scalar(select(Product).where(Product.id == product_id).with_for_update())
