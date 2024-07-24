from sqlalchemy.orm import Mapped, mapped_column
from . import base


class Product(base.PersistanceBase, base.ScalarID, base.ScalarTimestamp):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column("name")

    def __repr__(self) -> str:
        return f"Product(id={self.id}, name={self.name}, created_at={self.created_at}, updated_at={self.updated_at})"
