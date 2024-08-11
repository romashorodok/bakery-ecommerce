from dataclasses import dataclass
from typing import Any, Self, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.context_bus import (
    ContextBus,
    ContextEventProtocol,
    ContextPersistenceEvent,
    impl_event,
)
from bakery_ecommerce.internal.product_events import ProductByIdRetrievedEvent

from . import store
from .store import persistence

from .store.crud_queries import CrudOperation
from .store.persistence.product import Product
from .store.query import QueryProcessor


@dataclass
@impl_event(ContextEventProtocol)
class GetProductListEvent:
    page: int
    page_size: int
    name: str | None

    @property
    def payload(self) -> Self:
        return self


@dataclass
class GetProductListResult:
    products: Sequence[Product]


class GetProductList:
    def __init__(
        self, session: AsyncSession, queries: store.query.QueryProcessor
    ) -> None:
        self.__queries = queries
        self.__session = session

    async def execute(self, params: GetProductListEvent) -> GetProductListResult:
        product = persistence.product.Product

        async def get_product_by_cursor(
            session: AsyncSession,
        ) -> Sequence[persistence.product.Product]:
            stmt = select(product).limit(params.page_size).offset(params.page)
            if params.name:
                stmt = stmt.where(product.name.ilike(f"%{params.name}%"))

            row = await session.execute(stmt)
            return row.scalars().all()

        operation = store.crud_queries.CustomBuilder(get_product_by_cursor)
        products = await self.__queries.process(self.__session, operation)
        return GetProductListResult(products)


@dataclass
@impl_event(ContextEventProtocol)
class GetProductByIdEvent(ContextPersistenceEvent):
    product_id: str

    @property
    def payload(self) -> Self:
        return self


@dataclass
class GetProductByIdResult:
    product: Product | None


class GetProductById:
    def __init__(
        self,
        context: ContextBus,
        queries: store.query.QueryProcessor,
    ) -> None:
        self.__context = context
        self.__queries = queries

    async def execute(self, params: GetProductByIdEvent) -> GetProductByIdResult:
        result = await self.__queries.process(
            params.session,
            store.crud_queries.CrudOperation(
                persistence.product.Product,
                lambda q: q.get_one_by_field("id", params.product_id),
            ),
        )
        if result:
            print("publish product")
            await self.__context.publish(ProductByIdRetrievedEvent(result))
        return GetProductByIdResult(result)


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
    price: int

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
        product = await self.__create_product(params.name, params.price)
        await self.__session.flush()
        await self.__context.publish(ProductCreatedEvent(product))
        return product

    async def __create_product(self, name: str, price: int) -> Product:
        product = persistence.product.Product(name=name, price=price)
        operation = CrudOperation(Product, lambda q: q.create_one(product))
        return await self.__queries.process(self.__session, operation)


@dataclass
@impl_event(ContextEventProtocol)
class UpdateProductEvent:
    product_id: str
    fields: dict[str, Any]

    @property
    def payload(self) -> Self:
        return self


@dataclass
class UpdateProductResult:
    product: Product | None


class UpdateProduct:
    def __init__(self, session: AsyncSession, queries: QueryProcessor) -> None:
        self.__session = session
        self.__queries = queries

    async def execute(self, params: UpdateProductEvent) -> UpdateProductResult:
        operation = CrudOperation(
            Product, lambda q: q.update_partial("id", params.product_id, params.fields)
        )
        result = await self.__queries.process(self.__session, operation)
        return UpdateProductResult(result)
