from dataclasses import dataclass
from typing import Annotated, Any, Self
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import json

from bakery_ecommerce.composable import Composable, set_key
from bakery_ecommerce.context_bus import (
    ContextBus,
    ContextEventProtocol,
    ContextExecutor,
    impl_event,
)
from bakery_ecommerce.internal.cart.cart_events import (
    GetUserCartEvent,
    UserCartRetrievedEvent,
)
from bakery_ecommerce.internal.cart.cart_use_cases import GetUserCart
from bakery_ecommerce.internal.cart.store.cart_model import Cart
from bakery_ecommerce.internal.identity.token import Token
from bakery_ecommerce.internal.order.billing import StripeBilling
from bakery_ecommerce.internal.order.order_events import (
    CartItemsToOrderItemsEvent,
    ChangePaymentMethodEvent,
    GetOrdersEvent,
    GetUserDraftOrderEvent,
    GetUserOrdersEvent,
    UserDraftOrderRetrievedEvent,
)
from bakery_ecommerce.internal.order.order_use_cases import (
    CartItemsToOrderItems,
    ChangePaymentMethod,
    ChangePaymentMethodResult,
    GetOrders,
    GetOrdersResult,
    GetUserDraftOrder,
    GetUserDraftOrderResult,
    GetUserOrders,
    GetUserOrdersResult,
)
from bakery_ecommerce.internal.order.store.order_model import (
    Order,
    Payment_Provider_Enum,
)
from bakery_ecommerce.internal.store.query import QueryProcessor
from bakery_ecommerce.token_middleware import verify_access_token
from bakery_ecommerce import dependencies


api = APIRouter()


def user_get_or_create_draft_order_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    _get_user_draft_order = GetUserDraftOrder(context, queries)
    return context | ContextExecutor(
        GetUserDraftOrderEvent, _get_user_draft_order.execute
    )


@api.get("/draft", dependencies=[Depends(verify_access_token)])
async def user_get_or_create_draft_order(
    context: Annotated[
        ContextBus, Depends(user_get_or_create_draft_order_request__context_bus)
    ],
    token: Annotated[Token, Depends(verify_access_token)],
):
    user_id = token.user_id()
    if not user_id:
        raise HTTPException(status_code=401, detail="Not found user_id")

    await context.publish(GetUserDraftOrderEvent(user_id=user_id))

    result = await context.gather()
    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        GetUserDraftOrderResult,
        lambda resp, result: set_key(resp, "order", result.order),
    )
    return cmp.reduce(result.flatten())


@dataclass
@impl_event(ContextEventProtocol)
class UserChangeDraftPaymentMethodComposableEvent:
    provider: Payment_Provider_Enum
    user_id: UUID

    @property
    def payload(self) -> Self:
        return self


def user_change_draft_payment_method_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    _get_user_draft_order = GetUserDraftOrder(context, queries)
    _change_payment_method = ChangePaymentMethod(queries)

    root_event: UserChangeDraftPaymentMethodComposableEvent

    async def user_change_draft_payment_method_composable_event(
        e: UserChangeDraftPaymentMethodComposableEvent,
    ):
        nonlocal root_event
        root_event = e
        await context.publish(GetUserDraftOrderEvent(e.user_id))

    async def get_user_draft_order_retrieved_event(e: UserDraftOrderRetrievedEvent):
        nonlocal root_event
        await context.publish(
            ChangePaymentMethodEvent(order=e.order, provider=root_event.provider)
        )

    return (
        context
        | ContextExecutor(
            UserChangeDraftPaymentMethodComposableEvent,
            user_change_draft_payment_method_composable_event,
        )
        | ContextExecutor(GetUserDraftOrderEvent, _get_user_draft_order.execute)
        | ContextExecutor(
            UserDraftOrderRetrievedEvent, get_user_draft_order_retrieved_event
        )
        | ContextExecutor(ChangePaymentMethodEvent, _change_payment_method.execute)
    )


class UserChangeDraftPaymentMethod(BaseModel):
    provider: Payment_Provider_Enum


@api.put("/draft/payment-method", dependencies=[Depends(verify_access_token)])
async def user_change_draft_payment_method(
    body: UserChangeDraftPaymentMethod,
    token: Annotated[Token, Depends(verify_access_token)],
    context: Annotated[
        ContextBus, Depends(user_change_draft_payment_method_request__context_bus)
    ],
):
    user_id = token.user_id()
    if not user_id:
        raise HTTPException(status_code=401, detail="Not found user_id")

    await context.publish(
        UserChangeDraftPaymentMethodComposableEvent(
            user_id=user_id,
            provider=body.provider,
        )
    )

    result = await context.gather()
    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        ChangePaymentMethodResult,
        lambda resp, result: set_key(resp, "payment_detail", result.payment_detail),
    )
    return cmp.reduce(result.flatten())


@dataclass
@impl_event(ContextEventProtocol)
class ConvertCartToDraftOrder:
    user_id: UUID
    order: Order | None = None
    cart: Cart | None = None

    @property
    def payload(self) -> Self:
        return self


def user_convert_cart_to_draft_order_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    _get_user_cart = GetUserCart(context, queries)
    _get_user_draft_order = GetUserDraftOrder(context, queries)
    # TODO: provide different payment provider
    _cart_items_to_order_items = CartItemsToOrderItems(
        context, queries, StripeBilling()
    )

    root_event: ConvertCartToDraftOrder

    async def dispatch(e: ConvertCartToDraftOrder):
        nonlocal root_event
        root_event = e
        await context.publish(GetUserCartEvent(e.user_id))
        await context.publish(GetUserDraftOrderEvent(e.user_id))

    async def waiter(e: UserCartRetrievedEvent | UserDraftOrderRetrievedEvent):
        nonlocal root_event
        if isinstance(e, UserCartRetrievedEvent):
            root_event.cart = e.cart
        if isinstance(e, UserDraftOrderRetrievedEvent):
            root_event.order = e.order

        if root_event.order and root_event.cart:
            await context.publish(
                CartItemsToOrderItemsEvent(
                    cart=root_event.cart,
                    order=root_event.order,
                )
            )

    return (
        context
        | ContextExecutor(ConvertCartToDraftOrder, dispatch)
        | ContextExecutor(GetUserCartEvent, _get_user_cart.execute)
        | ContextExecutor(GetUserDraftOrderEvent, _get_user_draft_order.execute)
        | ContextExecutor(UserCartRetrievedEvent, waiter)
        | ContextExecutor(UserDraftOrderRetrievedEvent, waiter)
        | ContextExecutor(
            CartItemsToOrderItemsEvent, _cart_items_to_order_items.execute
        )
    )


@api.put("/draft/convert-cart-to-order", dependencies=[Depends(verify_access_token)])
async def user_convert_cart_to_draft_order(
    token: Annotated[Token, Depends(verify_access_token)],
    context: Annotated[
        ContextBus, Depends(user_convert_cart_to_draft_order_request__context_bus)
    ],
):
    user_id = token.user_id()
    if not user_id:
        raise HTTPException(status_code=401, detail="Not found user_id")

    await context.publish(ConvertCartToDraftOrder(user_id=user_id))
    await context.gather()
    return {"ok": True}


def orders_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    _get_orders = GetOrders(queries)
    return context | ContextExecutor(GetOrdersEvent, _get_orders.execute)


@api.get("/", dependencies=[Depends(verify_access_token)])
async def orders(
    token: Annotated[Token, Depends(verify_access_token)],
    context: Annotated[ContextBus, Depends(orders_request__context_bus)],
    page: int = 0,
    page_size: int = 20,
):
    user_id = token.user_id()
    if not user_id:
        raise HTTPException(status_code=401, detail="Not found user_id")

    await context.publish(
        GetOrdersEvent(
            page=page,
            page_size=page_size,
        )
    )

    result = await context.gather()
    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        GetOrdersResult,
        lambda resp, result: set_key(resp, "orders", result.orders_with_customers),
    )
    return cmp.reduce(result.flatten())


def user_orders_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    _get_user_orders = GetUserOrders(queries)
    return context | ContextExecutor(GetUserOrdersEvent, _get_user_orders.execute)


@api.get("/user", dependencies=[Depends(verify_access_token)])
async def user_orders(
    token: Annotated[Token, Depends(verify_access_token)],
    context: Annotated[ContextBus, Depends(user_orders_request__context_bus)],
    page: int = 0,
    page_size: int = 20,
):
    user_id = token.user_id()
    if not user_id:
        raise HTTPException(status_code=401, detail="Not found user_id")

    await context.publish(
        GetUserOrdersEvent(
            page=page,
            page_size=page_size,
            user_id=user_id,
        )
    )

    result = await context.gather()
    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        GetUserOrdersResult, lambda resp, result: set_key(resp, "orders", result.orders)
    )
    return cmp.reduce(result.flatten())


def register_handler(router: APIRouter):
    router.include_router(api, prefix="/orders")
