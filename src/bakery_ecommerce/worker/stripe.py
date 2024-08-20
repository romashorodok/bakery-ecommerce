from json import loads
from typing import Generic, TypeVar
from uuid import UUID
from nats.aio.msg import Msg
from pydantic import BaseModel


from bakery_ecommerce.internal.order.store.order_model import (
    Order,
    Order_Status_Enum,
    PaymentDetail,
)
from bakery_ecommerce.internal.store.crud_queries import CrudOperation
from bakery_ecommerce.internal.store.query import QueryProcessor
from bakery_ecommerce.internal.store.session import DatabaseSessionManager


class StripeMetadata(BaseModel):
    user_id: UUID
    order_id: UUID
    payment_detail_id: UUID


class BaseStripeObject(BaseModel):
    id: str
    metadata: StripeMetadata


class PaymentIntentStripeObject(BaseStripeObject):
    client_secret: str


StripeObject_T = TypeVar("StripeObject_T", bound=BaseStripeObject)


class StripeEventData(BaseModel, Generic[StripeObject_T]):
    object: StripeObject_T


class StripeEvent(BaseModel, Generic[StripeObject_T]):
    api_version: str
    data: StripeEventData[StripeObject_T]


async def payment_intent_created_handler(
    msg: Msg, queries: QueryProcessor, session_manager: DatabaseSessionManager
):
    data = loads(msg.data)
    stripe_event = StripeEvent[PaymentIntentStripeObject](**data)
    payment_intent = stripe_event.data.object.id
    client_secret = stripe_event.data.object.client_secret
    payment_detail_id = stripe_event.data.object.metadata.payment_detail_id

    async with session_manager.tx() as session:
        operation = CrudOperation(
            PaymentDetail,
            lambda q: q.update_partial(
                "id",
                payment_detail_id,
                {
                    "payment_intent": payment_intent,
                    "client_secret": client_secret,
                },
            ),
        )
        result = await queries.process(session, operation)
        if not result:
            raise ValueError(f"not found payment detail: {payment_detail_id}")

        await msg.ack()


async def charge_succeeded_worker_handler(
    msg: Msg, queries: QueryProcessor, session_manager: DatabaseSessionManager
):
    data = loads(msg.data)
    stripe_event = StripeEvent[BaseStripeObject](**data)
    order_id = stripe_event.data.object.metadata.order_id

    async with session_manager.tx() as session:
        operation = CrudOperation(
            Order,
            lambda q: q.update_partial(
                "id",
                order_id,
                {
                    "order_status": Order_Status_Enum.COMPLETED,
                },
            ),
        )
        result = await queries.process(session, operation)
        if not result:
            raise ValueError(f"not found order: {order_id}")

    await msg.ack()
