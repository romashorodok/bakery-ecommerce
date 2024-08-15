import fastapi
from fastapi import Depends

from typing import Annotated, Any
from pydantic import BaseModel, model_validator
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
    GetProductById,
    GetProductByIdEvent,
    GetProductByIdResult,
    GetProductList,
    GetProductListEvent,
    GetProductListResult,
    ProductCreatedEvent,
    CreateProduct,
    UpdateProduct,
    UpdateProductEvent,
    UpdateProductResult,
)
from bakery_ecommerce.internal.store.persistence.inventory_product import (
    InventoryProduct,
)
from bakery_ecommerce.internal.store.persistence.product import Product
from bakery_ecommerce.internal.store.query import QueryProcessor
from bakery_ecommerce.token_middleware import verify_access_token


api = fastapi.APIRouter()


class ProductCreateRequestBody(BaseModel):
    name: str
    price: int


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


@api.post(path="/products", dependencies=[Depends(verify_access_token)])
async def product_create(
    body: ProductCreateRequestBody,
    tx: Annotated[AsyncSession, Depends(dependencies.request_transaction)],
    context: Annotated[ContextBus, Depends(_product_create_request__context_bus)],
):
    try:
        await context.publish(CreateProductEvent(body.name, body.price))

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


def _product_list_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    get_product_list = GetProductList(tx, queries)

    return context | ContextExecutor(
        GetProductListEvent, lambda e: get_product_list.execute(e)
    )


@api.get(path="/products")
async def product_list(
    context: ContextBus = Depends(_product_list_request__context_bus),
    page: int = 0,
    page_size: int = 20,
    name: str | None = None,
):
    await context.publish(
        GetProductListEvent(
            page=page,
            page_size=page_size,
            name=name,
        )
    )

    result = await context.gather()

    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        GetProductListResult,
        lambda resp, result: set_key(resp, "products", result.products),
    )

    print(result.items)

    return cmp.reduce(result.flatten())


def _product_by_id_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    get_product_by_id = GetProductById(context, queries)
    return context | ContextExecutor(
        GetProductByIdEvent,
        lambda e: get_product_by_id.execute(e),
    )


@api.get(path="/products/{product_id}")
async def product_by_id(
    product_id: str,
    context: Annotated[ContextBus, Depends(_product_by_id_request__context_bus)],
    response: fastapi.Response,
):
    await context.publish(GetProductByIdEvent(product_id=product_id))

    result = await context.gather()

    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        GetProductByIdResult,
        lambda resp, result: set_key(resp, "product", result.product),
    )

    resp = cmp.reduce(result.flatten())

    if resp.get("product") is None:
        response.status_code = fastapi.status.HTTP_404_NOT_FOUND
        return

    return resp


def _update_product_by_id__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    tx: AsyncSession = Depends(dependencies.request_transaction),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    update_product = UpdateProduct(tx, queries)
    return context | ContextExecutor(
        UpdateProductEvent, lambda e: update_product.execute(e)
    )


class UpdateProductByIdRequestBody(BaseModel):
    name: str | None = None
    description: str | None = None
    price: int | None = None

    @model_validator(mode="before")
    @classmethod
    def at_least_one_field_present(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            raise ValueError("Request body must be a json")

        if not any(data.values()):
            raise ValueError("Request body require at least one field")

        return data


@api.patch(path="/products/{product_id}", dependencies=[Depends(verify_access_token)])
async def update_product_by_id(
    product_id: str,
    body: UpdateProductByIdRequestBody,
    context: Annotated[ContextBus, Depends(_update_product_by_id__context_bus)],
):
    await context.publish(
        UpdateProductEvent(
            product_id=product_id, fields=body.model_dump(exclude_none=True)
        )
    )

    result = await context.gather()

    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        UpdateProductResult,
        lambda resp, result: set_key(resp, "product", result.product),
    )
    return cmp.reduce(result.flatten())


def register_handler(router: fastapi.APIRouter):
    router.include_router(api)
