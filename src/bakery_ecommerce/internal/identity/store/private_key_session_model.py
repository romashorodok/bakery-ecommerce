from typing import Any
from uuid import UUID

from sqlalchemy.orm import MappedColumn, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from bakery_ecommerce.internal.store.persistence.base import PersistanceBase


class PrivateKeySession(PersistanceBase):
    __tablename__ = "private_key_sessions"

    id: MappedColumn[int] = mapped_column(primary_key=True)
    kid: MappedColumn[str] = mapped_column()
    signature: MappedColumn[dict[str, Any]] = mapped_column(type_=JSONB)
    blacklisted: MappedColumn[bool] = mapped_column(default=False)
    user_id: MappedColumn[UUID] = mapped_column()

    def __repr__(self) -> str:
        return f"PrivateKeySession(id={self.id}, kid={self.kid}, signature={self.signature}, blacklisted={self.blacklisted}, user_id={self.user_id})"
