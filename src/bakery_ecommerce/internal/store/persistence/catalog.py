from uuid import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.types import BOOLEAN, INT, TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bakery_ecommerce.internal.store.persistence.product import Product
from . import base


class CatalogItem(base.PersistanceBase, base.ScalarID):
    __tablename__ = "catalog_items"

    available: Mapped[bool] = mapped_column("available", BOOLEAN)
    visible: Mapped[bool] = mapped_column("visible", BOOLEAN)
    position: Mapped[int] = mapped_column("position", INT)

    catalog_id: Mapped[UUID] = mapped_column(ForeignKey("catalogs.id"))
    product_id: Mapped[UUID | None] = mapped_column(ForeignKey("products.id"))
    product: Mapped[Product | None] = relationship(lazy=False)


class Catalog(base.PersistanceBase, base.ScalarID):
    __tablename__ = "catalogs"

    headline: Mapped[str] = mapped_column("headline", TEXT)
