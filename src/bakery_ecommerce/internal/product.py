import asyncio
from dataclasses import dataclass
from typing import Any, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.composable import Composable
from bakery_ecommerce.context_bus import (
    ContextBus,
    ContextEventProtocol,
    ContextExecutor,
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
class ProductCreated:
    _payload: Product

    @property
    def payload(self) -> Product:
        return self._payload


class CreateProduct:
    def __init__(self, session: AsyncSession, queries: QueryProcessor) -> None:
        self.__queries = queries
        self.__session = session

    async def execute(self, params: CreateProductParams) -> Product:
        product = await self.__create_product(params.name)

        def create_coro(label: str, number: int):
            async def coro():
                print(f"{label} - {number}")
                if number % 2:
                    return label
                return number

            return coro

        def num_gen():
            number = 0
            while True:
                yield number
                number += 1

        num = num_gen()

        i = next(num)

        async def spanwn_product_event(bus: ContextBus):
            i = next(num)
            if i >= 2:
                return

            print("Spawn coro create value", i)
            print("Before 1 sec delay")
            await asyncio.sleep(1)
            print("After 1 sec delay")
            await bus.publish(evt)
            print("After publish")

        async def spawn_product():
            return Product()

        bus = ContextBus(
            [
                ContextExecutor(
                    ProductCreated, lambda _: create_coro("first coro", i)()
                ),
                ContextExecutor(ProductCreated, lambda _: spawn_product()),
                # ContextExecutor(ProductCreated, lambda _: spanwn_product_event(bus)),
            ],
        )
        evt = ProductCreated(product)

        await bus.publish(evt)

        results = await bus.gather()

        class Container:
            pass

        cmp = Composable(Container())
        cmp.reducer(int, lambda ctx, item: print("reduce int", item))
        cmp.reducer(str, lambda ctx, item: print("reduce str", item))
        cmp.reducer(Product, lambda ctx, item: print("reduce product", item))

        ctx = cmp.reduce(results.flatten())

        # product_created_executor = ContextExecutor(ProductCreated)
        # result = await product_created_executor.run_coros(evt)

        # bus.handlers[""] = product_created_executor

        # handlers = dict[ContextEventProtocol[EventPayload_T], ContextHandlerProtocol](
        #     {evt.name: lambda q: q}
        # )

        # await self.__create_inventory_product(product)

        await self.__session.flush()
        # await self.__session.commit()
        return product

    async def __create_product(self, name: str) -> Product:
        product = persistence.product.Product(name=name)
        operation = CrudOperation(Product, lambda q: q.create_one(product))
        return await self.__queries.process(self.__session, operation)

    async def __create_inventory_product(self, product: Product) -> InventoryProduct:
        inventory_product = InventoryProduct(product=product)
        operation = CrudOperation(
            InventoryProduct, lambda q: q.create_one(inventory_product)
        )
        return await self.__queries.process(self.__session, operation)
