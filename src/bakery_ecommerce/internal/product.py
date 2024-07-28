import asyncio
from dataclasses import dataclass
from typing import Any, Self, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.composable import Composable
from bakery_ecommerce.context_bus import (
    ContextBus,
    ContextEventProtocol,
    impl_event,
)

from . import store
from .store import persistence

from .store.crud_queries import CrudOperation
from .store.persistence.product import Product
from .store.persistence.inventory_product import InventoryProduct
from .store.query import QueryProcessor


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


@dataclass
@impl_event(ContextEventProtocol[Product])
class ProductCreatedEvent:
    _payload: Product

    @property
    def payload(self) -> Product:
        return self._payload


@dataclass
@impl_event(ContextEventProtocol)
class CreateProductEvent:
    name: str

    @property
    def payload(self) -> Self:
        return self


class CreateProduct:
    def __init__(
        self, context: ContextBus, session: AsyncSession, queries: QueryProcessor
    ) -> None:
        self.__queries = queries
        self.__session = session
        self.__context = context

    async def execute(self, params: CreateProductEvent) -> Product:
        product = await self.__create_product(params.name)
        await self.__session.flush()
        await self.__context.publish(ProductCreatedEvent(product))
        return product

    async def __create_product(self, name: str) -> Product:
        product = persistence.product.Product(name=name)
        operation = CrudOperation(Product, lambda q: q.create_one(product))
        return await self.__queries.process(self.__session, operation)
