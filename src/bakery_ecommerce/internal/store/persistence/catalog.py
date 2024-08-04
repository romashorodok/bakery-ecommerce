from uuid import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.types import BOOLEAN, INT, TEXT
from sqlalchemy.orm import Mapped, mapped_column
from . import base


class CatalogItem(base.PersistanceBase, base.ScalarID):
    __tablename__ = "catalog_items"

    available: Mapped[bool] = mapped_column("available", BOOLEAN)
    visible: Mapped[bool] = mapped_column("visible", BOOLEAN)
    position: Mapped[int] = mapped_column("position", INT)

    catalog_id: Mapped[UUID] = mapped_column(ForeignKey("catalogs.id"))


class Catalog(base.PersistanceBase, base.ScalarID):
    __tablename__ = "catalogs"

    headline: Mapped[str] = mapped_column("headline", TEXT)
    # catalog_items: Mapped[list[CatalogItem]] = relationship(lazy=False)
