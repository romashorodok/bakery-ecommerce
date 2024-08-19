from asyncio import sleep, Lock
from json import loads
from typing import Generic, TypeVar
from uuid import UUID
import nats
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
from bakery_ecommerce import dependencies


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


# stripe.payment_intent.created.pi_*
async def payment_intent_created_worker(
    consumer_name: str,
    nats_server: str,
    session_manager: DatabaseSessionManager,
):
    lock = Lock()
    async with await nats.connect(nats_server) as nc:
        queries = dependencies.query_processor_factory(nc)

        async def handler(msg: Msg):
            async with lock:
                print(
                    "nats handler acquire",
                )
                subject = msg.subject
                reply = msg.reply
                print(
                    "{consumer_name} | Received a message on '{subject} {reply}'".format(
                        subject=subject,
                        reply=reply,
                        consumer_name=consumer_name,
                    )
                )

                data = loads(msg.data)
                try:
                    stripe_event = StripeEvent[PaymentIntentStripeObject](**data)
                    payment_intent = stripe_event.data.object.id
                    client_secret = stripe_event.data.object.client_secret
                    payment_detail_id = (
                        stripe_event.data.object.metadata.payment_detail_id
                    )
                except Exception as e:
                    print(
                        "{consumer_name} | Invalid event format of a message on '{subject} {reply}'. Err: {error}".format(
                            subject=subject,
                            reply=reply,
                            consumer_name=consumer_name,
                            error=e,
                        )
                    )
                    await msg.ack()
                    return

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
                        print(
                            "{consumer_name} | Not found order of a message on '{subject} {reply}'".format(
                                subject=subject,
                                reply=reply,
                                consumer_name=consumer_name,
                            )
                        )

                await msg.ack()

        print("start nats connection", nc, "nats_args", nats_server)
        js = nc.jetstream()

        config = dependencies.payments_stripe_payment_intent_created_consumer_config(
            consumer_name
        )

        sub = await js.subscribe_bind(
            stream="PAYMENTS",
            consumer=consumer_name,
            config=config,
            cb=handler,
            manual_ack=True,
        )

        await sleep(10)
        await sub.unsubscribe()

        async with lock:
            await nc.drain()


# stripe.charge.succeeded.ch_*
async def charge_succeeded_worker(
    consumer_name: str,
    nats_server: str,
    session_manager: DatabaseSessionManager,
):
    lock = Lock()
    async with await nats.connect(nats_server) as nc:
        queries = dependencies.query_processor_factory(nc)

        async def handler(msg: Msg):
            async with lock:
                print(
                    "nats handler acquire",
                )
                subject = msg.subject
                reply = msg.reply
                print(
                    "{consumer_name} | Received a message on '{subject} {reply}'".format(
                        subject=subject,
                        reply=reply,
                        consumer_name=consumer_name,
                    )
                )

                data = loads(msg.data)
                try:
                    stripe_event = StripeEvent[BaseStripeObject](**data)
                    order_id = stripe_event.data.object.metadata.order_id
                except Exception as e:
                    print(
                        "{consumer_name} | Invalid event format of a message on '{subject} {reply}'. Err: {error}".format(
                            subject=subject,
                            reply=reply,
                            consumer_name=consumer_name,
                            error=e,
                        )
                    )
                    await msg.ack()
                    return

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
                        print(
                            "{consumer_name} | Not found order of a message on '{subject} {reply}'".format(
                                subject=subject,
                                reply=reply,
                                consumer_name=consumer_name,
                            )
                        )

                await msg.ack()

        print("start nats connection", nc, "nats_args", nats_server)
        js = nc.jetstream()

        config = dependencies.payments_stripe_charge_succeeded_consumer_config(
            consumer_name
        )

        sub = await js.subscribe_bind(
            stream="PAYMENTS",
            consumer=consumer_name,
            config=config,
            cb=handler,
            manual_ack=True,
        )

        await sleep(10)
        await sub.unsubscribe()

        async with lock:
            await nc.drain()
