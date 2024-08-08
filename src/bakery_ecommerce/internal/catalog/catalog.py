from dataclasses import dataclass
from typing import Any, Self, Sequence

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.context_bus import ContextEventProtocol, impl_event
from bakery_ecommerce.internal.catalog.store.catalog_queries import (
    NormalizeCatalogItemsPosition,
)
from bakery_ecommerce.internal.store.crud_queries import CrudOperation, CustomBuilder
from bakery_ecommerce.internal.store.join_queries import (
    JoinOn,
    JoinOperation,
    JoinRoot,
)
from bakery_ecommerce.internal.store.persistence.catalog import Catalog, CatalogItem

from bakery_ecommerce.internal.store.query import QueryProcessor


@dataclass
@impl_event(ContextEventProtocol)
class CreateCatalogEvent:
    headline: str

    @property
    def payload(self) -> Self:
        return self


@dataclass
class CreateCatalogResult:
    catalog: Catalog


class CreateCatalog:
    def __init__(self, session: AsyncSession, queries: QueryProcessor) -> None:
        self.__session = session
        self.__queries = queries

    async def execute(self, params: CreateCatalogEvent):
        model = Catalog()
        model.headline = params.headline
        operation = CrudOperation(Catalog, lambda q: q.create_one(model))
        result = await self.__queries.process(self.__session, operation)
        await self.__session.flush()
        return CreateCatalogResult(result)


@dataclass
@impl_event(ContextEventProtocol)
class GetCatalogListEvent:
    page: int
    page_size: int

    @property
    def payload(self) -> Self:
        return self


@dataclass
class GetCatalogListResult:
    catalogs: Sequence[Catalog]


class GetCatalogList:
    def __init__(self, session: AsyncSession, queries: QueryProcessor) -> None:
        self.__session = session
        self.__queries = queries

    async def execute(self, params: GetCatalogListEvent):
        async def get_catalog_by_cursor(
            session: AsyncSession,
        ) -> Sequence[Catalog]:
            stmt = select(Catalog).limit(params.page_size).offset(params.page)
            row = await session.execute(stmt)
            return row.scalars().unique().all()

        operation = CustomBuilder(get_catalog_by_cursor)
        catalogs = await self.__queries.process(self.__session, operation)
        return GetCatalogListResult(catalogs)


@dataclass
@impl_event(ContextEventProtocol)
class GetCatalogByIdEvent:
    catalog_id: str

    @property
    def payload(self) -> Self:
        return self


@dataclass
class GetCatalogByIdResult:
    catalog: Catalog | None
    catalog_items: list | None


class GetCatalogById:
    def __init__(self, session: AsyncSession, queries: QueryProcessor) -> None:
        self.__session = session
        self.__queries = queries

    async def execute(self, params: GetCatalogByIdEvent):
        operation = JoinOperation(
            where_value=params.catalog_id,
            join_root=JoinRoot(model=Catalog, field="id"),
            join_on={
                CatalogItem: JoinOn(
                    model=CatalogItem,
                    field="catalog_id",
                    root_field="id",
                )
            },
        )

        result = await self.__queries.process(self.__session, operation)

        catalogs = result.get(Catalog)
        if not catalogs or len(catalogs) != 1:
            raise ValueError("GetCatalogById return multiple catalogs or not found")

        catalog = catalogs[0]
        if not isinstance(catalog, Catalog):
            raise ValueError("GetCatalogById not a catalog object or not found")

        catalog_items = result.get(CatalogItem)
        return GetCatalogByIdResult(catalog=catalog, catalog_items=catalog_items)


@dataclass
@impl_event(ContextEventProtocol)
class UpdateCatalogEvent:
    catalog_id: str
    fields: dict[str, Any]

    @property
    def payload(self) -> Self:
        return self


@dataclass
class UpdateCatalogResult:
    catalog: Catalog | None


class UpdateCatalog:
    def __init__(self, session: AsyncSession, queries: QueryProcessor) -> None:
        self.__session = session
        self.__queries = queries

    async def execute(self, params: UpdateCatalogEvent) -> UpdateCatalogResult:
        operation = CrudOperation(
            Catalog, lambda q: q.update_partial("id", params.catalog_id, params.fields)
        )
        result = await self.__queries.process(self.__session, operation)
        return UpdateCatalogResult(result)


@dataclass
@impl_event(ContextEventProtocol)
class CreateCatalogItemEvent:
    catalog_id: str

    @property
    def payload(self) -> Self:
        return self


@dataclass
class CreateCatalogItemResult:
    catalog_item: CatalogItem | None


class CreateCatalogItem:
    def __init__(self, session: AsyncSession, queries: QueryProcessor) -> None:
        self.__session = session
        self.__queries = queries

    async def execute(self, params: CreateCatalogItemEvent) -> CreateCatalogItemResult:
        async def query(session: AsyncSession):
            position_query = (
                select(func.count(CatalogItem.id))
                .where(CatalogItem.catalog_id == params.catalog_id)
                .scalar_subquery()
            )

            stmt = (
                insert(CatalogItem)
                .values(
                    catalog_id=params.catalog_id,
                    position=position_query + 1,
                )
                .returning(CatalogItem)
            )

            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        result = await self.__queries.process(self.__session, CustomBuilder(query))
        return CreateCatalogItemResult(result)


@dataclass
@impl_event(ContextEventProtocol)
class DeleteCatalogItemEvent:
    catalog_id: str
    catalog_item_id: str

    @property
    def payload(self) -> Self:
        return self


@dataclass
class DeleteCatalogItemResult:
    success: bool


class DeleteCatalogItem:
    def __init__(self, session: AsyncSession, queries: QueryProcessor) -> None:
        self.__session = session
        self.__queries = queries

    async def execute(self, params: DeleteCatalogItemEvent) -> DeleteCatalogItemResult:
        operation = CrudOperation(
            CatalogItem, lambda q: q.remote_by_field("id", params.catalog_item_id)
        )
        result = await self.__queries.process(self.__session, operation)
        if not isinstance(result, bool):
            raise ValueError(f"DeleteCatalogItem must return bool got: {type(result)}")

        normalize_position = NormalizeCatalogItemsPosition(params.catalog_id)
        await self.__queries.process(self.__session, normalize_position)
        return DeleteCatalogItemResult(result)


@dataclass
@impl_event(ContextEventProtocol)
class UpdateCatalogItemProductEvent:
    catalog_id: str
    catalog_item_id: str
    product_id: str

    @property
    def payload(self) -> Self:
        return self


@dataclass
class UpdateCatalogItemProductResult:
    catalog_item: CatalogItem | None


class UpdateCatalogItemProduct:
    def __init__(self, session: AsyncSession, queries: QueryProcessor) -> None:
        self.__session = session
        self.__queries = queries

    async def execute(
        self, params: UpdateCatalogItemProductEvent
    ) -> UpdateCatalogItemProductResult:
        operation = CrudOperation(
            CatalogItem,
            lambda q: q.update_partial(
                "id",
                params.catalog_item_id,
                {"product_id": params.product_id},
            ),
        )
        result = await self.__queries.process(self.__session, operation)
        return UpdateCatalogItemProductResult(result)
