from typing import TypeAlias
from uuid import UUID, uuid4
from datetime import datetime


from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as UuidColumn
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy import DateTime


naming_convention = {
    "ix": "ix_ct_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_ct_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_ct_%(table_name)s_%(constraint_name)s",
    "fk": "fk_ct_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_ct_%(table_name)s",
}


class Base(DeclarativeBase, AsyncAttrs):
    metadata = MetaData(naming_convention=naming_convention)


PersistanceBase: TypeAlias = Base


class ScalarID:
    id: Mapped[UUID] = mapped_column(
        "id",
        UuidColumn(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid4,
    )


class utc_now(FunctionElement):
    type = DateTime()
    inherit_cache = True


class ScalarTimestamp:
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=utc_now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        server_default=utc_now(),
    )
