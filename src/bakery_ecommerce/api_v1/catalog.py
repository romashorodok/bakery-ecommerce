from typing import Annotated, Any
from fastapi import Depends
from fastapi.routing import APIRouter
from pydantic import BaseModel, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.composable import Composable, set_key
from bakery_ecommerce.context_bus import ContextBus, ContextExecutor
from bakery_ecommerce import dependencies
from bakery_ecommerce.internal.catalog.catalog import (
    CreateCatalog,
    CreateCatalogEvent,
    CreateCatalogItem,
    CreateCatalogItemEvent,
    CreateCatalogItemResult,
    CreateCatalogResult,
    DeleteCatalogItem,
    DeleteCatalogItemEvent,
    DeleteCatalogItemResult,
    GetCatalogById,
    GetCatalogByIdEvent,
    GetCatalogByIdResult,
    GetCatalogList,
    GetCatalogListEvent,
    GetCatalogListResult,
    UpdateCatalog,
    UpdateCatalogEvent,
    UpdateCatalogItemProduct,
    UpdateCatalogItemProductEvent,
    UpdateCatalogItemProductResult,
    UpdateCatalogResult,
)
from bakery_ecommerce.internal.store.query import QueryProcessor


api = APIRouter()


def _create_catalog_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    create_catalog = CreateCatalog(tx, queries)
    return context | ContextExecutor(
        CreateCatalogEvent, lambda e: create_catalog.execute(e)
    )


class CreateCatalogRequestBody(BaseModel):
    headline: str


@api.post(path="/")
async def create_catalog(
    body: CreateCatalogRequestBody,
    context: Annotated[ContextBus, Depends(_create_catalog_request__context_bus)],
):
    await context.publish(CreateCatalogEvent(headline=body.headline))

    result = await context.gather()

    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        CreateCatalogResult,
        lambda resp, result: set_key(resp, "catalog", result.catalog),
    )
    return cmp.reduce(result.flatten())


def _get_catalog_list_request__context_bus(
    context: Annotated[ContextBus, Depends(dependencies.request_context_bus)],
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    get_catalog_list = GetCatalogList(tx, queries)
    return context | ContextExecutor(
        GetCatalogListEvent, lambda e: get_catalog_list.execute(e)
    )


@api.get(path="/")
async def get_catalog_list(
    context: ContextBus = Depends(_get_catalog_list_request__context_bus),
    page: int = 0,
    page_size: int = 20,
):
    await context.publish(GetCatalogListEvent(page, page_size))

    result = await context.gather()
    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        GetCatalogListResult,
        lambda resp, result: set_key(resp, "catalogs", result.catalogs),
    )
    return cmp.reduce(result.flatten())


def _get_catalog_by_id_request__context_bus(
    context: Annotated[ContextBus, Depends(dependencies.request_context_bus)],
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    get_catalog_by_id = GetCatalogById(tx, queries)
    return context | ContextExecutor(
        GetCatalogByIdEvent, lambda e: get_catalog_by_id.execute(e)
    )


@api.get(path="/{catalog_id}")
async def get_catalog_by_id(
    catalog_id: str,
    context: Annotated[ContextBus, Depends(_get_catalog_by_id_request__context_bus)],
):
    await context.publish(
        GetCatalogByIdEvent(
            catalog_id=catalog_id,
        )
    )

    result = await context.gather()
    cmp = Composable(dict[str, Any]())

    def catalog_mapper(resp: dict[str, Any], result: GetCatalogByIdResult):
        set_key(resp, "catalog", result.catalog)
        set_key(resp, "catalog_items", result.catalog_items)

    cmp.reducer(GetCatalogByIdResult, catalog_mapper)
    return cmp.reduce(result.flatten())


def _update_catalog_by_id_request__context_bus(
    context: Annotated[ContextBus, Depends(dependencies.request_context_bus)],
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    update_catalog = UpdateCatalog(tx, queries)
    return context | ContextExecutor(
        UpdateCatalogEvent, lambda e: update_catalog.execute(e)
    )


class UpdateCatalogByIdRequestBody(BaseModel):
    headline: str | None = None

    @model_validator(mode="before")
    @classmethod
    def at_least_one_field_present(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            raise ValueError("Request body must be a json")

        if not any(data.values()):
            raise ValueError("Request body require at least one field")

        return data


@api.patch(path="/{catalog_id}")
async def update_catalog_by_id(
    catalog_id: str,
    body: UpdateCatalogByIdRequestBody,
    context: Annotated[ContextBus, Depends(_update_catalog_by_id_request__context_bus)],
):
    await context.publish(
        UpdateCatalogEvent(
            catalog_id=catalog_id,
            fields=body.model_dump(exclude_none=True),
        )
    )

    result = await context.gather()

    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        UpdateCatalogResult,
        lambda resp, result: set_key(resp, "catalog", result.catalog),
    )
    return cmp.reduce(result.flatten())


def _create_catalog_item_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    _create_catalog_item = CreateCatalogItem(tx, queries)
    return context | ContextExecutor(
        CreateCatalogItemEvent, lambda e: _create_catalog_item.execute(e)
    )


@api.post(path="/{catalog_id}/catalog-item")
async def create_catalog_item(
    catalog_id: str,
    context: Annotated[ContextBus, Depends(_create_catalog_item_request__context_bus)],
):
    await context.publish(CreateCatalogItemEvent(catalog_id=catalog_id))

    result = await context.gather()
    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        CreateCatalogItemResult,
        lambda resp, result: set_key(resp, "catalog_item", result),
    )
    return cmp.reduce(result.flatten())


def _delete_catalog_item_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    _delete_catalog_item = DeleteCatalogItem(tx, queries)
    return context | ContextExecutor(
        DeleteCatalogItemEvent, lambda e: _delete_catalog_item.execute(e)
    )


@api.delete(path="/{catalog_id}/catalog-item/{catalog_item_id}")
async def delete_catalog_item(
    catalog_id: str,
    catalog_item_id: str,
    context: Annotated[ContextBus, Depends(_delete_catalog_item_request__context_bus)],
):
    await context.publish(DeleteCatalogItemEvent(catalog_id, catalog_item_id))

    result = await context.gather()

    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        DeleteCatalogItemResult,
        lambda resp, result: set_key(resp, "success", result.success),
    )
    return cmp.reduce(result.flatten())


class ChangeCatalogItemProductRequestBody(BaseModel):
    product_id: str


def _change_catalog_item_product_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    update_catalog_item_product = UpdateCatalogItemProduct(tx, queries)
    return context | ContextExecutor(
        UpdateCatalogItemProductEvent, lambda q: update_catalog_item_product.execute(q)
    )


@api.put(path="/{catalog_id}/catalog-item/{catalog_item_id}/product")
async def change_catalog_item_product(
    catalog_id: str,
    catalog_item_id: str,
    body: ChangeCatalogItemProductRequestBody,
    context: Annotated[
        ContextBus, Depends(_change_catalog_item_product_request__context_bus)
    ],
):
    await context.publish(
        UpdateCatalogItemProductEvent(
            catalog_id=catalog_id,
            catalog_item_id=catalog_item_id,
            product_id=body.product_id,
        )
    )

    result = await context.gather()
    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        UpdateCatalogItemProductResult,
        lambda resp, result: set_key(resp, "catalog_item", result.catalog_item),
    )
    return cmp.reduce(result.flatten())


def register_handler(router: APIRouter):
    router.include_router(api, prefix="/catalogs")
    pass
