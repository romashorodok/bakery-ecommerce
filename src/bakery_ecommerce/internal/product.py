from dataclasses import dataclass
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import store
from .store import persistence


@dataclass
class GetProductListParams:
    page: int
    page_size: int


class GetProductList:
    def __init__(
        self, session: AsyncSession, queries: store.query.QueryProcessor
    ) -> None:
        self.__queries = queries
        self.__session = session

    async def execute(self, params: GetProductListParams):
        product = persistence.product.Product

        async def get_product_by_cursor(
            session: AsyncSession,
        ) -> Sequence[persistence.product.Product]:
            stmt = select(product).limit(params.page_size).offset(params.page)
            row = await session.execute(stmt)
            return row.scalars().all()

        operation = store.crud_queries.CustomBuilder(get_product_by_cursor)
        return await self.__queries.process(self.__session, operation)


@dataclass
class GetProductByNameParams:
    name: str


class GetProductByName:
    def __init__(
        self, session: AsyncSession, queries: store.query.QueryProcessor
    ) -> None:
        self.__queries = queries
        self.__session = session

    async def execute(
        self, params: GetProductByNameParams
    ) -> persistence.product.Product | None:
        op = store.crud_queries.CrudOperation(
            persistence.product.Product,
            lambda q: q.get_one_by_field("name", params.name),
        )
        return await self.__queries.process(self.__session, op)


@dataclass
class CreateProductParams:
    name: str


class CreateProduct:
    def __init__(
        self, session: AsyncSession, queries: store.query.QueryProcessor
    ) -> None:
        self.__queries = queries
        self.__session = session

    async def execute(self, params: CreateProductParams) -> persistence.product.Product:
        product = persistence.product.Product()
        product.name = params.name
        operation = store.crud_queries.CrudOperation(
            type(product), lambda q: q.create_one(product)
        )
        product = await self.__queries.process(self.__session, operation)

        inventory_product = persistence.inventory_product.InventoryProduct()
        inventory_product.product = product
        operation = store.crud_queries.CrudOperation(
            type(inventory_product),
            lambda q: q.create_one(inventory_product),
        )
        inventory_product = await self.__queries.process(self.__session, operation)

        await self.__session.flush()
        await self.__session.commit()
        return product
