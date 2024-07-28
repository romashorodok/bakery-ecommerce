import fastapi
from fastapi import Depends

from typing import Annotated, Any
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce import dependencies
from bakery_ecommerce.composable import Composable, set_key
from bakery_ecommerce.context_bus import ContextBus, ContextExecutor
from bakery_ecommerce.internal.inventory import (
    CreateInventoryProduct,
    CreateInventoryProductEvent,
)
from bakery_ecommerce.internal.product import (
    CreateProductEvent,
    ProductCreatedEvent,
    CreateProduct,
)
from bakery_ecommerce.internal.store.persistence.inventory_product import (
    InventoryProduct,
)
from bakery_ecommerce.internal.store.persistence.product import Product
from bakery_ecommerce.internal.store.query import QueryProcessor


# async def get_shared_session(
#     request: fastapi.Request,
#     session: AsyncSession = fastapi.Depends(dependencies.transaction),
# ) -> AsyncSession:
#     if not hasattr(request.state, "db"):
#         request.state.db = session
#     return request.state.db

# def get_shared_create_product(
#     session: AsyncSession = fastapi.Depends(get_shared_session),
#     queries: QueryProcessor = fastapi.Depends(dependencies.query_processor),
# ):
#     print("create product session", session)
#     yield CreateProduct(session, queries)


api = fastapi.APIRouter()


class ProductCreateRequestBody(BaseModel):
    name: str


def _product_create_request__create_product(
    request: fastapi.Request,
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
    context: ContextBus = Depends(dependencies.request_context_bus),
) -> CreateProduct:
    return dependencies.cache_request_attr(request, CreateProduct(context, tx, queries))


def _product_create_request__create_inventory_product(
    request: fastapi.Request,
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> CreateInventoryProduct:
    return dependencies.cache_request_attr(request, CreateInventoryProduct(tx, queries))


def _product_create_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    create_product: CreateProduct = Depends(_product_create_request__create_product),
    create_inventory_product: CreateInventoryProduct = Depends(
        _product_create_request__create_inventory_product
    ),
) -> ContextBus:
    context.add_executor(
        for_event=CreateProductEvent,
        executor=ContextExecutor(
            CreateProductEvent, lambda e: create_product.execute(e)
        ),
    )
    context.add_executor(
        for_event=ProductCreatedEvent,
        executor=ContextExecutor(
            ProductCreatedEvent,
            lambda e: create_inventory_product.execute(
                CreateInventoryProductEvent(e.id)
            ),
        ),
    )
    return context


@api.post(path="/products")
async def product_create(
    body: ProductCreateRequestBody,
    tx: Annotated[AsyncSession, Depends(dependencies.request_transaction)],
    context: Annotated[ContextBus, Depends(_product_create_request__context_bus)],
):
    try:
        await context.publish(CreateProductEvent(body.name))

        result = await context.gather()

        cmp = Composable(dict[str, Any]())
        cmp.reducer(Product, lambda resp, product: set_key(resp, "product", product))
        cmp.reducer(
            InventoryProduct, lambda resp, inv: set_key(resp, "inventory_product", inv)
        )
        resp = cmp.reduce(result.flatten())

        return resp
    except Exception as e:
        await tx.rollback()
        print("Error occured on product_create context. Err:", e)


# @api.get(path="/products")
# async def product_list(
#     get_product_list: Annotated[
#         internal.product.GetProductList, fastapi.Depends(dependencies.get_product_list)
#     ],
#     page: int = 0,
#     page_size: int = 20,
# ):
#     product_list = await get_product_list.execute(
#         internal.product.GetProductListParams(
#             page=page,
#             page_size=page_size,
#         )
#     )
#
#     return {"product_list": product_list}


# @api.get(path="/product")
# async def product(
#     name: str,
#     product_by_name: Annotated[
#         internal.product.GetProductByName,
#         fastapi.Depends(dependencies.get_product_by_name),
#     ],
#     response: fastapi.Response,
# ):
#     product = await product_by_name.execute(
#         internal.product.GetProductByNameParams(name)
#     )
#     if not product:
#         response.status_code = fastapi.status.HTTP_404_NOT_FOUND
#         return {}
#
#     return {"product": product}


def register_handler(router: fastapi.APIRouter):
    router.include_router(api)
