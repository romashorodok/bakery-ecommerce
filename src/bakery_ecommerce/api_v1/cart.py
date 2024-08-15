from dataclasses import dataclass
from typing import Annotated, Any, Self
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from bakery_ecommerce.composable import Composable, set_key
from bakery_ecommerce.context_bus import (
    ContextBus,
    ContextEventProtocol,
    ContextExecutor,
    ContextPersistenceEvent,
    impl_event,
)
from bakery_ecommerce import dependencies
from bakery_ecommerce.internal.cart.cart_events import (
    GetUserCartEvent,
    UserCartAddCartItemEvent,
    UserCartRetrievedEvent,
)
from bakery_ecommerce.internal.cart.cart_use_cases import (
    GetUserCart,
    GetUserCartResult,
    ProductAlreadyInCart,
    UserCartAddCartItem,
    UserCartAddCartItemResult,
)
from bakery_ecommerce.internal.cart.store.cart_item_model import CartItem
from bakery_ecommerce.internal.cart.store.cart_model import Cart
from bakery_ecommerce.internal.identity.token import Token
from bakery_ecommerce.internal.product import GetProductById, GetProductByIdEvent
from bakery_ecommerce.internal.product_events import ProductByIdRetrievedEvent
from bakery_ecommerce.internal.store.persistence.product import Product
from bakery_ecommerce.internal.store.query import QueryProcessor
from bakery_ecommerce.token_middleware import verify_access_token

api = APIRouter()


def _get_cart_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    get_user_cart = GetUserCart(context, queries)
    return context | ContextExecutor(
        GetUserCartEvent, lambda e: get_user_cart.execute(e)
    )


@api.get(path="/", dependencies=[Depends(verify_access_token)])
async def get_cart(
    context: Annotated[ContextBus, Depends(_get_cart_request__context_bus)],
    token: Annotated[Token, Depends(verify_access_token)],
):
    user_id = token.user_id()
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing user_id for get_cart")

    await context.publish(GetUserCartEvent(user_id))

    result = await context.gather()
    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        GetUserCartResult,
        lambda resp, result: set_key(resp, "cart", result.cart.to_dict()),
    )
    return cmp.reduce(result.flatten())


@dataclass
@impl_event(ContextEventProtocol)
class AddCartItemComposableEvent(ContextPersistenceEvent):
    product_id: str
    quantity: int
    user_id: UUID

    cart: Cart | None = None
    product: Product | None = None

    @property
    def payload(self) -> Self:
        return self


def _add_cart_item_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    _get_user_cart = GetUserCart(context, queries)
    _user_cart_add_cart_item = UserCartAddCartItem(queries)
    _get_product_by_id = GetProductById(context, queries)

    root_event: AddCartItemComposableEvent

    async def publish_get_user_cart_event(e: AddCartItemComposableEvent):
        nonlocal root_event
        root_event = e
        await context.publish(GetUserCartEvent(e.user_id))
        await context.publish(GetProductByIdEvent(e.product_id))

    async def addCartItemComposableWaiter(
        e: UserCartRetrievedEvent | ProductByIdRetrievedEvent,
    ):
        nonlocal root_event

        if isinstance(e, UserCartRetrievedEvent):
            root_event.cart = e.cart

        if isinstance(e, ProductByIdRetrievedEvent):
            root_event.product = e.product

        if root_event.product and root_event.cart:
            await context.publish(
                UserCartAddCartItemEvent(
                    quantity=root_event.quantity,
                    user_id=root_event.user_id,
                    product=root_event.product,
                    cart=root_event.cart,
                )
            )

    return (
        context
        | ContextExecutor(AddCartItemComposableEvent, publish_get_user_cart_event)
        | ContextExecutor(GetUserCartEvent, _get_user_cart.execute)
        | ContextExecutor(GetProductByIdEvent, _get_product_by_id.execute)
        | ContextExecutor(UserCartRetrievedEvent, addCartItemComposableWaiter)
        | ContextExecutor(ProductByIdRetrievedEvent, addCartItemComposableWaiter)
        | ContextExecutor(UserCartAddCartItemEvent, _user_cart_add_cart_item.execute)
    )


class AddCartItemRequestBody(BaseModel):
    quantity: int


@api.post(path="/cart-item/{product_id}", dependencies=[Depends(verify_access_token)])
async def add_cart_item(
    product_id: str,
    body: AddCartItemRequestBody,
    context: Annotated[ContextBus, Depends(_add_cart_item_request__context_bus)],
    token: Annotated[Token, Depends(verify_access_token)],
):
    user_id = token.user_id()
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing user_id for add_cart_item")

    await context.publish(
        AddCartItemComposableEvent(
            product_id=product_id,
            user_id=user_id,
            quantity=body.quantity,
        )
    )

    try:
        result = await context.gather()
        cmp = Composable(dict[str, Any]())
        cmp.reducer(
            UserCartAddCartItemResult,
            lambda resp, result: set_key(resp, "cart_item", result.cart_item),
        )
        return cmp.reduce(result.flatten())
    except ProductAlreadyInCart:
        raise HTTPException(status_code=412, detail="Product already in card")


def register_handler(router: APIRouter):
    router.include_router(api, prefix="/carts")
