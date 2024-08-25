import asyncio
import contextlib
import os
from typing import Any, Callable, Coroutine, Generator, TypeVar

import fastapi
import nats
import stripe
from bakery_ecommerce.context_bus import ContextBus
from bakery_ecommerce.internal.catalog.store.catalog_queries import (
    NormalizeCatalogItemsPosition,
    NormalizeCatalogItemsPositionHandler,
)
from bakery_ecommerce.internal.identity.store.private_key_session_queries import (
    GetPrivateKeySignature,
    GetPrivateKeySignatureHandler,
)
from bakery_ecommerce.internal.store import crud_queries, product_queries
from bakery_ecommerce.internal.store.join_queries import (
    JoinOperation,
    JoinOperationHandler,
)
from bakery_ecommerce.internal.store.query import (
    QueryCache,
    QueryProcessor,
    QueryProcessorHandlers,
)
from bakery_ecommerce.internal.store.session import (
    DatabaseSessionManager,
    PostgresDatabaseConfig,
)
from bakery_ecommerce.object_store import MinioStore, ObjectStore
from bakery_ecommerce.worker.image import product_image_transcoding_handler
from bakery_ecommerce.worker.stripe import (
    charge_succeeded_worker_handler,
    payment_intent_created_handler,
)
from nats.aio.client import Client as NATS
from nats.aio.msg import Msg
from nats.js import JetStreamContext
from nats.js.api import (
    AckPolicy,
    ConsumerConfig,
    DeliverPolicy,
    DiscardPolicy,
    RetentionPolicy,
    StreamConfig,
)
from nats.js.errors import NotFoundError
from sqlalchemy.ext.asyncio import AsyncSession

REQUEST_ATTR_T = TypeVar("REQUEST_ATTR_T")


def cache_request_attr(
    request: fastapi.Request, attr: REQUEST_ATTR_T
) -> REQUEST_ATTR_T:
    attr_type = str(type(attr))
    if not hasattr(request.state, attr_type):
        request.state._state[attr_type] = attr
    return request.state._state[attr_type]


session_manager = DatabaseSessionManager(PostgresDatabaseConfig().get_uri())


async def transaction():
    async with session_manager.tx() as tx:
        print("run transaction")
        yield tx
    print("out of transaction")


def request_transaction(
    request: fastapi.Request, tx: AsyncSession = fastapi.Depends(transaction)
) -> AsyncSession:
    return cache_request_attr(request, tx)


async def session():
    async with session_manager.session() as session:
        yield session


def minio_object_store_factory() -> MinioStore:
    return MinioStore()


def request_object_store() -> Generator[ObjectStore, Any, None]:
    yield minio_object_store_factory()


nats_server = "nats://localhost:4222"


async def nats_session():
    async with await nats.connect(nats_server) as nc:
        yield nc


def request_nats_session(
    request: fastapi.Request, nc: NATS = fastapi.Depends(nats_session)
):
    return cache_request_attr(request, nc)


async def nats_worker_task(
    stream: str,
    consumer: ConsumerConfig,
    consumer_name: str,
    msg_cb_f: Callable[
        [Msg, QueryProcessor, *tuple[Any, ...]], Coroutine[Any, Any, None]
    ],
    *args,
):
    lock = asyncio.Lock()
    async with await nats.connect(nats_server) as nc:
        print(
            "{consumer_name} | connected {nats_server}".format(
                consumer_name=consumer_name,
                nats_server=nats_server,
            )
        )

        async def cb(msg: Msg):
            subject = msg.subject
            reply = msg.reply
            print(
                "'{subject} {reply}' | Received a message".format(
                    subject=subject,
                    reply=reply,
                )
            )
            try:
                async with lock:
                    await msg_cb_f(msg, query_processor_factory(nc), *args)

            except ValueError as e:
                await msg.ack()
                print(
                    "'{subject} {reply}' | Skip the message catch value error: {error}".format(
                        subject=subject, reply=reply, error=e
                    )
                )
            except Exception as e:
                print(
                    "'{subject} {reply}' | Error: {error}".format(
                        subject=subject, reply=reply, error=e
                    )
                )

            print(
                "'{subject} {reply}' | Done ".format(
                    subject=subject,
                    reply=reply,
                )
            )

        js = nc.jetstream()
        sub = await js.subscribe_bind(
            stream,
            consumer=consumer_name,
            config=consumer,
            cb=cb,
            manual_ack=True,
        )
        await asyncio.sleep(10)
        await sub.unsubscribe()
        async with lock:
            await nc.drain()


async def spawn_nats_worker(
    stream: str,
    consumer: ConsumerConfig,
    consumer_name: str,
    msg_cb_f: Callable[..., Coroutine],
    *args,
):
    loop = asyncio.get_running_loop()
    delay = 2.0
    while True:
        try:
            await loop.create_task(
                nats_worker_task(
                    stream,
                    consumer,
                    consumer_name,
                    msg_cb_f,
                    *args,
                )
            )
        except Exception as e:
            if "Event loop stopped before Future completed" in str(e):
                print("Stop worker loop")
                break
            print(f"catch error in loop routine. Delay {delay}. {e}")
        finally:
            await asyncio.sleep(delay)


any_payment_intent_subject = "payment_intent.created.>"
any_charge_subject = "charge.succeeded.>"

payments_stripe_stream_config = StreamConfig(
    name="PAYMENTS_STRIPE",
    retention=RetentionPolicy.WORK_QUEUE,
    discard=DiscardPolicy.OLD,
    subjects=[
        any_payment_intent_subject,
        any_charge_subject,
    ],
)


def product_image_transcoding_required_subject(wildcard: str) -> str:
    return f"image.transcoding.required.{wildcard}"


product_images_transcoding_stream_config = StreamConfig(
    name="PRODUCT_IMAGES_TRANSCODING",
    retention=RetentionPolicy.WORK_QUEUE,
    discard=DiscardPolicy.OLD,
    subjects=[
        product_image_transcoding_required_subject(">"),
    ],
)


def product_images_transcoding_consumer_config(consumer_name: str) -> ConsumerConfig:
    return ConsumerConfig(
        name=consumer_name,
        deliver_policy=DeliverPolicy.ALL,
        deliver_group="product_images_transcoding_group_0",
        deliver_subject="image.transcoding.required",
        filter_subjects=[product_image_transcoding_required_subject("*")],
        ack_policy=AckPolicy.EXPLICIT,
    )


def payments_stripe_payment_intent_created_consumer_config(
    consumer_name: str,
) -> ConsumerConfig:
    return ConsumerConfig(
        name=consumer_name,
        deliver_policy=DeliverPolicy.ALL,
        deliver_group="payments_stripe_group_0",
        deliver_subject="payment_intent.created",
        filter_subjects=["payment_intent.created.*"],
        ack_policy=AckPolicy.EXPLICIT,
    )


def payments_stripe_charge_succeeded_consumer_config(
    consumer_name: str,
) -> ConsumerConfig:
    return ConsumerConfig(
        name=consumer_name,
        deliver_policy=DeliverPolicy.ALL,
        deliver_group="payments_stripe_group_0",
        deliver_subject="charge.succeeded",
        filter_subjects=["charge.succeeded.*"],
        ack_policy=AckPolicy.EXPLICIT,
    )


async def get_or_create_stream(js: JetStreamContext, config: StreamConfig):
    if not config.name:
        raise ValueError("Stream config must have a name")

    try:
        stream = await js.stream_info(config.name)
        stream = await js.update_stream(config)
    except NotFoundError as e:
        print(f"not found stream {e}", type(e))
        stream = await js.add_stream(config)

    return stream


async def get_or_create_consumer(
    js: JetStreamContext, stream_config: StreamConfig, consumer_config: ConsumerConfig
):
    if not consumer_config.name or not stream_config.name:
        raise ValueError("Requere stream_config.name and consumer_config.name")

    try:
        consumer = await js.consumer_info(stream_config.name, consumer_config.name, 1)
    except Exception as e:
        print(f"not found consumer {e}", type(e))
        consumer = await js.add_consumer(stream_config.name, consumer_config, 1)

    return consumer


@contextlib.asynccontextmanager
async def lifespan(_: fastapi.FastAPI):
    async with await nats.connect(nats_server) as nc:
        js = nc.jetstream()
        await get_or_create_stream(js, payments_stripe_stream_config)
        await get_or_create_stream(js, product_images_transcoding_stream_config)
        await get_or_create_consumer(
            js,
            payments_stripe_stream_config,
            payments_stripe_payment_intent_created_consumer_config(
                "stripe_payment_intent_created_0"
            ),
        )
        await get_or_create_consumer(
            js,
            payments_stripe_stream_config,
            payments_stripe_charge_succeeded_consumer_config(
                "stripe_charge_succeeded_0"
            ),
        )
        await get_or_create_consumer(
            js,
            product_images_transcoding_stream_config,
            product_images_transcoding_consumer_config(
                "product_images_transcoding_0",
            ),
        )

    stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY")
    print("Use stripe secret key:", stripe_secret_key)
    stripe.api_key = stripe_secret_key

    name = "stripe_charge_succeeded_consumer_0"
    stream: str = payments_stripe_stream_config.name  # pyright: ignore
    asyncio.ensure_future(
        spawn_nats_worker(
            stream,
            payments_stripe_charge_succeeded_consumer_config(name),
            name,
            charge_succeeded_worker_handler,
            session_manager,
        )
    )

    name = "stripe_payment_intent_created_consumer_0"
    asyncio.ensure_future(
        spawn_nats_worker(
            stream,
            payments_stripe_payment_intent_created_consumer_config(name),
            name,
            payment_intent_created_handler,
            session_manager,
        )
    )

    name = "product_images_transcoding_consumer_0"
    stream: str = product_images_transcoding_stream_config.name  # pyright: ignore
    asyncio.ensure_future(
        spawn_nats_worker(
            stream,
            product_images_transcoding_consumer_config(name),
            name,
            product_image_transcoding_handler,
            session_manager,
            minio_object_store_factory(),
        )
    )

    yield

    if not session_manager.is_closed():
        await session_manager.close()


query_handlers = QueryProcessorHandlers(
    {
        crud_queries.CrudOperation: crud_queries.CrudOperationHandler,
        crud_queries.CustomBuilder: crud_queries.CustomBuilderHandler,
        product_queries.FindProductByName: product_queries.FindProductByNameHandler,
        GetPrivateKeySignature: GetPrivateKeySignatureHandler,
        JoinOperation: JoinOperationHandler,
        NormalizeCatalogItemsPosition: NormalizeCatalogItemsPositionHandler,
    }
)


def query_processor_factory(nats: NATS) -> QueryProcessor:
    return QueryProcessor(query_handlers, QueryCache(nats))


def query_processor(nats: NATS = fastapi.Depends(request_nats_session)):
    yield QueryProcessor(query_handlers, QueryCache(nats))


def request_query_processor(
    request: fastapi.Request,
    queries: QueryProcessor = fastapi.Depends(query_processor),
) -> QueryProcessor:
    return cache_request_attr(request, queries)


def request_context_bus(request: fastapi.Request) -> ContextBus:
    return cache_request_attr(request, ContextBus(session_manager.session_maker()))
