from datetime import datetime
from typing import TypeAlias
from uuid import UUID

from pydantic import BaseModel

BaseSchema: TypeAlias = BaseModel


class ScalarIDSchema(BaseSchema):
    id: UUID


class ScalarTimestampSchema(BaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProductSchema(ScalarIDSchema, ScalarTimestampSchema):
    pass
