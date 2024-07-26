from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import base


class InventoryProduct(base.PersistanceBase, base.ScalarID):
    __tablename__ = "inventory_products"

    quantity_in_fridge: Mapped[int] = mapped_column(insert_default=0)
    quantity_in_bakery: Mapped[int] = mapped_column(insert_default=0)
    quantity_baked: Mapped[int] = mapped_column(insert_default=0)

    product = relationship("Product")
    product_id = Column(UUID, ForeignKey("products.id"))
