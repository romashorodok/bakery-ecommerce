from dataclasses import dataclass
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.context_bus import ContextEventProtocol, impl_event
from bakery_ecommerce.internal.catalog.store.front_page_model import FrontPage
from bakery_ecommerce.internal.store.crud_queries import CrudOperation
from bakery_ecommerce.internal.store.join_queries import JoinOn, JoinOperation, JoinRoot
from bakery_ecommerce.internal.store.persistence.catalog import CatalogItem
from bakery_ecommerce.internal.store.query import QueryProcessor


@dataclass
@impl_event(ContextEventProtocol)
class GetFrontPageEvent:
    @property
    def payload(self) -> Self:
        return self


@dataclass
class GetFrontPageResult:
    front_page: FrontPage | None
    catalog_items: list | None


class GetFrontPage:
    def __init__(self, session: AsyncSession, queries: QueryProcessor) -> None:
        self.__session = session
        self.__queries = queries

    async def execute(self, _: GetFrontPageEvent) -> GetFrontPageResult:
        operation = JoinOperation(
            where_value=True,
            join_root=JoinRoot(model=FrontPage, field="main"),
            join_on={
                CatalogItem: JoinOn(
                    model=CatalogItem,
                    field="catalog_id",
                    root_field="catalog_id",
                )
            },
        )

        result = await self.__queries.process(self.__session, operation)

        front_pages = result.get(FrontPage)
        if not front_pages or len(front_pages) != 1:
            raise ValueError("GetFrontPage return multiple front_pages or not found")

        front_page = front_pages[0]
        if not isinstance(front_page, FrontPage):
            raise ValueError("GetFrontPage not a FrontPage or not found")

        catalog_items = result.get(CatalogItem)
        return GetFrontPageResult(front_page, catalog_items)


@dataclass
@impl_event(ContextEventProtocol)
class SetFrontPageCatalogEvent:
    catalog_id: str
    front_page_id: int

    @property
    def payload(self) -> Self:
        return self


@dataclass
class SetFrontPageCatalogResult:
    front_page: FrontPage | None


class SetFrontPageCatalog:
    def __init__(self, session: AsyncSession, queries: QueryProcessor) -> None:
        self.__session = session
        self.__queries = queries

    async def execute(self, params: SetFrontPageCatalogEvent):
        operation = CrudOperation(
            FrontPage,
            lambda q: q.update_partial(
                "id",
                params.front_page_id,
                {"catalog_id": params.catalog_id},
            ),
        )
        result = await self.__queries.process(self.__session, operation)
        return SetFrontPageCatalogResult(result)
