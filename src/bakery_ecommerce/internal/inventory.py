from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.context_bus import ContextEventProtocol, impl_event
from bakery_ecommerce.internal.store.query import QueryProcessor

from .store.persistence.inventory_product import InventoryProduct
from .store.crud_queries import CrudOperation


@dataclass
@impl_event(ContextEventProtocol)
class CreateInventoryProductEvent:
    product_id: UUID

    @property
    def payload(self) -> Self:
        return self


class CreateInventoryProduct:
    def __init__(self, session: AsyncSession, queries: QueryProcessor) -> None:
        self.__session = session
        self.__queries = queries

    async def execute(self, params: CreateInventoryProductEvent) -> InventoryProduct:
        inventory_product = InventoryProduct()
        inventory_product.product_id = params.product_id

        inventory_product = await self.__create_inventory_product(inventory_product)

        await self.__session.flush()

        return inventory_product

    async def __create_inventory_product(
        self, inventory_product: InventoryProduct
    ) -> InventoryProduct:
        operation = CrudOperation(
            InventoryProduct, lambda q: q.create_one(inventory_product)
        )
        return await self.__queries.process(self.__session, operation)
