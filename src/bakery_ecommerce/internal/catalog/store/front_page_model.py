from uuid import UUID
from sqlalchemy.orm import MappedColumn, mapped_column
from bakery_ecommerce.internal.store.persistence.base import PersistanceBase


class FrontPage(PersistanceBase):
    __tablename__ = "front_pages"

    id: MappedColumn[int] = mapped_column(primary_key=True)
    main: MappedColumn[bool] = mapped_column()
    catalog_id: MappedColumn[UUID] = mapped_column()

    # https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#one-to-many
    # catalog: Mapped[Catalog] = relationship()

    def __repr__(self) -> str:
        return f"FrontPage(id={self.id}, main={self.main})"
