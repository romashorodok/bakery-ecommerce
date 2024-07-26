from sqlalchemy.types import BOOLEAN, INT, TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import base


class CatalogItem(base.PersistanceBase, base.ScalarID, base.ScalarTimestamp):
    __tablename__ = "catalog_items"

    available: Mapped[bool] = mapped_column("available", BOOLEAN)
    visible: Mapped[bool] = mapped_column("visible", BOOLEAN)
    position: Mapped[int] = mapped_column("position", INT)

    product = relationship("Products")
    catalog = relationship("Catalogs")


class Catalog(base.PersistanceBase, base.ScalarID, base.ScalarTimestamp):
    __tablename__ = "catalogs"

    headline: Mapped[str] = mapped_column("headline", TEXT)
