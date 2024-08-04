from typing import Annotated, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.composable import Composable, set_key
from bakery_ecommerce.context_bus import ContextBus, ContextExecutor
from bakery_ecommerce import dependencies
from bakery_ecommerce.internal.catalog.front_page import (
    GetFrontPage,
    GetFrontPageEvent,
    GetFrontPageResult,
    SetFrontPageCatalog,
    SetFrontPageCatalogEvent,
    SetFrontPageCatalogResult,
)
from bakery_ecommerce.internal.store.query import QueryProcessor


api = APIRouter()


def _update_front_page_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    set_front_page_catalog = SetFrontPageCatalog(tx, queries)
    return context | ContextExecutor(
        SetFrontPageCatalogEvent, lambda e: set_front_page_catalog.execute(e)
    )


class UpdateFrontPageRequestBody(BaseModel):
    catalog_id: str
    front_page_id: int


@api.put("/")
async def update_front_page(
    body: UpdateFrontPageRequestBody,
    context: Annotated[ContextBus, Depends(_update_front_page_request__context_bus)],
):
    await context.publish(
        SetFrontPageCatalogEvent(
            catalog_id=body.catalog_id,
            front_page_id=body.front_page_id,
        )
    )

    result = await context.gather()
    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        SetFrontPageCatalogResult,
        lambda resp, result: set_key(resp, "front_page", result.front_page),
    )
    return cmp.reduce(result.flatten())


def _get_front_page_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    get_front_page = GetFrontPage(tx, queries)
    return context | ContextExecutor(
        GetFrontPageEvent, lambda e: get_front_page.execute(e)
    )


@api.get("/")
async def front_page(
    context: Annotated[ContextBus, Depends(_get_front_page_request__context_bus)],
):
    await context.publish(GetFrontPageEvent())
    result = await context.gather()
    cmp = Composable(dict[str, Any]())

    def front_page_mapper(resp: dict[str, Any], result: GetFrontPageResult):
        set_key(resp, "front_page", result.front_page)
        set_key(resp, "catalog_items", result.catalog_items)

    cmp.reducer(GetFrontPageResult, front_page_mapper)
    return cmp.reduce(result.flatten())


def register_handler(router: APIRouter):
    router.include_router(api, prefix="/front-page")
