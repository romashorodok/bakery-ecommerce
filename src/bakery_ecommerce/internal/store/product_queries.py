from dataclasses import dataclass
from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from . import query
from . import persistence


@dataclass
class FindProductByName(query.Query[persistence.product.Product | None]):
    name: str


class FindProductByNameHandler(
    query.QueryHandler[FindProductByName, persistence.product.Product | None]
):
    @override
    def __init__(self, executor: AsyncSession) -> None:
        self.__executor = executor

    @override
    async def handle(
        self, query: FindProductByName
    ) -> persistence.product.Product | None:
        product = persistence.product.Product

        stmt = select(product).where(product.name == query.name)
        result = await self.__executor.execute(stmt)

        return result.scalar_one_or_none()
