from enum import StrEnum
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.properties import ForeignKey

from bakery_ecommerce.internal.store.persistence.base import PersistanceBase, ScalarID
from bakery_ecommerce.internal.store.persistence.product import Product


class Payment_Provider_Enum(StrEnum):
    STRIPE = "STRIPE"
    PAYPAL = "PAYPAL"


class Order_Status_Enum(StrEnum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class OrderItem(PersistanceBase, ScalarID):
    __tablename__ = "order_items"

    quantity: Mapped[int] = mapped_column()
    price: Mapped[int] = mapped_column()
    price_multiplier: Mapped[int] = mapped_column()
    price_multiplied: Mapped[int] = mapped_column()

    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"))
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"))

    product: Mapped[Product] = relationship(lazy=False)


class PaymentDetail(PersistanceBase, ScalarID):
    __tablename__ = "payment_details"

    payment_provider: Mapped[Payment_Provider_Enum | None] = mapped_column()
    payment_intent: Mapped[str | None] = mapped_column()
    client_secret: Mapped[str | None] = mapped_column()


class Order(PersistanceBase, ScalarID):
    __tablename__ = "orders"

    order_status: Mapped[Order_Status_Enum] = mapped_column(
        default=Order_Status_Enum.DRAFT
    )

    payment_detail_id: Mapped[UUID] = mapped_column(ForeignKey("payment_details.id"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    payment_detail: Mapped[PaymentDetail] = relationship(lazy=False)
    order_items: Mapped[list[OrderItem]] = relationship(lazy=False)

    def items_price_multiplied(self) -> int:
        return sum(item.price_multiplied for item in self.order_items)
