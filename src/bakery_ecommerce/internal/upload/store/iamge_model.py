from sqlalchemy.orm import Mapped, mapped_column
from bakery_ecommerce.internal.store.persistence.base import PersistanceBase, ScalarID


class Image(PersistanceBase, ScalarID):
    __tablename__ = "images"

    original_file: Mapped[str] = mapped_column()
    original_file_hash: Mapped[str] = mapped_column()
    bucket: Mapped[str] = mapped_column()
    transcoded_file: Mapped[str | None] = mapped_column()
    submited: Mapped[bool] = mapped_column(default=False)
