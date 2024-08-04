from dataclasses import dataclass
from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bakery_ecommerce.internal.store.persistence.catalog import CatalogItem
from bakery_ecommerce.internal.store.query import Query, QueryHandler


@dataclass
class NormalizeCatalogItemsPosition(Query[bool]):
    catalog_id: str


class NormalizeCatalogItemsPositionHandler(
    QueryHandler[NormalizeCatalogItemsPosition, bool]
):
    @override
    def __init__(self, executor: AsyncSession) -> None:
        self.__executor = executor

    @override
    async def handle(self, query: NormalizeCatalogItemsPosition) -> bool:
        stmt = (
            select(CatalogItem)
            .where(CatalogItem.catalog_id == query.catalog_id)
            .order_by(CatalogItem.position)
        )

        rows = await self.__executor.execute(stmt)

        catalog_items = rows.scalars().all()
        for idx, catalog_item in enumerate(catalog_items, start=1):
            catalog_item.position = idx

        self.__executor.add_all(catalog_items)
        await self.__executor.flush()

        return True
