from uuid import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bakery_ecommerce.internal.cart.store.cart_item_model import CartItem
from bakery_ecommerce.internal.store.persistence.base import PersistanceBase, ScalarID


class Cart(PersistanceBase, ScalarID):
    __tablename__ = "carts"

    user_id: Mapped[UUID] = mapped_column()
    cart_items: Mapped[list[CartItem]] = relationship(lazy=False)
