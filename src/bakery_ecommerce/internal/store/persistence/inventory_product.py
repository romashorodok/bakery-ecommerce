from sqlalchemy.types import INT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import base


class InventoryProduct(base.PersistanceBase, base.ScalarID, base.ScalarTimestamp):
    __tablename__ = "inventory_products"

    quantity_in_fridge: Mapped[int] = mapped_column("quantity_in_fridge", INT)
    quantity_in_bakery: Mapped[int] = mapped_column("quantity_in_fridge", INT)
    quantity_baked: Mapped[int] = mapped_column("quantity_in_fridge", INT)

    product = relationship("Products")
