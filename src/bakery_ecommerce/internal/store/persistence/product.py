from uuid import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bakery_ecommerce.internal.upload.store.image_model import Image

from . import base


class Product(base.PersistanceBase, base.ScalarID, base.ScalarTimestamp):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column("name")
    price: Mapped[int] = mapped_column("price")

    product_images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"Product(id={self.id}, name={self.name}, created_at={self.created_at}, updated_at={self.updated_at})"


class ProductImage(base.PersistanceBase, base.ScalarID):
    __tablename__ = "product_images"

    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"))
    image_id: Mapped[UUID] = mapped_column(ForeignKey("images.id"))
    featured: Mapped[bool] = mapped_column(default=False)

    product: Mapped[Product] = relationship(back_populates="product_images")
    image: Mapped[Image] = relationship(
        lazy="joined",
    )
