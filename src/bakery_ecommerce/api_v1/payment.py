from dataclasses import dataclass
from typing import Annotated, Any, Self, TypedDict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from nats.js.errors import NoStreamResponseError

from bakery_ecommerce import dependencies
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
    CartItemsToOrderItemsConvertedEvent,
    CartItemsToOrderItemsEvent,
    GetUserDraftOrderEvent,
    UserDraftOrderRetrievedEvent,
)
from bakery_ecommerce.internal.order.order_use_cases import (
    CartItemsToOrderItems,
    GetUserDraftOrder,
)
from bakery_ecommerce.internal.order.store.order_model import Order
from bakery_ecommerce.internal.order.stripe_events import (
    StripeCreateOrderPaymentIntentEvent,
)
from bakery_ecommerce.internal.order.stripe_use_cases import (
    StripeCreateOrderPaymentIntent,
    StripeCreateOrderPaymentIntentResult,
)
from bakery_ecommerce.internal.store.query import QueryProcessor
from bakery_ecommerce.token_middleware import verify_access_token

from pydantic import BaseModel

from nats.aio.client import Client as NATS


api = APIRouter()


class StripeObject(TypedDict):
    id: str


class StripeData(TypedDict):
    object: StripeObject


class StripeRequest(BaseModel):
    type: str
    api_version: str
    data: StripeData


@api.post("/stripe/webhook")
async def stripe_webhook_handler(
    request: Request,
    body: StripeRequest,
    nats: Annotated[NATS, Depends(dependencies.request_nats_session)],
):
    payload = await request.body()
    # stripe_signature = request.headers.get("stripe-signature")

    js = nats.jetstream()

    try:
        await js.publish(
            subject=f"{body.type}.{body.data['object']['id']}",
            stream="PAYMENTS_STRIPE",
            payload=payload,
        )
    except NoStreamResponseError:
        print(
            f"Receive not interested in stripe subject {body.type}.{body.data['object']['id']}"
        )


@dataclass
@impl_event(ContextEventProtocol)
class StripeCreatePaymentIntentEvent:
    user_id: UUID

    cart: Cart | None = None
    order: Order | None = None

    @property
    def payload(self) -> Self:
        return self


# TODO: Half of the code is the same as in `user_convert_cart_to_draft_order_request__context_bus`
def stripe_create_payment_intent_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    _get_user_cart = GetUserCart(context, queries)
    _get_user_draft_order = GetUserDraftOrder(context, queries)
    # TODO: provide different payment provider
    _cart_items_to_order_items = CartItemsToOrderItems(
        context, queries, StripeBilling()
    )
    _stripe_create_payment_intent = StripeCreateOrderPaymentIntent()

    root_event: StripeCreatePaymentIntentEvent

    async def dispatch(e: StripeCreatePaymentIntentEvent):
        nonlocal root_event
        root_event = e
        await context.publish(GetUserCartEvent(e.user_id))
        await context.publish(GetUserDraftOrderEvent(e.user_id))

    async def cart_items_to_order_items_event_waiter(
        e: UserCartRetrievedEvent | UserDraftOrderRetrievedEvent,
    ):
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

    async def waiter(e: CartItemsToOrderItemsConvertedEvent):
        nonlocal root_event
        if not e.order:
            raise ValueError("Not found order after cart to order converted")
        await context.publish(
            StripeCreateOrderPaymentIntentEvent(
                order=e.order, user_id=root_event.user_id
            )
        )

    return (
        context
        | ContextExecutor(StripeCreatePaymentIntentEvent, dispatch)
        | ContextExecutor(GetUserCartEvent, _get_user_cart.execute)
        | ContextExecutor(GetUserDraftOrderEvent, _get_user_draft_order.execute)
        | ContextExecutor(
            UserCartRetrievedEvent, cart_items_to_order_items_event_waiter
        )
        | ContextExecutor(
            UserDraftOrderRetrievedEvent, cart_items_to_order_items_event_waiter
        )
        | ContextExecutor(
            CartItemsToOrderItemsEvent, _cart_items_to_order_items.execute
        )
        | ContextExecutor(CartItemsToOrderItemsConvertedEvent, waiter)
        | ContextExecutor(
            StripeCreateOrderPaymentIntentEvent, _stripe_create_payment_intent.execute
        )
    )


@api.post("/stripe/payment-intent", dependencies=[Depends(verify_access_token)])
async def stripe_create_payment_intent(
    context: Annotated[
        ContextBus, Depends(stripe_create_payment_intent_request__context_bus)
    ],
    token: Annotated[Token, Depends(verify_access_token)],
):
    user_id = token.user_id()
    if not user_id:
        raise HTTPException(status_code=401, detail="Not found access_tokne user_id")

    await context.publish(StripeCreatePaymentIntentEvent(user_id))

    result = await context.gather()
    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        StripeCreateOrderPaymentIntentResult,
        lambda resp, result: set_key(resp, "client_secret", result.client_secret),
    )
    return cmp.reduce(result.flatten())


def register_handler(router: APIRouter):
    router.include_router(api, prefix="/payments")
