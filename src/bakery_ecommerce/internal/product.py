from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.internal.store.persistence import product
from . import store


@dataclass
class GetProductByNameParams:
    name: str


class GetProductByName:
    def __init__(
        self, session: AsyncSession, queries: store.query.QueryProcessor
    ) -> None:
        self.__queries = queries
        self.__session = session

    async def execute(self, params: GetProductByNameParams) -> product.Product | None:
        op = store.crud_queries.CrudOperation(
            product.Product,
            lambda q: q.get_one_by_field("name", params.name),
        )
        return await self.__queries.process(self.__session, op)
