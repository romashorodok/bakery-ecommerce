from uuid import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.properties import ForeignKey
from bakery_ecommerce.internal.store.persistence.base import PersistanceBase, ScalarID
from bakery_ecommerce.internal.store.persistence.product import Product


class CartItem(PersistanceBase, ScalarID):
    __tablename__ = "cart_items"

    quantity: Mapped[int] = mapped_column()

    cart_id: Mapped[UUID] = mapped_column(ForeignKey("carts.id"))
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"))
    product: Mapped[Product] = relationship(lazy=False)

    def __repr__(self) -> str:
        return f"CartItem(id={self.id} quantity={self.quantity}, cart_id={self.cart_id}, product_id={self.product_id})"
